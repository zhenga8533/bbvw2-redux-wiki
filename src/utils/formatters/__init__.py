"""
Output formatting utilities.

This module provides formatters for various output types including markdown,
tables, and YAML. Note that markdown_formatter has dependencies on the data
layer (PokeDBLoader) and is therefore domain-aware rather than a pure utility.

Import patterns:
- Package-level imports for commonly used formatters:
  from src.utils.formatters import create_table, format_type_badge
- Direct imports for specialized formatters:
  from src.utils.formatters.yaml_formatter import update_pokedex_subsection
"""

from .markdown_formatter import (
    format_ability,
    format_checkbox,
    format_item,
    format_move,
    format_pokemon,
    format_pokemon_card_grid,
    format_stat_bar,
    format_type_badge,
)
from .table_formatter import create_table
from .yaml_formatter import (
    load_mkdocs_config,
    save_mkdocs_config,
    update_pokedex_subsection,
)

__all__ = [
    # Markdown formatters
    "format_ability",
    "format_checkbox",
    "format_item",
    "format_move",
    "format_pokemon",
    "format_pokemon_card_grid",
    "format_stat_bar",
    "format_type_badge",
    # Table formatters
    "create_table",
    # YAML formatters
    "load_mkdocs_config",
    "save_mkdocs_config",
    "update_pokedex_subsection",
]
