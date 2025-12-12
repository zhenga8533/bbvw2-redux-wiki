"""
Dictionary utility functions.

This module contains general-purpose utilities for working with dictionaries.
"""

from collections import Counter
from typing import Any


def get_most_common_value(dictionary: dict[str, Any]) -> Any | None:
    """Get the most common value from a dictionary.

    Args:
        dictionary (dict[str, Any]): Dictionary with any keys and values

    Returns:
        Any | None: The most common value, or None if the dictionary is empty or has no non-None values.
    """
    if not dictionary:
        return None

    # Filter out None values
    non_none_values = [v for v in dictionary.values() if v is not None]

    if not non_none_values:
        return None

    # Count occurrences
    counter = Counter(non_none_values)

    # Get most common - returns list of (value, count) tuples
    # In case of tie, Counter.most_common() returns them in first-seen order
    most_common = counter.most_common(1)

    return most_common[0][0] if most_common else None
