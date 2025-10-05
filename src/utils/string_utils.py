"""
String parsing utilities for Pokemon/Move/Item/Ability names and text extraction.

This module provides functions to:
- Normalize display names to PokeAPI-compatible slugs
- Extract game data (levels, items, moves) from text descriptions
- Parse evolution requirements from natural language
"""

import re
from typing import Optional


def normalize_name(name: str) -> str:
    """
    Convert a display name to a normalized slug format.

    Args:
        name: Display name (e.g., "King's Rock", "Mr. Mime")

    Returns:
        str: Normalized slug (e.g., "kings-rock", "mr-mime")

    Examples:
        >>> normalize_name("King's Rock")
        'kings-rock'
        >>> normalize_name("Mr. Mime")
        'mr-mime'
        >>> normalize_name("Farfetch'd")
        'farfetchd'
    """
    # Convert to lowercase
    slug = name.lower()

    # Remove possessive apostrophes (King's -> kings)
    slug = slug.replace("'s ", "s-").replace("'s", "s")

    # Remove other apostrophes (Farfetch'd -> farfetchd)
    slug = slug.replace("'", "")

    # Handle special abbreviations
    slug = slug.replace("jr.", "jr")
    slug = slug.replace("mr.", "mr")
    slug = slug.replace("mime jr", "mime-jr")

    # Replace spaces with hyphens
    slug = slug.replace(" ", "-")

    # Remove any duplicate hyphens
    slug = re.sub(r'-+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    return slug


def parse_item_name(name: str) -> str:
    """
    Parse an item name into its PokeAPI slug.

    Args:
        name: Item name in any format

    Returns:
        str: PokeAPI-compatible item slug

    Examples:
        >>> parse_item_name("King's Rock")
        'kings-rock'
        >>> parse_item_name("Link Cable")
        'link-cable'
        >>> parse_item_name("Deep Sea Tooth")
        'deep-sea-tooth'
    """
    return normalize_name(name)


def parse_move_name(name: str) -> str:
    """
    Parse a move name into its PokeAPI slug.

    Args:
        name: Move name in any format

    Returns:
        str: PokeAPI-compatible move slug

    Examples:
        >>> parse_move_name("Aura Sphere")
        'aura-sphere'
        >>> parse_move_name("Dragon Claw")
        'dragon-claw'
    """
    return normalize_name(name)


def parse_ability_name(name: str) -> str:
    """
    Parse an ability name into its PokeAPI slug.

    Args:
        name: Ability name in any format

    Returns:
        str: PokeAPI-compatible ability slug

    Examples:
        >>> parse_ability_name("Lightning Rod")
        'lightning-rod'
        >>> parse_ability_name("Serene Grace")
        'serene-grace'
    """
    return normalize_name(name)


def parse_pokemon_name(name: str) -> str:
    """
    Parse a Pokemon name into its PokeAPI slug.

    Args:
        name: Pokemon name in any format

    Returns:
        str: PokeAPI-compatible pokemon slug

    Examples:
        >>> parse_pokemon_name("Mr. Mime")
        'mr-mime'
        >>> parse_pokemon_name("Farfetch'd")
        'farfetchd'
        >>> parse_pokemon_name("Mime Jr.")
        'mime-jr'
    """
    slug = normalize_name(name)

    # Special cases for Pokemon with unique formatting
    special_cases = {
        'nidoran-f': 'nidoran-f',
        'nidoran-m': 'nidoran-m',
        'ho-oh': 'ho-oh',
        'porygon-z': 'porygon-z',
        'porygon2': 'porygon2',
    }

    if slug in special_cases:
        return special_cases[slug]

    return slug


def parse_type_name(name: str) -> str:
    """
    Parse a type name into its PokeAPI slug.

    Args:
        name: Type name in any format

    Returns:
        str: PokeAPI-compatible type slug

    Examples:
        >>> parse_type_name("Fighting")
        'fighting'
        >>> parse_type_name("Fairy")
        'fairy'
    """
    return name.lower().strip()


def extract_number(text: str, pattern: str) -> Optional[int]:
    r"""
    Extract a number from text using a pattern.

    Args:
        text: Text to search
        pattern: Regex pattern with one capture group for the number

    Returns:
        int: Extracted number, or None if not found

    Examples:
        >>> extract_number("at Level 25", r'level\s+(\d+)')
        25
        >>> extract_number("220+ friendship", r'(\d+)\+?\s*friendship')
        220
    """
    match = re.search(pattern, text.lower())
    if match:
        return int(match.group(1))
    return None


def extract_with_pattern(text: str, pattern: str, parser_func=None) -> Optional[str]:
    r"""
    Extract and parse text using a regex pattern.

    Args:
        text: Text to search
        pattern: Regex pattern with one capture group
        parser_func: Optional function to parse the extracted text (e.g., parse_item_name)

    Returns:
        str: Extracted and parsed text, or None if not found

    Examples:
        >>> extract_with_pattern("via the use of a Link Cable",
        ...                      r'via the use of (?:a |an )?(.+?)(?:\.|$)',
        ...                      parse_item_name)
        'link-cable'
    """
    match = re.search(pattern, text.lower())
    if match:
        extracted = match.group(1).strip()
        if parser_func:
            return parser_func(extracted)
        return extracted
    return None
