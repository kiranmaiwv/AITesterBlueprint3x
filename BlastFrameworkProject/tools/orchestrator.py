#!/usr/bin/env python3
"""
Orchestrator - Main flow controller
Layer 2: Decision-making & flow coordination
Ties together JIRA fetch -> GROQ generation -> validation -> file save
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Import tools
sys.path.insert(0, str(Path(__file__).parent))
from jira_connector import JiraConnector
from groq_strategy_generator import GroqStrategyGenerator
from validator import StrategyValidator
from file_manager import FileManager


class StrategyOrchestrator:
    """Orchestrate the complete strategy generation flow"""

    def __init__(self, jira_url, jira_email, jira_token, groq_key, save_dir=None):
        """Initialize orchestrator with credentials"""
        self.jira_connector = JiraConnector(jira_url, jira_email, jira_token)
        self.groq_generator = GroqStrategyGenerator(groq_key)
        self.validator = StrategyValidator()
        self.file_manager = FileManager(save_dir)

    def generate_full_strategy(self, issue_key, save_files=True):
        """
        Generate complete test strategy for a JIRA issue

        Flow:
        1. Fetch JIRA issue
        2. Generate strategy via GROQ
        3. Validate output
        4. Save to files

        Returns:
            dict with complete results and metadata
        """

        start_time = datetime.now()
        result = {
            "timestamp": start_time.isoformat(),
            "issue_key": issue_key,
            "status": "IN_PROGRESS",
            "steps": {}
        }

        # STEP 1: Fetch JIRA Issue
        print(f"[1/4] Fetching JIRA issue: {issue_key}")
        jira_result = self.jira_connector.fetch_issue(issue_key)
        result["steps"]["jira_fetch"] = jira_result

        if not jira_result.get("success"):
            result["status"] = "FAILED"
            result["error"] = jira_result.get("error", "Unknown error")
            return result

        jira_issue = jira_result.get("jira_issue", {})
        print(f"✓ Found issue: {jira_issue.get('summary', 'N/A')}")

        # STEP 2: Generate Strategy via GROQ
        print(f"[2/4] Generating test strategy with GROQ...")
        groq_result = self.groq_generator.generate_strategy(jira_issue)
        result["steps"]["groq_generation"] = groq_result

        if not groq_result.get("success"):
            result["status"] = "FAILED"
            result["error"] = groq_result.get("error", "GROQ generation failed")
            return result

        print(f"✓ Generated in {groq_result.get('generation_time_ms', 0)}ms")

        # STEP 3: Validate Output
        print(f"[3/4] Validating strategy...")
        validation_result = self.validator.validate(groq_result)
        result["steps"]["validation"] = validation_result

        if not validation_result.get("valid"):
            result["status"] = "VALIDATION_FAILED"
            result["errors"] = validation_result.get("errors", [])
            result["warnings"] = validation_result.get("warnings", [])
            print(f"✗ Validation failed: {', '.join(validation_result.get('errors', []))}")
            return result

        print(f"✓ Valid strategy ({validation_result['statistics']['word_count']} words)")

        # STEP 4: Save to Files
        if save_files:
            print(f"[4/4] Saving strategy to files...")

            # Save markdown
            md_result = self.file_manager.save_strategy(groq_result, issue_key)
            result["steps"]["save_markdown"] = md_result

            if md_result.get("success"):
                print(f"✓ Saved to: {md_result.get('filename')}")
            else:
                print(f"✗ Failed to save: {md_result.get('error')}")

            # Save JSON
            json_result = self.file_manager.save_strategy(groq_result, issue_key)
            result["steps"]["save_json"] = json_result

        result["status"] = "SUCCESS"
        result["generation_time_ms"] = int((datetime.now() - start_time).total_seconds() * 1000)

        return result


# CLI Usage
if __name__ == "__main__":
    # Load .env
    env_path = Path(__file__).parent.parent / ".env"

    jira_email = None
    jira_token = None
    jira_url = None
    groq_key = None

    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('JIRA_EMAIL'):
                jira_email = line.split('=', 1)[1].strip().strip('"')
            elif line.startswith('JIRA_API_TOKEN'):
                jira_token = line.split('=', 1)[1].strip().strip('"')
            elif line.startswith('JIRA_URL'):
                jira_url = line.split('=', 1)[1].strip().strip('"')
            elif line.startswith('GROQ_KEY'):
                groq_key = line.split('=', 1)[1].strip().strip('"')

    base_url = jira_url.split('/jira/')[0] if '/jira/' in jira_url else jira_url

    # Create orchestrator
    orchestrator = StrategyOrchestrator(base_url, jira_email, jira_token, groq_key)

    # Generate strategy
    issue_key = sys.argv[1] if len(sys.argv) > 1 else "KAN-1"
    result = orchestrator.generate_full_strategy(issue_key)

    print(f"\n{'='*60}")
    print(json.dumps(result, indent=2))
    print(f"{'='*60}")
