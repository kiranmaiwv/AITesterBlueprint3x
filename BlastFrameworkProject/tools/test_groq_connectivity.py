#!/usr/bin/env python3
"""
Test GROQ API connectivity
Minimal script to verify GROQ API is accessible and responding
"""

import os
import json
import sys
from datetime import datetime

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed. Install with: pip install requests")
    sys.exit(1)

# Load .env
from pathlib import Path
env_path = Path(__file__).parent.parent / ".env"

groq_key = None
with open(env_path, 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith('GROQ_KEY'):
            groq_key = line.split('=', 1)[1].strip().strip('"')
            break

if not groq_key:
    print("ERROR: GROQ_KEY not found in .env")
    sys.exit(1)

print(f"[{datetime.now().isoformat()}] Testing GROQ API connectivity...")
print(f"API Key (masked): {groq_key[:10]}...{groq_key[-5:]}")

# Test GROQ API
url = "https://api.groq.com/openai/v1/models"
headers = {
    "Authorization": f"Bearer {groq_key}",
    "Accept": "application/json"
}

try:
    response = requests.get(url, headers=headers, timeout=10)

    result = {
        "timestamp": datetime.now().isoformat(),
        "status": "PASS" if response.status_code == 200 else "FAIL",
        "status_code": response.status_code,
        "url": url,
        "response_time_ms": int(response.elapsed.total_seconds() * 1000)
    }

    if response.status_code == 200:
        data = response.json()
        result["models_available"] = len(data.get("data", []))
        print(f"✅ PASS: GROQ API responsive. {result['models_available']} models available.")
    else:
        result["error"] = response.text[:200]
        print(f"❌ FAIL: GROQ API returned {response.status_code}")
        print(f"Response: {response.text[:200]}")

    # Save result
    with open('/Users/kiranmaiwunnava/AITesterBlueprint3x-main/BlastFrameworkProject/.tmp/groq_test_result.json', 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Test result saved to .tmp/groq_test_result.json")

except Exception as e:
    result = {
        "timestamp": datetime.now().isoformat(),
        "status": "ERROR",
        "error": str(e)
    }
    print(f"❌ ERROR: {str(e)}")
    with open('/Users/kiranmaiwunnava/AITesterBlueprint3x-main/BlastFrameworkProject/.tmp/groq_test_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    sys.exit(1)
