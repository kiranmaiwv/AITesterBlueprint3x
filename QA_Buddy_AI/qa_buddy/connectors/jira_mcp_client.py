"""MCP Client for Jira — wraps the Jira MCP server protocol."""

import json
import requests
from qa_buddy.config import config
from qa_buddy.connectors.jira_connector import JiraConnector


class JiraMCPClient:
    """Client that talks to Jira via MCP protocol.
    
    Falls back to direct REST API if MCP server is unreachable.
    """
    
    MCP_SERVER_URL = "http://localhost:8765/mcp"
    
    def __init__(self):
        self._mcp_available = None
        self._direct = None
    
    def _check_mcp(self):
        if self._mcp_available is not None:
            return self._mcp_available
        try:
            r = requests.get("http://localhost:8765/health", timeout=2)
            self._mcp_available = r.status_code == 200
        except:
            self._mcp_available = False
        return self._mcp_available
    
    def _get_direct(self):
        if self._direct is None:
            base = config.JIRA_URL.split("/jira/")[0] if "/jira/" in config.JIRA_URL else config.JIRA_URL
            base = base.split("/browse/")[0] if "/browse/" in base else base
            self._direct = JiraConnector(base, config.JIRA_EMAIL, config.JIRA_API_TOKEN)
        return self._direct
    
    def _mcp_call(self, tool_name: str, args: dict) -> dict:
        """Call a tool via MCP protocol."""
        payload = {
            "jsonrpc": "2.0",
            "method": "call_tool",
            "params": {"name": tool_name, "arguments": args},
            "id": 1
        }
        r = requests.post(self.MCP_SERVER_URL, json=payload, timeout=10)
        resp = r.json()
        if "result" in resp:
            content = resp["result"]["content"]
            text = "".join(c["text"] for c in content if c["type"] == "text")
            return json.loads(text)
        raise Exception(resp.get("error", {}).get("message", "MCP call failed"))
    
    def search_issues(self, jql: str, max_results: int = 20) -> dict:
        """Search Jira issues via MCP or direct REST."""
        if self._check_mcp():
            return self._mcp_call("search_jira_issues", {"jql": jql, "max_results": max_results})
        return self._get_direct().search_issues(jql, max_results)
    
    def fetch_issue(self, issue_key: str) -> dict:
        """Fetch a single Jira issue via MCP or direct REST."""
        if self._check_mcp():
            return self._mcp_call("get_jira_issue", {"issue_key": issue_key})
        return self._get_direct().fetch_issue(issue_key)
