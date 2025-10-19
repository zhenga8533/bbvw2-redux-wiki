"""
Utility functions for generating markdown content.

This module provides helpers for creating consistent markdown elements
like Pokemon displays with sprites and links.
"""

from src.data.pokedb_loader import PokeDBLoader
from src.utils.config_util import get_config
from src.utils.text_util import name_to_id


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

    pokemon_id = name_to_id(pokemon_name)
    try:
        pokemon_data = PokeDBLoader.load_pokemon(pokemon_id)
    except FileNotFoundError:
        return pokemon_name

    # Add sprite image if requested
    if has_sprite:
        animated_url = pokemon_data.sprites.versions.black_white.animated.front_default
        sprite_url = pokemon_data.sprites.front_default

        if is_animated and animated_url:
            pokemon_html += f'<img src="{animated_url}" alt="{pokemon_name} (gif)">'
        else:
            pokemon_html += f'<img src="{sprite_url}" width="96" alt="{pokemon_name}">'

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


def format_item(
    item_name: str,
    has_sprite: bool = True,
    has_name: bool = True,
    has_flavor_text: bool = True,
):
    """
    Format an item with optional sprite, name, and flavor text.

    Args:
        item_name: The display name of the item (e.g., "Potion")
        has_sprite: Whether to include the item's sprite image
        has_name: Whether to include the item's name text
        has_flavor_text: Whether to include the item's flavor text below the name

    Returns:
        Markdown string with item sprite, name, and optional flavor text

    Example output:
        <div align="center"><img src="sprite.png"><br><strong>Potion</strong><br>Restores 20 HP.</div>
    """
    item_html = '<div align="center">'

    # Try to load item URL
    try:
        item_data = PokeDBLoader.load_item(name_to_id(item_name))
    except FileNotFoundError:
        return item_name

    if has_sprite:
        item_sprite_url = item_data.sprite
        item_html += f'<img src="{item_sprite_url}"><br>'

    if has_name:
        # Show flavor text as tooltip on hover
        if has_flavor_text and item_data.flavor_text:
            item_html += f'<strong title="{item_data.flavor_text}">{item_name}</strong>'
        else:
            item_html += f"<strong>{item_name}</strong>"

    item_html += "</div>"
    return item_html
