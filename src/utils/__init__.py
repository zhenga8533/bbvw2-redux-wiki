"""
Utility modules for the wiki generator.

This module contains only pure utility functions and helpers
that have no domain-specific knowledge.

The utilities are organized into subdirectories:
- core/: Core infrastructure (config, logging, component system)
- formatters/: Output formatting (markdown, tables, YAML)
- data/: Pokemon-specific domain logic (constants, type effectiveness)
- text/: Text processing utilities
- services/: Business logic services

Note: Some utilities are excluded from __init__.py:
- markdown_util: Excluded to avoid circular imports (imports from src.data.pokedb_loader)
  Import directly: from src.utils.formatters.markdown_util import format_move
- registry_util: Internal runtime utility for component registration
- component_runner: Internal runtime utility for running registered components
"""

# Core utilities
from .core.logger import LogContext, get_logger

# Re-export commonly used constants
from .data.constants import (
    DAMAGE_CLASS_ICONS,
    POKEMON_FORM_SUBFOLDERS,
    TYPE_COLORS,
)

# Pokemon utilities
from .data.type_effectiveness import TYPE_CHART, calculate_type_effectiveness

# Text utilities
from .text.dict_util import get_most_common_value
from .text.text_util import extract_form_suffix, format_display_name, name_to_id

__all__ = [
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
    "DAMAGE_CLASS_ICONS",
    "POKEMON_FORM_SUBFOLDERS",
]
