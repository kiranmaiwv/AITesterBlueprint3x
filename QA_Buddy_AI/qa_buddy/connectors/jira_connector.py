"""JIRA Connector — fetch issues via JQL. Reused from BlastFramework."""

import base64
import requests


def extract_adf_text(adf_content):
    if adf_content is None:
        return ""
    if isinstance(adf_content, str):
        return adf_content
    texts = []
    def _walk(node):
        if isinstance(node, dict):
            t = node.get("type")
            if t == "text":
                texts.append(node.get("text", ""))
            elif t in ("paragraph", "heading", "listItem", "blockquote"):
                texts.append("\n")
                for c in node.get("content", []):
                    _walk(c)
                texts.append("\n")
            elif t in ("orderedList", "bulletList", "doc"):
                for c in node.get("content", []):
                    _walk(c)
            if node.get("type") == "hardBreak":
                texts.append("\n")
    _walk(adf_content)
    return "".join(texts).strip()


class JiraConnector:
    def __init__(self, base_url, email, api_token):
        self.base_url = base_url.rstrip("/")
        auth = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {auth}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def search_issues(self, jql, max_results=50):
        endpoint = f"{self.base_url}/rest/api/3/search/jql"
        all_issues = []
        start_at = 0
        try:
            while True:
                resp = requests.post(
                    endpoint, headers=self.headers,
                    json={"jql": jql, "maxResults": max_results, "startAt": start_at},
                    timeout=10,
                )
                if resp.status_code != 200:
                    return {"success": False, "error": resp.text}
                data = resp.json()
                for issue in data.get("issues", []):
                    fields = issue.get("fields", {})
                    desc = extract_adf_text(fields.get("description")) if isinstance(fields.get("description"), dict) else (fields.get("description") or "")
                    all_issues.append({
                        "key": issue.get("key", ""),
                        "summary": fields.get("summary", ""),
                        "description": desc,
                        "issue_type": fields.get("issuetype", {}).get("name", ""),
                        "status": fields.get("status", {}).get("name", ""),
                        "priority": fields.get("priority", {}).get("name", ""),
                    })
                total = data.get("total", 0)
                start_at += len(data.get("issues", []))
                if start_at >= total:
                    break
            return {"success": True, "total": len(all_issues), "issues": all_issues}
        except Exception as e:
            return {"success": False, "error": str(e)}
