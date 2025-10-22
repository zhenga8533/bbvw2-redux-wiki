"""
Dictionary utility functions.

This module contains general-purpose utilities for working with dictionaries.
"""

from collections import Counter
from typing import Any


def get_most_common_value(dictionary: dict[str, Any]) -> Any | None:
    """
    Get the most common value from a dictionary.

    If there's a tie, returns the first value in insertion order.
    None values are filtered out before counting.

    Args:
        dictionary: Dictionary with any keys and values

    Returns:
        The most common value, or None if dict is empty or all values are None

    Examples:
        >>> get_most_common_value({"a": "x", "b": "x", "c": "y"})
        'x'
        >>> get_most_common_value({"a": 1, "b": 2, "c": 1})
        1
        >>> get_most_common_value({"a": None, "b": None})
        None
        >>> get_most_common_value({})
        None
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
