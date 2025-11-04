"""
Utility functions for generating markdown content.

This module provides helpers for creating consistent markdown elements
like Pokemon displays with sprites and links.
"""

from typing import Optional, Union

from src.data.pokedb_loader import PokeDBLoader
from src.models.pokedb import Pokemon
from src.utils.text.text_util import format_display_name, name_to_id
from src.utils.pokemon.constants import (
    ITEM_NAME_SPECIAL_CASES,
    DEFAULT_RELATIVE_PATH,
    TYPE_COLORS,
)


def format_checkbox(checked: bool) -> str:
    """
    Generate a checkbox input element.

    Args:
        checked (bool): Whether the checkbox should be checked.

    Returns:
        str: HTML string for the checkbox input.
    """
    return f'<input type="checkbox" disabled{" checked" if checked else ""} />'


def format_type_badge(type_name: str) -> str:
    """
    Format a Pokemon type name with a colored badge using HTML span element.

    This function consolidates the type badge formatting logic previously
    duplicated in pokemon_generator and move_generator (_format_type methods).

    Args:
        type_name: The type name to format (e.g., "fire", "water", "grass")

    Returns:
        HTML span element with styled badge

    Example:
        >>> format_type_badge("fire")
        '<span style="...">Fire</span>'
    """
    formatted_name = type_name.title()
    type_color = TYPE_COLORS.get(type_name.lower(), "#777777")

    # Create a styled badge with gradient background, padding, and rounded corners
    badge_style = (
        f"background: linear-gradient(135deg, {type_color} 0%, {type_color}dd 100%);"
        f"color: white;"
        f"padding: 0.25rem 0.75rem;"
        f"border-radius: 12px;"
        f"font-size: 0.75rem;"
        f"font-weight: 600;"
        f"text-transform: uppercase;"
        f"display: inline-block;"
        f"text-align: center;"
        f"text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);"
        f"box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);"
    )

    return f'<span style="{badge_style}">{formatted_name}</span>'


def format_ability(
    ability_name: str,
    is_linked: bool = True,
    relative_path: str = DEFAULT_RELATIVE_PATH,
) -> str:
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

    if is_linked:
        # Create link to ability page using normalized name
        return (
            f"[{display_name}]({relative_path}/pokedex/abilities/{normalized_name}.md)"
        )
    else:
        return display_name


def format_pokemon(
    pokemon_name: str,
    has_sprite: bool = True,
    is_animated: bool = True,
    is_linked: bool = True,
    relative_path: str = DEFAULT_RELATIVE_PATH,
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
        relative_path: Path to docs root (default: "../.." for pages in subdirectories when use_directory_urls is true)

    Returns:
        Markdown string with sprite and name

    Example output:
        <div align="center"><img src="sprite.png" width="96"><br><a href="../../pokedex/pokemon/pikachu/">Pikachu</a></div>
    """
    pokemon_html = '<div align="center">'

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

    # Add linked or plain name (HTML link - no .md extension)
    if is_linked:
        pokemon_html += f'<a href="{relative_path}/pokedex/pokemon/{pokemon_id}/">{pokemon_name}</a>'
    else:
        pokemon_html += pokemon_name

    pokemon_html += "</div>"

    return pokemon_html


def format_item(
    item_name: str,
    has_sprite: bool = True,
    is_linked: bool = True,
    relative_path: str = DEFAULT_RELATIVE_PATH,
    html_mode: bool = False,
) -> str:
    """
    Format an item with optional sprite and link to its page.

    Args:
        item_name: The item identifier (e.g., "potion" or "Potion")
        has_sprite: Whether to include the item's sprite image
        is_linked: Whether to create a link to the item's page
        relative_path: Path to docs root (default: "../.." for pokemon pages, use ".." for changes pages)
        html_mode: If True, output HTML <a> tags instead of markdown links (for use inside HTML tables)

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

    # Replace special abbreviations within the name (using imported constants)
    display_name = format_display_name(display_name)

    # Build HTML output
    item_html = "<span>"

    # Add sprite if requested
    if has_sprite and item_data.sprite:
        item_html += f'<img src="{item_data.sprite}" alt="{display_name}" style="vertical-align: middle;">'

    # Add linked or plain name
    if is_linked:
        # Create link to item page using normalized name
        link_path = f"{relative_path}/pokedex/items/{normalized_name}.md"
        if html_mode:
            # Use HTML <a> tag for HTML tables
            item_html += f'<a href="{link_path}">{display_name}</a>'
        else:
            # Use markdown syntax for regular markdown content
            item_html += f"[{display_name}]({link_path})"
    else:
        item_html += display_name

    item_html += "</span>"
    return item_html


def format_move(
    move_name: str,
    is_linked: bool = True,
    relative_path: str = DEFAULT_RELATIVE_PATH,
    html_mode: bool = False,
) -> str:
    """
    Format a move name with optional link to its page.

    Args:
        move_name: The move identifier (e.g., "thunderbolt" or "Thunderbolt")
        is_linked: Whether to create a link to the move's page
        relative_path: Path to docs root (default: "../.." for pokemon pages, use ".." for changes pages)
        html_mode: If True, output HTML <a> tags instead of markdown links (for use inside HTML tables)

    Returns:
        Formatted markdown/HTML string for the move (link or plain text)
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

    if is_linked:
        # Create link to move page using normalized name
        link_path = f"{relative_path}/pokedex/moves/{normalized_name}.md"
        if html_mode:
            # Use HTML <a> tag for HTML tables
            return f'<a href="{link_path}">{display_name}</a>'
        else:
            # Use markdown syntax for regular markdown content
            return f"[{display_name}]({link_path})"
    else:
        return display_name


def format_pokemon_card(
    pokemon: Union[str, Pokemon],
    relative_path: str = "../pokemon",
) -> str:
    """
    Format a Pokemon as markdown content for MkDocs Material grid cards.

    Args:
        pokemon: Pokemon name (str) or Pokemon object
        relative_path: Relative path to the pokemon directory
            - From pokedex/abilities/ or pokedex/items/: "../pokemon"
            - From docs/ (parsers): "../pokedex/pokemon"

    Returns:
        Markdown string for card content (to be used inside a list item)

    Example usage:
        # In your generator/parser:
        md += '<div class="grid cards" markdown>\n\n'
        md += "-   "
        md += format_pokemon_card("pikachu")
        md += "\n\n"
        md += "</div>\n\n"

    Example output:
        [![Pikachu](sprite.gif)](../pokemon/pikachu.md)

        ***

        **#025 [Pikachu](../pokemon/pikachu.md)**
    """
    # Load Pokemon data if string is provided
    if isinstance(pokemon, str):
        pokemon_data = PokeDBLoader.load_pokemon(pokemon.lower().replace(" ", "-"))
        if not pokemon_data:
            # Fallback if Pokemon data not found
            return pokemon
    else:
        pokemon_data = pokemon

    # Get dex number
    dex_num = pokemon_data.pokedex_numbers.get("national", "???")

    # Get sprite URL (prefer animated)
    sprite_url = None
    if hasattr(pokemon_data.sprites, "versions") and pokemon_data.sprites.versions:
        bw = pokemon_data.sprites.versions.black_white
        if bw.animated and bw.animated.front_default:
            sprite_url = bw.animated.front_default

    # Fallback to static sprite
    if not sprite_url:
        sprite_url = pokemon_data.sprites.front_default

    # Format name for display
    display_name = format_display_name(pokemon_data.name)

    # Create link (relative_path should include the full path to pokemon dir)
    link = f"{relative_path}/{pokemon_data.name}.md"

    # Build card content using pure markdown (centering handled by CSS)
    card = ""

    # Sprite with link
    if sprite_url:
        card += f"\t[![{display_name}]({sprite_url})]({link})"
    else:
        card += f"\t[{display_name}]({link})"

    card += "\n\n\t***\n\n"

    # Dex number and name
    card += f"\t**#{dex_num:03d} [{display_name}]({link})**"

    return card
