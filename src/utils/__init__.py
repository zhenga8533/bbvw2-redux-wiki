"""
Utility modules for the wiki generator.

This module contains only pure utility functions and helpers
that have no domain-specific knowledge.
"""

from .logger_utils import get_logger, LogContext
from .text_utils import name_to_id

__all__ = [
    "get_logger",
    "LogContext",
    "name_to_id",
]
