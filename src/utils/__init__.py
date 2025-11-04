"""
Utility modules for the wiki generator.

This module contains only pure utility functions and helpers
that have no domain-specific knowledge.

The utilities are organized into subdirectories:
- core/: Core infrastructure (config, logging, component system)
- formatters/: Output formatting (markdown, tables, YAML)
- pokemon/: Pokemon-specific domain logic (constants, type effectiveness)
- text/: Text processing utilities

Note: Some utilities are excluded from __init__.py:
- markdown_util: Excluded to avoid circular imports (imports from src.data.pokedb_loader)
  Import directly: from src.utils.formatters.markdown_util import format_move
- registry_util: Internal runtime utility for component registration
- component_runner: Internal runtime utility for running registered components
"""

# Core utilities
from .core.config import get_config
from .core.logger import get_logger, LogContext

# Text utilities
from .text.dict_util import get_most_common_value
from .text.text_util import name_to_id, format_display_name, extract_form_suffix

# Pokemon utilities
from .data.type_effectiveness import calculate_type_effectiveness, TYPE_CHART

# Re-export commonly used constants
from .data.constants import (
    TYPE_COLORS,
    ITEM_NAME_SPECIAL_CASES,
    DAMAGE_CLASS_ICONS,
    GENERATION_DISPLAY_NAMES,
    GENERATION_ORDER,
    POKEMON_FORM_SUBFOLDERS_ALL,
    POKEMON_FORM_SUBFOLDERS_STANDARD,
)

__all__ = [
    # Config utilities
    "get_config",
    # Logging utilities
    "get_logger",
    "LogContext",
    # Text utilities
    "name_to_id",
    "format_display_name",
    "extract_form_suffix",
    # Dict utilities
    "get_most_common_value",
    # Type effectiveness
    "calculate_type_effectiveness",
    "TYPE_CHART",
    # Constants
    "TYPE_COLORS",
    "ITEM_NAME_SPECIAL_CASES",
    "DAMAGE_CLASS_ICONS",
    "GENERATION_DISPLAY_NAMES",
    "GENERATION_ORDER",
    "POKEMON_FORM_SUBFOLDERS_ALL",
    "POKEMON_FORM_SUBFOLDERS_STANDARD",
]
