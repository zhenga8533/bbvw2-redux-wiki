"""
Singleton configuration loader for easy access to config.json.
"""

import json
from pathlib import Path
from typing import Any

_config: dict[str, Any] | None = None


def get_config() -> dict[str, Any]:
    """
    Load config.json and return it as a dictionary.

    Implements a singleton pattern to ensure the file is read only once.

    Returns:
        dict: The application configuration.
    """
    global _config
    if _config is None:
        config_path = Path(__file__).parent.parent / "config.json"
        try:
            with config_path.open("r", encoding="utf-8") as f:
                _config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # In case of error, return an empty dict or handle appropriately
            print(f"Error loading config.json: {e}")
            _config = {}
    return _config or {}
