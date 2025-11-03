"""
Singleton configuration loader for easy access to config.json.

This module provides a singleton pattern for loading and accessing application
configuration from config.json. The configuration is loaded only once on first
access and cached for subsequent calls, improving performance.

Configuration Structure:
    The config.json file is expected to be located in the src/ directory and
    contains application-wide settings such as parser and generator registries,
    file paths, and other configuration options.

Usage:
    from src.utils.core.config_util import get_config

    config = get_config()
    parsers = config.get("parsers", [])
    generators = config.get("generators", [])

Error Handling:
    If config.json is not found or contains invalid JSON, an empty dictionary
    is returned and an error message is printed to stdout. This ensures the
    application can continue running with default values.
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
        config_path = Path(__file__).parent.parent.parent / "config.json"
        try:
            with config_path.open("r", encoding="utf-8") as f:
                _config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # In case of error, return an empty dict or handle appropriately
            print(f"Error loading config.json: {e}")
            _config = {}
    return _config or {}
