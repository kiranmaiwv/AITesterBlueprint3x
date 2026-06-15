#!/usr/bin/env python3
"""
Try Jira API v3 JQL search endpoint
"""

import json
import sys
import base64
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit(1)

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
base_url = base_url.rstrip('/')

auth = base64.b64encode(f"{jira_email}:{jira_token}".encode()).decode()
headers = {
    "Authorization": f"Basic {auth}",
    "Accept": "application/json"
}

print("Trying v3 JQL Search Endpoint...")

# Try the new JQL endpoint
try:
    response = requests.post(
        f"{base_url}/rest/api/3/issues/search",
        headers=headers,
        json={"jql": "key = KAN-1"},
        timeout=10
    )

    print(f"Status: {response.status_code}")
    data = response.json()

    if response.status_code == 200:
        issues = data.get("issues", [])
        if issues:
            issue = issues[0]
            print(f"✅ FOUND KAN-1!")
            print(json.dumps(issue, indent=2))
        else:
            print(f"❌ No issues found. Total: {data.get('total', 0)}")
            print(f"Response: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)[:500]}")

except Exception as e:
    print(f"❌ Error: {str(e)}")
