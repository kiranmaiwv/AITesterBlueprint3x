# Jira MCP Server for QA Buddy AI
# Run: python scripts/jira_mcp_server.py
# This implements the Model Context Protocol for Jira integration.

import json, sys, os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

class JiraMCPServer:
    """MCP-compatible Jira server.
    
    Exposes Jira operations as tools that can be called by the LLM.
    Protocol: JSON-RPC over stdin/stdout.
    """
    
    def __init__(self, base_url, email, api_token):
        from qa_buddy.connectors.jira_connector import JiraConnector
        self.jira = JiraConnector(base_url, email, api_token)
    
    def handle_request(self, request: dict) -> dict:
        """Handle a JSON-RPC request."""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "initialize":
            return self._initialize()
        elif method == "list_tools":
            return self._list_tools()
        elif method == "call_tool":
            return self._call_tool(params.get("name"), params.get("arguments", {}))
        elif method == "shutdown":
            return {"jsonrpc": "2.0", "result": None, "id": request.get("id")}
        else:
            return {"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method not found: {method}"}, "id": request.get("id")}
    
    def _initialize(self):
        return {
            "jsonrpc": "2.0",
            "result": {
                "protocolVersion": "0.1.0",
                "capabilities": {"tools": {}}
            },
            "id": 1
        }
    
    def _list_tools(self):
        return {
            "jsonrpc": "2.0",
            "result": {
                "tools": [
                    {
                        "name": "search_jira_issues",
                        "description": "Search Jira issues using JQL. Returns issue keys, summaries, and descriptions.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "jql": {"type": "string", "description": "JQL query string"},
                                "max_results": {"type": "integer", "description": "Max results to return", "default": 20}
                            },
                            "required": ["jql"]
                        }
                    },
                    {
                        "name": "get_jira_issue",
                        "description": "Fetch full details of a single Jira issue by key.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "issue_key": {"type": "string", "description": "Jira issue key (e.g. KAN-1)"}
                            },
                            "required": ["issue_key"]
                        }
                    }
                ]
            },
            "id": 1
        }
    
    def _call_tool(self, name: str, args: dict) -> dict:
        try:
            if name == "search_jira_issues":
                result = self.jira.search_issues(args["jql"], max_results=args.get("max_results", 20))
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                    },
                    "id": 1
                }
            elif name == "get_jira_issue":
                from qa_buddy.connectors.jira_connector import JiraConnector
                result = self.jira.fetch_issue(args["issue_key"])
                return {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                    },
                    "id": 1
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32602, "message": f"Unknown tool: {name}"},
                    "id": 1
                }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(e)},
                "id": 1
            }
    
    def run_stdio(self):
        """Run the MCP server over stdin/stdout."""
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                request = json.loads(line)
                response = self.handle_request(request)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except json.JSONDecodeError as e:
                sys.stdout.write(json.dumps({
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": f"Parse error: {e}"},
                    "id": None
                }) + "\n")
                sys.stdout.flush()
            except EOFError:
                break

    def run_http(self, host="0.0.0.0", port=8765):
        """Run the MCP server over HTTP."""
        from flask import Flask, request, jsonify
        app = Flask(__name__)
        
        @app.route("/mcp", methods=["POST"])
        def mcp():
            req = request.get_json()
            resp = self.handle_request(req)
            return jsonify(resp)
        
        @app.route("/health", methods=["GET"])
        def health():
            return jsonify({"status": "ok", "service": "jira-mcp"})
        
        print(f"Jira MCP server running on http://{host}:{port}")
        app.run(host=host, port=port)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    base_url = os.environ.get("JIRA_URL", "").split("/jira/")[0] if "/jira/" in os.environ.get("JIRA_URL", "") else os.environ.get("JIRA_URL", "")
    base_url = base_url.split("/browse/")[0] if "/browse/" in base_url else base_url
    email = os.environ.get("JIRA_EMAIL", "")
    token = os.environ.get("JIRA_API_TOKEN", "")
    
    if not all([base_url, email, token]):
        print(json.dumps({"error": "JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN must be set in .env"}, indent=2))
        sys.exit(1)
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "http"
    server = JiraMCPServer(base_url, email, token)
    
    if mode == "stdio":
        server.run_stdio()
    else:
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765
        server.run_http(port=port)
