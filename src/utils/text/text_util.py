"""
Text utility functions for name formatting, ID generation, and string manipulation.

This module provides common text processing utilities used throughout the codebase,
including name formatting with special cases, ID generation, and string comparison operations.
"""

import re
import itertools
import string

from src.utils.data.constants import (
    ITEM_DISPLAY_ABBREVIATIONS,
    ITEM_DISPLAY_CASES,
    POKEMON_DISPLAY_CASES,
)


def name_to_id(name: str) -> str:
    """
    Convert a name to a standardized ID format.

    Converts to lowercase, replaces spaces with hyphens, and removes
    non-alphanumeric characters (except hyphens). This is used for
    file names and string values in the JSON data.

    Note: JSON field names use snake_case, but this function produces
    kebab-case for file names and data values.

    Args:
        name: The name to convert.

    Returns:
        A standardized ID string (lowercase, kebab-case, alphanumeric only).

    Examples:
        >>> name_to_id("Mr. Mime")
        'mr-mime'
        >>> name_to_id("Farfetch'd")
        'farfetchd'
        >>> name_to_id("Ho-Oh")
        'ho-oh'
        >>> name_to_id("Nidoran♀")
        'nidoran'
        >>> name_to_id("Type: Null")
        'type-null'
    """
    # Convert to lowercase, replace spaces with hyphens, and remove non-alphanumeric characters
    id_str = name.replace("é", "e")
    id_str = re.sub(r"[^a-z0-9\s-]", "", id_str.lower())
    id_str = re.sub(r"\s+", "-", id_str)
    id_str = id_str.strip("-")
    return id_str


def format_display_name(
    name: str,
    special_cases: dict[str, str] = {},
    special_abbreviations: dict[str, str] = {},
) -> str:
    """
    Format a name for display with proper capitalization and special case handling.

    This function consolidates the name formatting logic previously duplicated across
    multiple generators (_format_name methods in pokemon_generator, move_generator, etc.).
    It handles special characters, applies title case, and processes both whole-name
    special cases and abbreviation replacements within names.

    Args:
        name: The name to format (e.g., "nidoran-f", "u-turn", "exp-share")
        special_cases: Optional dict mapping lowercase names to their special-cased versions
                      (e.g., {"nidoran f": "Nidoran♀", "u turn": "U-turn"})
        special_abbreviations: Optional dict mapping abbreviations to their replacements
                              (e.g., {"tm": "TM", "hp": "HP", "pp": "PP"})
                              These are applied within the name after title casing

    Returns:
        The formatted display name with proper capitalization

    Examples:
        >>> # Pokemon special cases
        >>> format_display_name("nidoran-f", {"nidoran f": "Nidoran♀"})
        'Nidoran♀'
        >>> # Move special cases
        >>> format_display_name("u-turn", {"u turn": "U-turn"})
        'U-turn'
        >>> # Item with abbreviations
        >>> format_display_name("exp-share", special_abbreviations={"exp": "Exp"})
        'Exp Share'
        >>> # Default title case
        >>> format_display_name("pikachu")
        'Pikachu'
    """
    # Handle special characters and formatting
    formatted_name = name.replace("-", " ").replace("_", " ")

    # Extend special cases and abbreviations with constants
    special_cases = special_cases | POKEMON_DISPLAY_CASES | ITEM_DISPLAY_ABBREVIATIONS
    special_abbreviations = special_abbreviations | ITEM_DISPLAY_CASES

    # Check for whole-name special cases first
    lower_name = formatted_name.lower()
    if lower_name in special_cases:
        return special_cases[lower_name]

    # Apply title case FIRST
    formatted_name = string.capwords(formatted_name)

    # Apply special abbreviation replacements AFTER title casing
    for abbr, replacement in special_abbreviations.items():
        # Use word boundary at start, but allow digits after
        formatted_name = re.sub(
            rf"\b{re.escape(abbr)}(?=\b|\d)",
            replacement,
            formatted_name,
            flags=re.IGNORECASE,
        )

    return formatted_name


def strip_common_prefix(string1: str, string2: str) -> str:
    """
    Removes the longest identical starting substring shared between string1 and string2
    from string2, including any common trailing punctuation like ', ' or ' '.

    Args:
        string1: The reference string (e.g., 'Surf, Normal').
        string2: The string to be stripped (e.g., 'Surf, Dark Spot').

    Returns:
        The remainder of string2 after the common prefix and any common separators
        are removed (e.g., 'Dark Spot').
    """
    common_chars = itertools.takewhile(
        lambda pair: pair[0] == pair[1], zip(string1, string2)
    )
    common_prefix = "".join(c for c, _ in common_chars)

    start_index = len(common_prefix)

    while start_index < len(string2) and string2[start_index] in (",", " "):
        start_index += 1

    return string2[start_index:]


def strip_common_suffix(string1: str, string2: str) -> str:
    """
    Removes the longest identical ending substring shared between string1 and string2
    from string2, including any common leading punctuation like ', ' or ' '.

    Args:
        string1: The reference string (e.g., 'Blue, Normal').
        string2: The string to be stripped (e.g., 'Red, Normal').

    Returns:
        The remainder of string2 after the common suffix and any common separators
        are removed (e.g., 'Red').
    """
    # 1. Find the longest common suffix
    common_chars = itertools.takewhile(
        lambda pair: pair[0] == pair[1],
        zip(reversed(string1), reversed(string2)),
    )
    common_suffix = "".join(c for c, _ in common_chars)[::-1]

    # 2. Determine the ending index for the result in string2
    end_index = len(string2) - len(common_suffix)

    # 3. Handle common leading separators (e.g., ', ' or ' ')
    # Move the index back past any trailing space or comma *in string2* # that is now at the end of the remaining string.
    # It removes multiple spaces/commas but stops at any other character.
    while end_index > 0 and string2[end_index - 1] in (",", " "):
        end_index -= 1

    # 4. Return the remainder of string2
    return string2[:end_index]


def extract_form_suffix(pokemon_name: str, base_name: str) -> str:
    """
    Extract the form suffix from a Pokemon name.

    Args:
        pokemon_name: Full Pokemon name (e.g., "giratina-altered")
        base_name: Base species name (e.g., "giratina")

    Returns:
        The form suffix, or empty string if no suffix exists.
        Examples:
            - ("giratina-altered", "giratina") -> "altered"
            - ("rotom", "rotom") -> ""
            - ("darmanitan-zen", "darmanitan") -> "zen"
    """
    if pokemon_name.startswith(base_name):
        suffix = pokemon_name[len(base_name) :].lstrip("-")
        return suffix
    return ""
