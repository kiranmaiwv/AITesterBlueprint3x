#!/usr/bin/env python3
"""
Test JIRA API connectivity
Minimal script to verify JIRA API is accessible and can fetch KAN-1 issue
"""

import os
import json
import sys
import base64
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed. Install with: pip install requests")
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

if not all([jira_email, jira_token, jira_url]):
    print("ERROR: Missing JIRA credentials in .env")
    print(f"  Email: {bool(jira_email)}, Token: {bool(jira_token)}, URL: {bool(jira_url)}")
    sys.exit(1)

# Extract base URL (remove /jira/software/projects/... if present)
base_url = jira_url.split('/jira/')[0] if '/jira/' in jira_url else jira_url
base_url = base_url.rstrip('/')

print(f"[{datetime.now().isoformat()}] Testing JIRA API connectivity...")
print(f"Base URL: {base_url}")
print(f"Email: {jira_email}")

# Test 1: Fetch KAN-1 issue
api_url = f"{base_url}/rest/api/3/issue/KAN-1"
auth = base64.b64encode(f"{jira_email}:{jira_token}".encode()).decode()
headers = {
    "Authorization": f"Basic {auth}",
    "Accept": "application/json"
}

try:
    print(f"\nFetching issue: {api_url}")
    response = requests.get(api_url, headers=headers, timeout=10)

    result = {
        "timestamp": datetime.now().isoformat(),
        "status": "PASS" if response.status_code == 200 else "FAIL",
        "status_code": response.status_code,
        "url": api_url,
        "response_time_ms": int(response.elapsed.total_seconds() * 1000)
    }

    if response.status_code == 200:
        data = response.json()
        result["issue"] = {
            "key": data.get("key", ""),
            "summary": data.get("fields", {}).get("summary", ""),
            "description": data.get("fields", {}).get("description", "")[:100] + "..." if data.get("fields", {}).get("description") else "",
            "status": data.get("fields", {}).get("status", {}).get("name", ""),
            "issue_type": data.get("fields", {}).get("issuetype", {}).get("name", "")
        }
        print(f"✅ PASS: JIRA API responsive. Issue KAN-1 fetched successfully.")
        print(f"  Summary: {result['issue']['summary']}")
        print(f"  Status: {result['issue']['status']}")
        print(f"  Type: {result['issue']['issue_type']}")
    else:
        result["error"] = response.text[:200]
        print(f"❌ FAIL: JIRA API returned {response.status_code}")
        print(f"Response: {response.text[:200]}")

    # Save result
    with open('/Users/kiranmaiwunnava/AITesterBlueprint3x-main/BlastFrameworkProject/.tmp/jira_test_result.json', 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\nTest result saved to .tmp/jira_test_result.json")

except Exception as e:
    result = {
        "timestamp": datetime.now().isoformat(),
        "status": "ERROR",
        "error": str(e)
    }
    print(f"❌ ERROR: {str(e)}")
    with open('/Users/kiranmaiwunnava/AITesterBlueprint3x-main/BlastFrameworkProject/.tmp/jira_test_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    sys.exit(1)
