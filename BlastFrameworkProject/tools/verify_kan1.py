#!/usr/bin/env python3
"""
Quick verification: Can we access KAN-1?
Run this after creating KAN-1 in JIRA
"""

import base64
import requests
import json
from pathlib import Path

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

print("🔍 Verifying KAN-1 access...")
print(f"URL: {base_url}/rest/api/3/issue/KAN-1\n")

try:
    response = requests.get(
        f"{base_url}/rest/api/3/issue/KAN-1",
        headers=headers,
        timeout=10
    )

    if response.status_code == 200:
        issue = response.json()
        print("✅ SUCCESS! KAN-1 is accessible!\n")
        print(f"📋 Issue Details:")
        print(f"   Key: {issue['key']}")
        print(f"   Summary: {issue['fields']['summary']}")
        print(f"   Type: {issue['fields']['issuetype']['name']}")
        print(f"   Status: {issue['fields']['status']['name']}")
        print(f"\n✅ Ready to proceed with Phase 3: Architect!")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {str(e)}")
