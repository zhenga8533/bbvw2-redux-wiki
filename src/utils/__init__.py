"""
Utility modules for the wiki generator.

This module provides commonly used utility functions organized into subdirectories:

Structure:
- core/: Core infrastructure (config, logging, component system)
- formatters/: Output formatting (markdown, tables, YAML)
- data/: Pokemon-specific domain logic (constants, type effectiveness)
- text/: Text processing utilities
- services/: Business logic services

Import Conventions:
1. Package-level imports for commonly used utilities:
   from src.utils import get_logger, format_display_name

2. Direct module imports for specialized/rarely used utilities:
   from src.utils.formatters.yaml_formatter import update_pokedex_subsection
   from src.utils.services import AttributeService

Note: markdown_formatter in formatters/ imports from src.utils.data.loaders.pokedb_loader,
making it domain-aware rather than a pure utility. This is intentional to
provide convenient Pokemon-specific formatting functions.
"""

# Core utilities
from .core.logger import LogContext, get_logger

# Re-export commonly used constants
from .data.constants import (
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
    "POKEMON_FORM_SUBFOLDERS",
]
