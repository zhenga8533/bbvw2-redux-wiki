"""
Logger utilities for the wiki generator.

Provides both basic logging setup and structured change logging for parsers.
"""

import json
import logging
import sys
import io
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


# Fix Windows console encoding for Unicode characters (only once)
if sys.platform == "win32" and not isinstance(sys.stdout, io.TextIOWrapper):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except (AttributeError, ValueError):
        # Already wrapped or not a buffered stream
        pass


def setup_logger(name: str, file_path: str):
    """
    Set up a logger that logs to a file named after the calling script.

    Args:
        name: Logger name (typically __name__)
        file_path: Path to the calling script (typically __file__)

    Returns:
        Logger instance configured for both file and console output

    Note:
        Logs are reset on each run (file mode='w')
    """

    log_filename = f"{Path(file_path).stem}.log"
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / log_filename

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    # Create formatters
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    # Console handler with UTF-8 encoding
    c_handler = logging.StreamHandler()
    c_handler.setFormatter(console_formatter)
    logger.addHandler(c_handler)

    # File handler (overwrites the file on each run) with UTF-8 encoding
    f_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    f_handler.setFormatter(file_formatter)
    logger.addHandler(f_handler)

    return logger


class ChangeLogger:
    """
    Mixin class for logging data changes in parsers.

    Provides methods to track, format, and output changes made to data files.
    """

    def __init__(self):
        """Initialize the change logger."""
        self.changes_log: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(self.__class__.__name__)

    def log_change(
        self,
        entity_type: str,
        entity_name: str,
        field: str,
        old_value: Any,
        new_value: Any,
        file_path: Optional[Path] = None,
        metadata: Optional[Dict] = None,
    ):
        """
        Log a single data change.

        Args:
            entity_type: Type of entity (e.g., 'pokemon', 'move', 'item')
            entity_name: Name/ID of the entity being modified
            field: Field being changed (e.g., 'evolution_chain', 'base_stats')
            old_value: Previous value (None if new)
            new_value: New value
            file_path: Path to the file being modified
            metadata: Additional context about the change
        """
        change_entry = {
            "timestamp": datetime.now().isoformat(),
            "entity_type": entity_type,
            "entity_name": entity_name,
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
            "file_path": str(file_path) if file_path else None,
            "metadata": metadata or {},
        }
        self.changes_log.append(change_entry)

        # Log to console
        self._log_to_console(change_entry)

    def _log_to_console(self, change: Dict[str, Any]):
        """Format and log change to console."""
        entity = f"{change['entity_type'].upper()}: {change['entity_name']}"
        field = change['field']
        old = self._format_value(change['old_value'])
        new = self._format_value(change['new_value'])

        if old is None:
            self.logger.info(f"  [ADD] {entity}.{field} = {new}")
        elif new is None:
            self.logger.info(f"  [REMOVE] {entity}.{field} (was: {old})")
        else:
            self.logger.info(f"  [UPDATE] {entity}.{field}: {old} -> {new}")

    def _format_value(self, value: Any, max_length: int = 60) -> str:
        """Format a value for display in logs."""
        if value is None:
            return "None"

        # Handle dict/list
        if isinstance(value, (dict, list)):
            formatted = json.dumps(value, ensure_ascii=False)
            if len(formatted) > max_length:
                return formatted[:max_length] + "..."
            return formatted

        # Handle strings
        if isinstance(value, str):
            if len(value) > max_length:
                return value[:max_length] + "..."
            return f'"{value}"'

        return str(value)

    def log_file_update(self, file_path: Path, action: str = "updated"):
        """
        Log that a file was updated.

        Args:
            file_path: Path to the file
            action: Action performed (updated, created, deleted)
        """
        self.logger.info(f"  [FILE] {action}: {file_path}")

    def get_change_summary(self) -> Dict[str, Any]:
        """
        Generate a summary of all changes.

        Returns:
            dict: Summary statistics and grouped changes
        """
        if not self.changes_log:
            return {
                "total_changes": 0,
                "by_entity_type": {},
                "by_action": {},
                "files_modified": [],
            }

        # Count by entity type
        by_entity_type = {}
        for change in self.changes_log:
            entity_type = change["entity_type"]
            by_entity_type[entity_type] = by_entity_type.get(entity_type, 0) + 1

        # Count by action type
        by_action = {"add": 0, "update": 0, "remove": 0}
        for change in self.changes_log:
            if change["old_value"] is None:
                by_action["add"] += 1
            elif change["new_value"] is None:
                by_action["remove"] += 1
            else:
                by_action["update"] += 1

        # Get unique files modified
        files_modified = list(
            {c["file_path"] for c in self.changes_log if c["file_path"]}
        )

        return {
            "total_changes": len(self.changes_log),
            "by_entity_type": by_entity_type,
            "by_action": by_action,
            "files_modified": files_modified,
        }

    def save_change_log(self, output_path: Path):
        """
        Save the complete change log to a JSON file.

        Args:
            output_path: Path to save the log file
        """
        log_data = {
            "summary": self.get_change_summary(),
            "changes": self.changes_log,
            "generated_at": datetime.now().isoformat(),
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Change log saved to: {output_path}")

    def print_change_summary(self):
        """Print a human-readable summary of changes to console."""
        summary = self.get_change_summary()

        if summary["total_changes"] == 0:
            self.logger.info("No changes made.")
            return

        self.logger.info("\n" + "=" * 60)
        self.logger.info("CHANGE SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Total changes: {summary['total_changes']}")

        if summary["by_entity_type"]:
            self.logger.info("\nBy entity type:")
            for entity_type, count in summary["by_entity_type"].items():
                self.logger.info(f"  - {entity_type}: {count}")

        if summary["by_action"]:
            self.logger.info("\nBy action:")
            for action, count in summary["by_action"].items():
                if count > 0:
                    self.logger.info(f"  - {action}: {count}")

        if summary["files_modified"]:
            self.logger.info(f"\nFiles modified: {len(summary['files_modified'])}")

        self.logger.info("=" * 60 + "\n")
