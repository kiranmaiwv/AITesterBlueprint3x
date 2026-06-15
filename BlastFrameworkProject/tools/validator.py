#!/usr/bin/env python3
"""
Validator - Validate test strategies match format requirements
Layer 3: Deterministic validation tool
"""

import re
import json
from datetime import datetime

class StrategyValidator:
    """Validate test strategy outputs against requirements"""

    REQUIRED_SECTIONS = [
        "objective",
        "scope",
        "focus areas",
        "approach",
        "deliverables",
        "team & schedule",
        "entry",  # entry & exit criteria
        "exit",
        "risks"
    ]

    MIN_WORDS = 800
    MAX_WORDS = 3000

    @staticmethod
    def count_words(text):
        """Count words in text"""
        return len(text.split())

    @staticmethod
    def has_required_sections(content):
        """Check if content has all required sections (case-insensitive)"""
        content_lower = content.lower()
        missing = []

        for section in StrategyValidator.REQUIRED_SECTIONS:
            if section not in content_lower:
                missing.append(section)

        return missing

    @staticmethod
    def is_valid_markdown(content):
        """Check if content is valid markdown"""
        # Must have headings
        if not re.search(r'^#{1,6}\s', content, re.MULTILINE):
            return False, "No markdown headings found"

        # Must not have unmatched brackets
        if content.count('{') != content.count('}'):
            return False, "Unmatched curly braces"

        return True, "Valid markdown"

    @staticmethod
    def validate(strategy_data):
        """
        Validate strategy output

        Args:
            strategy_data: dict with strategy_content key

        Returns:
            dict with validation result
        """

        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }

        if not strategy_data or "strategy_content" not in strategy_data:
            validation_result["valid"] = False
            validation_result["errors"].append("No strategy_content in input")
            return validation_result

        content = strategy_data["strategy_content"]

        # Check 1: Not empty
        if not content or len(content.strip()) == 0:
            validation_result["valid"] = False
            validation_result["errors"].append("Strategy content is empty")
            return validation_result

        # Check 2: Word count
        word_count = StrategyValidator.count_words(content)
        validation_result["statistics"]["word_count"] = word_count

        if word_count < StrategyValidator.MIN_WORDS:
            validation_result["valid"] = False
            validation_result["errors"].append(
                f"Content too short: {word_count} words (minimum: {StrategyValidator.MIN_WORDS})"
            )
        elif word_count > StrategyValidator.MAX_WORDS:
            validation_result["warnings"].append(
                f"Content quite long: {word_count} words (recommended max: {StrategyValidator.MAX_WORDS})"
            )

        # Check 3: Required sections
        missing = StrategyValidator.has_required_sections(content)
        if missing:
            validation_result["valid"] = False
            validation_result["errors"].append(
                f"Missing sections: {', '.join(missing)}"
            )
        validation_result["statistics"]["sections_found"] = len(StrategyValidator.REQUIRED_SECTIONS) - len(missing)

        # Check 4: Valid markdown
        is_valid, markdown_msg = StrategyValidator.is_valid_markdown(content)
        if not is_valid:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Invalid markdown: {markdown_msg}")

        # Check 5: No code injection
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'onclick=',
            r'onerror='
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                validation_result["valid"] = False
                validation_result["errors"].append(f"Potential security issue: {pattern}")

        return validation_result


# CLI Usage
if __name__ == "__main__":
    import sys

    sample_strategy = {
        "strategy_content": """# Test Strategy for User Authentication & SSO Integration

## Objective
...
""" + " word " * 300  # Padded to have reasonable word count
    }

    result = StrategyValidator.validate(sample_strategy)
    print(json.dumps(result, indent=2))
