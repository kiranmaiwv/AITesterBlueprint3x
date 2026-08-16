"""
ai_generator.py — Generates pytest test code from a natural-language description
using OpenAI's GPT-4o-mini model.

The OpenAI API key is read from the OPENAI_API_KEY environment variable. If no
key is configured (or the API call fails), a deterministic template-based
fallback generator is used so the app still works end-to-end without a key.
"""

import os
import re

SYSTEM_PROMPT = (
    "You are a senior QA engineer expert in ETL testing with pytest and SQLite. "
    "Generate a single pytest test function that tests the described ETL data "
    "quality condition against a SQLite database. Import sqlite3 and os in the "
    "function. Connect using: db_path = os.environ.get(\"DATABASE_PATH\", "
    "\"../backend/database/etl_qa.db\") . Return ONLY the python function code, "
    "no markdown, no explanation."
)


def _strip_markdown_fences(text: str) -> str:
    """Remove ```python ... ``` fences if the model wrapped the code."""
    text = text.strip()
    fence = re.match(r"^```(?:python)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        return fence.group(1).strip()
    return text


def _slugify(description: str) -> str:
    """Turn a free-text description into a valid python identifier suffix."""
    slug = re.sub(r"[^a-z0-9]+", "_", description.lower()).strip("_")
    slug = slug[:50] or "generated"
    return slug


def _template_fallback(description: str) -> str:
    """
    Deterministic fallback used when no OpenAI key is available or the API call
    fails. Produces a runnable pytest function that connects to the DB and runs
    a generic sanity check, embedding the user's description as context.
    """
    name = _slugify(description)
    safe_desc = description.replace('"', "'")
    return f'''def test_{name}():
    """Auto-generated (template fallback) test for: {safe_desc}"""
    import os
    import sqlite3

    db_path = os.environ.get("DATABASE_PATH", "../backend/database/etl_qa.db")
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        # Generic data-quality sanity check across the customers table.
        # Replace this logic with the specific condition you described:
        # "{safe_desc}"
        cur.execute("SELECT COUNT(*) FROM customers")
        total = cur.fetchone()[0]
        assert total > 0, "Expected at least one customer row"
    finally:
        conn.close()
'''


def generate_test_code(description: str) -> str:
    """
    Generate a pytest function from a natural-language description.

    Returns the python source of a single test function as a string.
    """
    if not description or not description.strip():
        raise ValueError("description must not be empty")

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return _template_fallback(description)

    try:
        # Imported lazily so the module works even if openai isn't installed.
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": description.strip()},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        code = _strip_markdown_fences(content)
        if "def test" not in code:
            # Model didn't return a proper test — fall back.
            return _template_fallback(description)
        return code
    except Exception:
        # Any failure (bad key, network, quota) -> graceful fallback.
        return _template_fallback(description)
