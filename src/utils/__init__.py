"""
Utility modules for the wiki generator.

This module contains only pure utility functions and helpers
that have no domain-specific knowledge.
"""

from .logger import setup_logger, ChangeLogger
from .text_utils import name_to_id

__all__ = [
    "setup_logger",
    "ChangeLogger",
    "name_to_id",
]
