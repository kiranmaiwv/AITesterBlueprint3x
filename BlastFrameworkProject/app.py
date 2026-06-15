#!/usr/bin/env python3
"""
Flask Backend Server - API for React UI
Layer 2: Navigation & request handling
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
from pathlib import Path
import json

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent / "tools"))

from jira_connector import JiraConnector
from groq_strategy_generator import GroqStrategyGenerator
from validator import StrategyValidator
from file_manager import FileManager
from orchestrator import StrategyOrchestrator

app = Flask(__name__)
CORS(app)


def load_env():
    """Load .env file values (for pre-filling the UI)"""
    env_path = Path(__file__).parent / ".env"
    env_vars = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    env = load_env()
    return jsonify({
        "status": "healthy",
        "service": "JIRA Test Strategy Generator API",
        "has_groq_key": bool(env.get('GROQ_KEY', '').startswith('gsk_')),
        "has_jira_creds": bool(env.get('JIRA_EMAIL') and env.get('JIRA_API_TOKEN'))
    }), 200


@app.route('/api/env-config', methods=['GET'])
def env_config():
    """Return stored .env config (for pre-filling UI)"""
    env = load_env()
    return jsonify({
        "success": True,
        "config": {
            "jiraEmail": env.get('JIRA_EMAIL', ''),
            "jiraUrl": env.get('JIRA_URL', ''),
            "groqKey": "",
            "hasGroqKey": bool(env.get('GROQ_KEY')),
            "hasJiraToken": bool(env.get('JIRA_API_TOKEN'))
        }
    }), 200


@app.route('/api/fetch-issue', methods=['POST'])
def fetch_issue():
    """
    Fetch a JIRA issue
    POST body: { issueKey, jiraEmail, jiraToken, jiraUrl }
    """
    try:
        data = request.json
        issue_key = data.get('issueKey')
        jira_email = data.get('jiraEmail')
        jira_token = data.get('jiraToken')
        jira_url = data.get('jiraUrl')

        if not all([issue_key, jira_email, jira_token, jira_url]):
            return jsonify({
                "success": False,
                "error": "Missing required fields"
            }), 400

        # Extract base URL from full JIRA URL
        base_url = jira_url.split('/jira/')[0] if '/jira/' in jira_url else jira_url
        base_url = base_url.split('/browse/')[0] if '/browse/' in base_url else base_url

        connector = JiraConnector(base_url, jira_email, jira_token)
        result = connector.fetch_issue(issue_key)

        return jsonify(result), 200 if result.get('success') else 400

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/generate-strategy', methods=['POST'])
def generate_strategy():
    """
    Generate test strategy from JIRA issue
    POST body: { issueKey, jiraIssue, groqKey, saveDir }
    """
    try:
        data = request.json
        jira_issue = data.get('jiraIssue')
        groq_key = data.get('groqKey')
        save_dir = data.get('saveDir', './generated_strategies')

        if not all([jira_issue, groq_key]):
            return jsonify({
                "success": False,
                "error": "Missing required fields"
            }), 400

        generator = GroqStrategyGenerator(groq_key)
        strategy_result = generator.generate_strategy(jira_issue)

        if not strategy_result.get('success'):
            return jsonify({
                "success": False,
                "error": strategy_result.get('error', 'Generation failed')
            }), 500

        # Validate
        validator = StrategyValidator()
        validation = validator.validate(strategy_result)

        # Save files
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
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/generate-full', methods=['POST'])
def generate_full():
    """
    Full orchestration: fetch issue + generate strategy in one call
    """
    try:
        data = request.json
        issue_key = data.get('issueKey')
        jira_email = data.get('jiraEmail')
        jira_token = data.get('jiraToken')
        jira_url = data.get('jiraUrl')
        groq_key = data.get('groqKey')
        save_dir = data.get('saveDir', './generated_strategies')

        if not all([issue_key, jira_email, jira_token, jira_url, groq_key]):
            return jsonify({
                "success": False,
                "error": "Missing required fields"
            }), 400

        base_url = jira_url.split('/jira/')[0] if '/jira/' in jira_url else jira_url
        base_url = base_url.split('/browse/')[0] if '/browse/' in base_url else base_url

        orchestrator = StrategyOrchestrator(base_url, jira_email, jira_token, groq_key, save_dir)
        result = orchestrator.generate_full_strategy(issue_key)

        if result.get('status') == 'SUCCESS':
            return jsonify({
                "success": True,
                **result
            }), 200
        else:
            return jsonify({
                "success": False,
                **result
            }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/strategies', methods=['GET'])
def list_strategies():
    """List all generated strategies"""
    try:
        save_dir = request.args.get('saveDir', './generated_strategies')
        file_manager = FileManager(save_dir)
        result = file_manager.list_strategies()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5050)
