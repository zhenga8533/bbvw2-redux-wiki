"""
Utility modules for the wiki generator.

This module contains only pure utility functions and helpers
that have no domain-specific knowledge.
"""

from .dict_util import get_most_common_value
from .logger_util import get_logger, LogContext
from .text_util import name_to_id

__all__ = [
    "get_logger",
    "LogContext",
    "name_to_id",
    "get_most_common_value",
]
