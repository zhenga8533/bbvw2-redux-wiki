"""
Utility modules for the wiki generator.

This module contains only pure utility functions and helpers
that have no domain-specific knowledge.

Note: markdown_util is intentionally excluded from __init__.py to avoid
circular imports, as it imports from src.data.pokedb_loader. Import it
directly when needed: from src.utils.markdown_util import format_move
"""

from .config_util import get_config
from .dict_util import get_most_common_value
from .logger_util import get_logger, LogContext
from .text_util import name_to_id

__all__ = [
    "get_config",
    "get_logger",
    "LogContext",
    "name_to_id",
    "get_most_common_value",
]
