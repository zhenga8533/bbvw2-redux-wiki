"""
Utility functions for generating markdown content.

This module provides helpers for creating consistent markdown elements
like Pokemon displays with sprites and links.
"""

from typing import Optional

from src.data.pokedb_loader import PokeDBLoader
from src.utils.config_util import get_config
from src.utils.text_util import name_to_id


def format_checkbox(checked: bool) -> str:
    """
    Generate a checkbox input element.

    Args:
        checked (bool): Whether the checkbox should be checked.

    Returns:
        str: HTML string for the checkbox input.
    """
    return f'<input type="checkbox" disabled{" checked" if checked else ""} />'


def format_ability(ability_name: str, is_linked: bool = True, relative_path: str = "../..") -> str:
    """
    Format an ability name with optional link to its page.

    Args:
        ability_name: The ability identifier (e.g., "overgrow" or "Overgrow")
        is_linked: Whether to create a link to the ability's page
        relative_path: Path to docs root (default: "../.." for pokemon pages, use ".." for changes pages)
    Returns:
        Formatted markdown string for the ability (link or plain text)
    """
    # Try to load ability data to check if it exists
    ability_data = PokeDBLoader.load_ability(ability_name)
    if not ability_data:
        # If data doesn't exist, return plain text with formatted name
        return ability_name.replace("-", " ").title()

    # Use the normalized name from the loaded data for the link
    normalized_name = ability_data.name

    # Format the display name
    display_name = ability_name.replace("-", " ").title()

    # Special cases for proper capitalization
    special_cases = {
        "rks system": "RKS System",
    }
    if ability_name.lower().replace("-", " ") in special_cases:
        display_name = special_cases[ability_name.lower().replace("-", " ")]

    if is_linked:
        # Create link to ability page using normalized name
        return f"[{display_name}]({relative_path}/pokedex/abilities/{normalized_name}.md)"
    else:
        return display_name


def format_pokemon(
    pokemon_name: str,
    has_sprite: bool = True,
    is_animated: bool = True,
    is_linked: bool = True,
) -> str:
    """
    Format a Pokemon name with its sprite stacked on top, optionally has_link to its Pokedex page.

    Creates markdown with the sprite image above the Pokemon name, centered in a table cell.
    Uses HTML for better control over layout.

    Args:
        pokemon_name: The display name of the Pokemon (e.g., "Pikachu")
        has_sprite: Whether to include the sprite image
        is_animated: Whether to use the animated sprite if available
        is_linked: Whether to link the name to its Pokedex entry

    Returns:
        Markdown string with sprite and name

    Example output:
        <div align="center"><img src="sprite.png" width="96"><br><a href="../pokedex/pikachu">Pikachu</a></div>
    """
    pokemon_html = '<div align="center">'

    config = get_config()
    pokedex_base_path = config.get("markdown", {}).get(
        "pokedex_base_path", "../pokedex"
    )

    # Try to load Pokemon data
    pokemon_data = PokeDBLoader.load_pokemon(pokemon_name)
    if not pokemon_data:
        return pokemon_name

    # Get the normalized ID for links
    pokemon_id = name_to_id(pokemon_name)

    # Add sprite image if requested
    if has_sprite:
        animated_url = pokemon_data.sprites.versions.black_white.animated.front_default
        sprite_url = pokemon_data.sprites.front_default

        if is_animated and animated_url:
            pokemon_html += f'<img src="{animated_url}" alt="{pokemon_name} (gif)">'
        elif sprite_url:
            pokemon_html += f'<img src="{sprite_url}" width="96" alt="{pokemon_name}">'
        # If no sprite available, don't add an img tag

    # Add line break if both sprite and name are present
    if has_sprite and is_linked:
        pokemon_html += "<br>"

    # Add linked or plain name
    if is_linked:
        pokemon_html += f'<a href="{pokedex_base_path}/{pokemon_id}">{pokemon_name}</a>'
    else:
        pokemon_html += pokemon_name

    pokemon_html += "</div>"

    return pokemon_html


def format_item(item_name: str, has_sprite: bool = True, is_linked: bool = True, relative_path: str = "../..") -> str:
    """
    Format an item with optional sprite and link to its page.

    Args:
        item_name: The item identifier (e.g., "potion" or "Potion")
        has_sprite: Whether to include the item's sprite image
        is_linked: Whether to create a link to the item's page
        relative_path: Path to docs root (default: "../.." for pokemon pages, use ".." for changes pages)

    Returns:
        HTML/markdown string with sprite and/or link
    """
    # Try to load item data to check if it exists
    item_data = PokeDBLoader.load_item(item_name)
    if not item_data:
        # If data doesn't exist, return plain text with formatted name
        return item_name.replace("-", " ").title()

    # Use the normalized name from the loaded data for the link
    normalized_name = item_data.name

    # Format the display name
    display_name = item_name.replace("-", " ").title()

    # Special cases for proper capitalization
    special_cases = {
        "tm": "TM",
        "hm": "HM",
        "hp": "HP",
        "pp": "PP",
        "exp": "Exp",
    }

    # Replace special abbreviations within the name
    for abbr, replacement in special_cases.items():
        display_name = display_name.replace(f" {abbr.title()} ", f" {replacement} ")
        display_name = display_name.replace(f" {abbr.title()}", f" {replacement}")
        if display_name.lower().startswith(abbr + " "):
            display_name = replacement + display_name[len(abbr):]

    # Build HTML output
    item_html = ""

    # Add sprite if requested
    if has_sprite and item_data.sprite:
        item_html += f'<img src="{item_data.sprite}" alt="{display_name}" style="vertical-align: middle; margin-right: 4px;">'

    # Add linked or plain name
    if is_linked:
        # Create link to item page using normalized name
        item_html += f'[{display_name}]({relative_path}/pokedex/items/{normalized_name}.md)'
    else:
        item_html += display_name

    return item_html


def format_move(move_name: str, is_linked: bool = True, relative_path: str = "../..") -> str:
    """
    Format a move name with optional link to its page.

    Args:
        move_name: The move identifier (e.g., "thunderbolt" or "Thunderbolt")
        is_linked: Whether to create a link to the move's page
        relative_path: Path to docs root (default: "../.." for pokemon pages, use ".." for changes pages)

    Returns:
        Formatted markdown string for the move (link or plain text)
    """
    # Try to load move data to check if it exists
    move_data = PokeDBLoader.load_move(move_name)
    if not move_data:
        # If data doesn't exist, return plain text with formatted name
        return move_name.replace("-", " ").title()

    # Use the normalized name from the loaded data for the link
    normalized_name = move_data.name

    # Format the display name
    display_name = move_name.replace("-", " ").title()

    # Special cases for proper capitalization
    special_cases = {
        "u turn": "U-turn",
        "v create": "V-create",
    }
    if move_name.lower().replace("-", " ") in special_cases:
        display_name = special_cases[move_name.lower().replace("-", " ")]

    if is_linked:
        # Create link to move page using normalized name
        return f"[{display_name}]({relative_path}/pokedex/moves/{normalized_name}.md)"
    else:
        return display_name
