"""
test_runner.py — Safely executes generated pytest code and runs the full
pre-written test suite via subprocess, parsing results into JSON.
"""

import json
import os
import subprocess
import sys
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
PROJECT_ROOT = os.path.dirname(BASE_DIR)                                 # repo root
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")
DB_PATH = os.path.join(BASE_DIR, "database", "etl_qa.db")


def _env_with_db() -> dict:
    env = os.environ.copy()
    env["DATABASE_PATH"] = DB_PATH
    return env


# Hardcoded relative DB paths that AI-generated tests sometimes use.
_LEGACY_DB_PATHS = [
    "../backend/database/etl_qa.db",
    "./backend/database/etl_qa.db",
    "backend/database/etl_qa.db",
    "etl_qa.db",
]


def _rewrite_db_paths(test_code: str) -> str:
    """
    Rewrite any hardcoded relative DB path in generated test code to the
    absolute path (no os import needed, works in any cwd).
    """
    import re

    abs_path = repr(DB_PATH)
    for legacy in _LEGACY_DB_PATHS:
        escaped = re.escape(legacy)
        test_code = re.sub(rf"['\"]({escaped})['\"]", abs_path, test_code)
    return test_code


def run_single_test(test_code: str) -> dict:
    """
    Write the provided test code to a temporary file and run it with pytest.

    Returns a dict: {"passed": bool, "output": str, "error": str}
    """
    if not test_code or "def test" not in test_code:
        return {
            "passed": False,
            "output": "",
            "error": "No valid pytest test function found in the provided code.",
        }

    test_code = _rewrite_db_paths(test_code)

    tmp_dir = tempfile.mkdtemp(prefix="etlqa_test_")
    tmp_file = os.path.join(tmp_dir, "test_generated.py")
    with open(tmp_file, "w") as f:
        f.write(test_code)

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", tmp_file, "-v", "--tb=short", "-p", "no:cacheprovider"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=_env_with_db(),
            timeout=60,
        )
        output = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
        passed = proc.returncode == 0
        return {
            "passed": passed,
            "output": output.strip(),
            "error": "" if passed else "One or more assertions failed. See output.",
        }
    except subprocess.TimeoutExpired:
        return {"passed": False, "output": "", "error": "Test execution timed out (60s)."}
    except Exception as exc:  # pragma: no cover
        return {"passed": False, "output": "", "error": str(exc)}
    finally:
        try:
            os.remove(tmp_file)
            os.rmdir(tmp_dir)
        except OSError:
            pass


def run_all_tests() -> dict:
    """
    Run the entire pre-written pytest suite in the tests/ directory using the
    pytest-json-report plugin and return structured results.

    Returns:
      {
        "summary": {"total": int, "passed": int, "failed": int},
        "tests": [{"name": str, "outcome": "passed"|"failed", "message": str}, ...],
        "raw_output": str
      }
    """
    report_fd, report_path = tempfile.mkstemp(suffix=".json", prefix="etlqa_report_")
    os.close(report_fd)

    try:
        proc = subprocess.run(
            [
                sys.executable, "-m", "pytest", TESTS_DIR,
                "-v", "--tb=short", "-p", "no:cacheprovider",
                "--json-report", f"--json-report-file={report_path}",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            env=_env_with_db(),
            timeout=120,
        )
        raw_output = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")

        tests = []
        summary = {"total": 0, "passed": 0, "failed": 0}

        if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
            with open(report_path) as f:
                data = json.load(f)
            for t in data.get("tests", []):
                nodeid = t.get("nodeid", "")
                name = nodeid.split("::")[-1] if "::" in nodeid else nodeid
                outcome = t.get("outcome", "unknown")
                message = ""
                call = t.get("call") or {}
                crash = (call.get("crash") or {})
                if outcome != "passed":
                    message = crash.get("message", "") or call.get("longrepr", "") or ""
                tests.append({
                    "name": name,
                    "nodeid": nodeid,
                    "outcome": outcome,
                    "message": message[:500],
                })
            s = data.get("summary", {})
            summary = {
                "total": s.get("total", len(tests)),
                "passed": s.get("passed", 0),
                "failed": s.get("failed", 0),
            }
        else:
            summary["error"] = "Could not produce JSON report."

        return {"summary": summary, "tests": tests, "raw_output": raw_output.strip()}
    except subprocess.TimeoutExpired:
        return {
            "summary": {"total": 0, "passed": 0, "failed": 0},
            "tests": [],
            "raw_output": "Test suite execution timed out (120s).",
        }
    finally:
        try:
            os.remove(report_path)
        except OSError:
            pass
