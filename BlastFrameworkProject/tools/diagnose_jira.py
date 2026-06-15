#!/usr/bin/env python3
"""
Diagnose JIRA access - List available projects and issues
"""

import json
import sys
import base64
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed")
    sys.exit(1)

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
base_url = base_url.rstrip('/')

auth = base64.b64encode(f"{jira_email}:{jira_token}".encode()).decode()
headers = {
    "Authorization": f"Basic {auth}",
    "Accept": "application/json"
}

print(f"[JIRA Diagnostics] {datetime.now().isoformat()}")
print(f"Base URL: {base_url}\n")

# Step 1: List Projects
print("=" * 60)
print("STEP 1: Fetching all projects...")
print("=" * 60)

try:
    response = requests.get(f"{base_url}/rest/api/3/project", headers=headers, timeout=10)
    if response.status_code == 200:
        projects = response.json()
        print(f"✅ Found {len(projects)} projects:\n")
        for proj in projects:
            print(f"  Project: {proj['key']} - {proj['name']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text[:300]}")
except Exception as e:
    print(f"❌ Error: {str(e)}")

# Step 2: List Issues in KAN project
print("\n" + "=" * 60)
print("STEP 2: Fetching issues from KAN project...")
print("=" * 60)

try:
    jql = "project = KAN"
    response = requests.get(
        f"{base_url}/rest/api/3/search",
        headers=headers,
        params={"jql": jql, "maxResults": 10},
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        issues = data.get("issues", [])
        print(f"✅ Found {data.get('total', 0)} issues in KAN project\n")

        if issues:
            print(f"First {len(issues)} issues:")
            for issue in issues:
                print(f"  - {issue['key']}: {issue['fields']['summary']}")
        else:
            print("No issues found in KAN project")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text[:300]}")
except Exception as e:
    print(f"❌ Error: {str(e)}")

# Step 3: Try to fetch KAN-1 directly with verbose error
print("\n" + "=" * 60)
print("STEP 3: Direct fetch of KAN-1...")
print("=" * 60)

try:
    response = requests.get(
        f"{base_url}/rest/api/3/issue/KAN-1",
        headers=headers,
        timeout=10
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        issue = response.json()
        print(f"✅ KAN-1 found!")
        print(f"  Summary: {issue['fields']['summary']}")
        print(f"  Status: {issue['fields']['status']['name']}")
    else:
        print(f"❌ Failed to fetch KAN-1")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "=" * 60)
print("Diagnostics complete. See .tmp/jira_diagnostics.log")
print("=" * 60)
