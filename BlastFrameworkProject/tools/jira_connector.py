#!/usr/bin/env python3
"""
JIRA Connector - Fetch JIRA issues
Layer 3: Deterministic tool for fetching JIRA issue data
"""

import base64
import requests
import json
from datetime import datetime
from pathlib import Path


def extract_adf_text(adf_content):
    """Extract plain text from JIRA Atlassian Document Format (ADF)"""
    if adf_content is None:
        return ""
    if isinstance(adf_content, str):
        return adf_content

    texts = []

    def _walk(node):
        if isinstance(node, dict):
            content_type = node.get("type")
            if content_type == "text":
                texts.append(node.get("text", ""))
            elif content_type in ("paragraph", "heading", "listItem", "blockquote"):
                if content_type in ("heading", "listItem", "blockquote"):
                    texts.append("\n")
                for child in node.get("content", []):
                    _walk(child)
                if content_type in ("heading", "listItem", "blockquote"):
                    texts.append("\n")
            elif content_type in ("orderedList", "bulletList", "doc"):
                for child in node.get("content", []):
                    _walk(child)
            else:
                for child in node.get("content", []):
                    _walk(child)
            if node.get("type") == "hardBreak":
                texts.append("\n")

    _walk(adf_content)
    return "".join(texts).strip()


class JiraConnector:
    def __init__(self, base_url, email, api_token):
        """Initialize JIRA connector with credentials"""
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.api_token = api_token
        self.timeout = 10

        # Build auth header
        auth_string = f"{email}:{api_token}"
        encoded = base64.b64encode(auth_string.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def fetch_issue(self, issue_key):
        """
        Fetch a single JIRA issue
        Returns: dict with issue data or error details
        """
        endpoint = f"{self.base_url}/rest/api/3/issue/{issue_key}"

        try:
            response = requests.get(endpoint, headers=self.headers, timeout=self.timeout)

            result = {
                "timestamp": datetime.now().isoformat(),
                "issue_key": issue_key,
                "status_code": response.status_code,
                "success": response.status_code == 200
            }

            if response.status_code == 200:
                data = response.json()
                fields = data.get("fields", {})
                raw_desc = fields.get("description")
                description = extract_adf_text(raw_desc) if isinstance(raw_desc, dict) else (raw_desc or "")

                result["jira_issue"] = {
                    "key": data.get("key", ""),
                    "summary": fields.get("summary", ""),
                    "description": description,
                    "issue_type": fields.get("issuetype", {}).get("name", ""),
                    "status": fields.get("status", {}).get("name", ""),
                    "priority": fields.get("priority", {}).get("name", ""),
                    "assignee": fields.get("assignee"),
                    "project_key": fields.get("project", {}).get("key", "")
                }
            else:
                result["error"] = response.json().get("errorMessages", [response.text])[0]

            return result

        except requests.exceptions.Timeout:
            return {
                "timestamp": datetime.now().isoformat(),
                "issue_key": issue_key,
                "success": False,
                "error": f"Request timeout ({self.timeout}s exceeded)"
            }
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "issue_key": issue_key,
                "success": False,
                "error": str(e)
            }

    def search_issues(self, jql_query, max_results=10):
        """
        Search JIRA using JQL
        Returns: dict with list of issues or error
        """
        endpoint = f"{self.base_url}/rest/api/3/search/jql"

        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json={"jql": jql_query, "maxResults": max_results},
                timeout=self.timeout
            )

            result = {
                "timestamp": datetime.now().isoformat(),
                "status_code": response.status_code,
                "success": response.status_code == 200
            }

            if response.status_code == 200:
                data = response.json()
                result["total"] = data.get("total", 0)
                result["issues"] = [
                    {
                        "key": issue.get("key", ""),
                        "summary": issue.get("fields", {}).get("summary", ""),
                        "type": issue.get("fields", {}).get("issuetype", {}).get("name", "")
                    }
                    for issue in data.get("issues", [])
                ]
            else:
                result["error"] = response.json().get("errorMessages", [response.text])[0]

            return result

        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }


# CLI Usage
if __name__ == "__main__":
    import sys

    # Load .env
    env_path = Path(__file__).parent.parent / ".env"

    jira_email = None
    jira_token = None
    jira_url = None

    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('JIRA_EMAIL'):
                jira_email = line.split('=', 1)[1].strip().strip('"')
            elif line.startswith('JIRA_API_TOKEN'):
                jira_token = line.split('=', 1)[1].strip().strip('"')
            elif line.startswith('JIRA_URL'):
                jira_url = line.split('=', 1)[1].strip().strip('"')

    base_url = jira_url.split('/jira/')[0] if '/jira/' in jira_url else jira_url

    connector = JiraConnector(base_url, jira_email, jira_token)

    issue_key = sys.argv[1] if len(sys.argv) > 1 else "KAN-1"
    result = connector.fetch_issue(issue_key)

    print(json.dumps(result, indent=2))
