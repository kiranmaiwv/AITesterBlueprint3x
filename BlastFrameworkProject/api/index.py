#!/usr/bin/env python3
"""
Vercel Serverless Function - Wraps Flask app for Vercel deployment
"""

import sys
import os
from pathlib import Path

# Add project root and tools to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tools"))

from flask import Flask, request, jsonify
from flask_cors import CORS
import json

from jira_connector import JiraConnector
from groq_strategy_generator import GroqStrategyGenerator
from validator import StrategyValidator
from file_manager import FileManager

app = Flask(__name__)
CORS(app)

# ============================================================
# Helper
# ============================================================
def get_env(key):
    """Read env var: Vercel env vars first, then .env file fallback"""
    val = os.environ.get(key)
    if val:
        return val
    # fallback to .env (for local testing)
    env_path = project_root / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                if k.strip() == key:
                    return v.strip().strip('"').strip("'")
    return ""


# ============================================================
# Routes
# ============================================================

@app.route('/api/env-config', methods=['GET'])
def env_config():
    """Return stored config for pre-filling UI"""
    return jsonify({
        "success": True,
        "config": {
            "jiraEmail": get_env('JIRA_EMAIL'),
            "jiraUrl": get_env('JIRA_URL'),
            "groqKey": "",
            "hasGroqKey": bool(get_env('GROQ_KEY')),
            "hasJiraToken": bool(get_env('JIRA_API_TOKEN'))
        }
    }), 200


@app.route('/api/fetch-issue', methods=['POST'])
def fetch_issue():
    try:
        data = request.json
        issue_key = data.get('issueKey')
        jira_email = data.get('jiraEmail') or get_env('JIRA_EMAIL')
        jira_token = data.get('jiraToken') or get_env('JIRA_API_TOKEN')
        jira_url = data.get('jiraUrl') or get_env('JIRA_URL')

        if not all([issue_key, jira_email, jira_token, jira_url]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        base_url = jira_url.split('/jira/')[0] if '/jira/' in jira_url else jira_url
        base_url = base_url.split('/browse/')[0] if '/browse/' in base_url else base_url

        connector = JiraConnector(base_url, jira_email, jira_token)
        result = connector.fetch_issue(issue_key)
        return jsonify(result), 200 if result.get('success') else 400

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/generate-strategy', methods=['POST'])
def generate_strategy():
    try:
        data = request.json
        jira_issue = data.get('jiraIssue')
        groq_key = data.get('groqKey') or get_env('GROQ_KEY')
        save_dir = data.get('saveDir', '/tmp/generated_strategies')

        if not all([jira_issue, groq_key]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        generator = GroqStrategyGenerator(groq_key)
        strategy_result = generator.generate_strategy(jira_issue)

        if not strategy_result.get('success'):
            return jsonify({"success": False, "error": strategy_result.get('error', 'Generation failed')}), 500

        validator = StrategyValidator()
        validation = validator.validate(strategy_result)

        file_manager = FileManager(save_dir)
        save_result = file_manager.save_strategy(strategy_result, jira_issue.get('key', 'unknown'))

        return jsonify({
            "success": True,
            "strategy_content": strategy_result.get('strategy_content'),
            "metadata": {
                "generation_time_ms": strategy_result.get('generation_time_ms'),
                "tokens_used": strategy_result.get('tokens_used'),
                "validation": validation,
                "saved_to": save_result.get('filepath')
            },
            "steps": {
                "groq_generation": strategy_result,
                "validation": validation,
                "save_markdown": save_result
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================
# Vercel handler
# ============================================================
# Vercel Python runtime expects a variable named 'app' (Flask/WSGI)
