#!/usr/bin/env python3
"""
File Manager - Save and export test strategies
Layer 3: Deterministic file operations tool
"""

import json
import os
from datetime import datetime
from pathlib import Path

class FileManager:
    """Manage strategy file operations"""

    def __init__(self, base_dir=None):
        """Initialize file manager with base directory"""
        if base_dir is None:
            base_dir = Path(__file__).parent.parent / "generated_strategies"
        else:
            base_dir = Path(base_dir)

        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_strategy(self, strategy_data, issue_key):
        """
        Save strategy to markdown file

        Args:
            strategy_data: dict with strategy_content
            issue_key: JIRA issue key (e.g., "KAN-1")

        Returns:
            dict with file path and status
        """

        try:
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{issue_key}_TestStrategy_{timestamp}.md"
            filepath = self.base_dir / filename

            # Prepare content
            content = strategy_data.get("strategy_content", "")

            # Add header with metadata
            header = f"""# Test Strategy: {issue_key}

**Generated:** {datetime.now().isoformat()}
**Source:** JIRA Issue {issue_key}

---

"""

            full_content = header + content

            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)

            return {
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "filepath": str(filepath),
                "filename": filename,
                "size_bytes": os.path.getsize(filepath)
            }

        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }

    def save_json(self, data, issue_key):
        """
        Save strategy data as JSON (for programmatic access)

        Args:
            data: dict with full strategy data
            issue_key: JIRA issue key

        Returns:
            dict with file path and status
        """

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{issue_key}_Strategy_{timestamp}.json"
            filepath = self.base_dir / filename

            # Add metadata
            data_with_meta = {
                "metadata": {
                    "issue_key": issue_key,
                    "saved_at": datetime.now().isoformat(),
                    "file_format": "json"
                },
                "data": data
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_with_meta, f, indent=2)

            return {
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "filepath": str(filepath),
                "filename": filename,
                "size_bytes": os.path.getsize(filepath)
            }

        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }

    def list_strategies(self):
        """List all saved strategies"""
        try:
            files = list(self.base_dir.glob("*_TestStrategy_*.md"))

            return {
                "success": True,
                "count": len(files),
                "strategies": [
                    {
                        "filename": f.name,
                        "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                        "size_bytes": f.stat().st_size
                    }
                    for f in sorted(files, reverse=True)
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_strategy_path(self):
        """Get the directory where strategies are saved"""
        return str(self.base_dir)


# CLI Usage
if __name__ == "__main__":
    manager = FileManager()

    sample_data = {
        "strategy_content": "# Test Strategy\n\nThis is a test strategy content."
    }

    # Save markdown
    result = manager.save_strategy(sample_data, "KAN-1")
    print("Save result:")
    print(json.dumps(result, indent=2))

    # List saved strategies
    print("\nSaved strategies:")
    list_result = manager.list_strategies()
    print(json.dumps(list_result, indent=2))
