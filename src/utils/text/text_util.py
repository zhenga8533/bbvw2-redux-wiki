"""
Text utility functions for name formatting, ID generation, and string manipulation.

This module provides common text processing utilities used throughout the codebase,
including name formatting with special cases, ID generation, and string comparison operations.
"""

import itertools
import re
import string

from src.utils.data.constants import (
    ITEM_DISPLAY_ABBREVIATIONS,
    ITEM_DISPLAY_CASES,
    POKEMON_DISPLAY_CASES,
)


def name_to_id(name: str) -> str:
    """Convert a name to a standardized ID format.

    Args:
        name (str): The name to convert.

    Returns:
        str: A standardized ID string (lowercase, kebab-case, alphanumeric only).
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
    """Format a name for display with proper capitalization and special case handling.

    Args:
        name (str): The name to format.
        special_cases (dict[str, str], optional): Mapping of lowercase names to their special-cased versions. Defaults to {}.
        special_abbreviations (dict[str, str], optional): Mapping of abbreviations to their replacements. Defaults to {}.

    Returns:
        str: The formatted display name.
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
    """Remove the longest identical starting substring shared between string1 and string2

    Args:
        string1 (str): The first string to compare.
        string2 (str): The second string to compare.

    Returns:
        str: The portion of string2 that comes after the common prefix.
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
    """Remove the longest identical ending substring shared between string1 and string2

    Args:
        string1 (str): The first string to compare.
        string2 (str): The second string to compare.

    Returns:
        str: The portion of string2 that comes after the common suffix.
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
    """Extract the form suffix from a Pokemon name.

    Args:
        pokemon_name (str): The full name of the Pokemon.
        base_name (str): The base name of the Pokemon.

    Returns:
        str: The form suffix, or empty string if no suffix exists.
    """
    if pokemon_name.startswith(base_name):
        suffix = pokemon_name[len(base_name) :].lstrip("-")
        return suffix
    return ""


def parse_pokemon_forme(pokemon_name: str) -> tuple[str, str]:
    """Parse a Pokemon name to extract base name and forme.

    Handles various forme name formats:
    - "Wormadam Plant Cloak" -> ("wormadam", "plant")
    - "Rotom Fan" -> ("rotom", "fan")
    - "Deoxys Speed" -> ("deoxys", "speed")
    - "Pikachu" -> ("pikachu", "")

    Common forme suffixes to remove: Cloak, Forme, Form

    Args:
        pokemon_name (str): The full Pokemon name (e.g., "Wormadam Plant Cloak")

    Returns:
        tuple[str, str]: A tuple of (base_pokemon_id, forme_id)
            - base_pokemon_id: The base Pokemon ID in kebab-case
            - forme_id: The forme ID in kebab-case, or empty string if no forme
    """
    # Convert to ID format first
    pokemon_id = name_to_id(pokemon_name)

    # List of known Pokemon with formes and their base names
    # Format: (base_name, number_of_words_in_base)
    forme_pokemon = [
        ("wormadam", 1),  # Wormadam Plant/Sandy/Trash Cloak
        ("rotom", 1),  # Rotom Heat/Wash/Frost/Fan/Mow
        ("deoxys", 1),  # Deoxys Normal/Attack/Defense/Speed
        ("shaymin", 1),  # Shaymin Land/Sky
        ("giratina", 1),  # Giratina Altered/Origin
        ("arceus", 1),  # Arceus (various types)
        ("basculin", 1),  # Basculin Red-Striped/Blue-Striped
        ("darmanitan", 1),  # Darmanitan Standard/Zen
        ("tornadus", 1),  # Tornadus Incarnate/Therian
        ("thundurus", 1),  # Thundurus Incarnate/Therian
        ("landorus", 1),  # Landorus Incarnate/Therian
        ("kyurem", 1),  # Kyurem (Normal/Black/White)
        ("keldeo", 1),  # Keldeo Ordinary/Resolute
        ("meloetta", 1),  # Meloetta Aria/Pirouette
        ("genesect", 1),  # Genesect (various drives)
    ]

    # Check if this Pokemon has formes
    for base_name, base_word_count in forme_pokemon:
        if pokemon_id.startswith(base_name):
            # Extract everything after the base name
            remainder = pokemon_id[len(base_name) :].lstrip("-")

            if not remainder:
                return (base_name, "")

            # Remove common suffixes from the forme
            forme = remainder
            for suffix in ["cloak", "forme", "form"]:
                if forme.endswith(f"-{suffix}"):
                    forme = forme[: -len(suffix) - 1]

            return (base_name, forme)

    # No forme detected
    return (pokemon_id, "")


def sanitize_filename(filename: str) -> str:
    """Sanitize a string to be safe for use as a filename.

    Converts the filename to snake_case format:
    - Removes invalid filesystem characters
    - Converts to lowercase
    - Replaces spaces and hyphens with underscores
    - Removes consecutive underscores

    Args:
        filename (str): The original filename string.
    Returns:
        str: The sanitized filename string in snake_case.

    Examples:
        >>> sanitize_filename("Abundant Shrine")
        'abundant_shrine'
        >>> sanitize_filename("Route 1")
        'route_1'
        >>> sanitize_filename("Castelia City - Battle Company")
        'castelia_city_battle_company'
    """
    # Remove or replace characters that are invalid in filenames
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "", filename)

    # Convert to lowercase
    sanitized = sanitized.lower()

    # Replace spaces, hyphens, and other separators with underscores
    sanitized = re.sub(r'[\s\-]+', '_', sanitized)

    # Remove any non-alphanumeric characters except underscores
    sanitized = re.sub(r'[^a-z0-9_]', '', sanitized)

    # Replace multiple consecutive underscores with a single underscore
    sanitized = re.sub(r'_+', '_', sanitized)

    # Strip leading/trailing underscores
    sanitized = sanitized.strip('_')

    return sanitized
