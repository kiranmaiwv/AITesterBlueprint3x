#!/usr/bin/env python3
"""
GROQ Strategy Generator - Generate test strategies from JIRA issues
Layer 3: Deterministic tool for calling GROQ API
"""

import requests
import json
from datetime import datetime
from pathlib import Path

class GroqStrategyGenerator:
    def __init__(self, api_key):
        """Initialize GROQ generator with API key"""
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "openai/gpt-oss-120b"
        self.timeout = 30  # 30-second SLA

    def generate_strategy(self, jira_issue):
        """
        Generate test strategy from JIRA issue data

        Args:
            jira_issue: dict with keys (key, summary, description, issue_type, status, priority)

        Returns:
            dict with strategy_content and metadata
        """

        # Build prompt
        system_prompt = """You are an expert QA test strategy architect. Your task is to generate comprehensive, professional test strategy documents that follow industry best practices.

Guidelines:
- Be specific and actionable
- Include realistic estimates and team sizes
- Reference industry standards (OWASP, ISO/IEC standards, etc.)
- Provide practical testing approaches based on issue type
- Keep a formal, professional tone"""

        user_prompt = f"""Generate a comprehensive Test Strategy document for this software feature/issue:

**Issue Key:** {jira_issue.get('key', 'N/A')}
**Summary:** {jira_issue.get('summary', 'N/A')}
**Description:** {jira_issue.get('description', 'N/A')}
**Type:** {jira_issue.get('issue_type', 'N/A')}
**Status:** {jira_issue.get('status', 'N/A')}
**Priority:** {jira_issue.get('priority', 'N/A')}

Please generate a COMPLETE Test Strategy document with exactly these sections (use # markdown headers):

1. # Objective - Describe what is being tested and why. Be specific to this feature.

2. # Scope - Detail what is IN SCOPE and OUT OF SCOPE for testing.

3. # Focus Areas - List specific areas of focus (e.g., Functional correctness, Security, Performance, Usability, Compatibility). Provide 3-5 focus areas relevant to this feature.

4. # Approach - Describe:
   - Black box and white box testing techniques
   - Automation tools and frameworks
   - Manual testing approach
   - Testing types (unit, integration, end-to-end, etc.)

5. # Deliverables - List the tangible outputs (test cases, reports, documentation, etc.)

6. # Team & Schedule - Estimate:
   - Team size needed
   - Effort (person-hours or duration)
   - Timeline with phases

7. # Entry & Exit Criteria - Define when testing starts and when it's complete

8. # Risks - Identify potential risks, blockers, and mitigation strategies

Generate approximately 1500 words. Use professional language. Make it actionable and realistic."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }

        start_time = datetime.now()

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            generation_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            result = {
                "timestamp": datetime.now().isoformat(),
                "source_issue": jira_issue.get('key', 'unknown'),
                "model_used": self.model,
                "generation_time_ms": generation_time_ms,
                "status_code": response.status_code,
                "success": response.status_code == 200
            }

            if response.status_code == 200:
                data = response.json()
                strategy_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                result["strategy_content"] = strategy_content
                result["tokens_used"] = data.get("usage", {}).get("completion_tokens", 0)
            else:
                result["error"] = response.json().get("error", {}).get("message", response.text)

            return result

        except requests.exceptions.Timeout:
            return {
                "timestamp": datetime.now().isoformat(),
                "source_issue": jira_issue.get('key', 'unknown'),
                "success": False,
                "error": f"Generation timeout (exceeded {self.timeout}s SLA)",
                "generation_time_ms": int((datetime.now() - start_time).total_seconds() * 1000)
            }
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "source_issue": jira_issue.get('key', 'unknown'),
                "success": False,
                "error": str(e),
                "generation_time_ms": int((datetime.now() - start_time).total_seconds() * 1000)
            }


# CLI Usage
if __name__ == "__main__":
    import sys

    # Load .env
    env_path = Path(__file__).parent.parent / ".env"

    groq_key = None

    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('GROQ_KEY'):
                groq_key = line.split('=', 1)[1].strip().strip('"')
                break

    generator = GroqStrategyGenerator(groq_key)

    # Test with sample JIRA issue
    sample_issue = {
        "key": "KAN-1",
        "summary": "User Authentication & SSO Integration",
        "description": "As a user, I want a secure and streamlined login interface...",
        "issue_type": "Story",
        "status": "To Do",
        "priority": "High"
    }

    result = generator.generate_strategy(sample_issue)

    print(json.dumps(result, indent=2))
