"""
Utility functions for generating markdown content.

This module provides helpers for creating consistent markdown elements
like Pokemon displays with sprites and links.
"""

from typing import Optional

from src.models.pokedb import Pokemon
from src.data.pokedb_loader import PokeDBLoader
from src.utils.config_loader import get_config
from src.utils.text_utils import name_to_id
from src.utils.constants import POKEMON_SPRITE_WIDTH


def get_pokemon_sprite_url(pokemon: Pokemon, animated: bool = False) -> Optional[str]:
    """
    Get the default sprite URL for a Pokemon.

    Args:
        pokemon: Pokemon dataclass object
        animated: Whether to get the animated sprite URL

    Returns:
        URL to the Pokemon's front default sprite, or None if not available
    """
    if animated:
        animated_sprite = pokemon.sprites.versions.black_white.animated.front_default
        if animated_sprite:
            return animated_sprite

    return pokemon.sprites.front_default


def format_pokemon_with_sprite(
    pokemon_name: str,
    linked: bool = True,
    animated: bool = True,
) -> str:
    """
    Format a Pokemon name with its sprite stacked on top, optionally linked to its Pokedex page.

    Creates markdown with the sprite image above the Pokemon name, centered in a table cell.
    Uses HTML for better control over layout.

    Args:
        pokemon_name: The display name of the Pokemon (e.g., "Pikachu")
        linked: Whether to link the name to its Pokedex entry
        animated: Whether to use the animated sprite if available

    Returns:
        Markdown string with sprite and name

    Example output:
        <div align="center"><img src="sprite.png" width="96"><br><a href="../pokedex/pikachu">Pikachu</a></div>
    """
    # Use config for default paths
    config = get_config()
    pokedex_base_path = config.get("markdown", {}).get(
        "pokedex_base_path", "../pokedex"
    )

    pokemon_id = name_to_id(pokemon_name)

    # Try to load sprite URL
    try:
        pokemon_data = PokeDBLoader.load_pokemon(pokemon_id)
        sprite_url = get_pokemon_sprite_url(pokemon_data, animated=animated)
    except FileNotFoundError:
        # If Pokemon not found, just use text
        sprite_url = None

    # Build the HTML structure
    if sprite_url:
        sprite_img = (
            f'<img src="{sprite_url}" width="{POKEMON_SPRITE_WIDTH}" alt="{pokemon_name}">'
            if not animated
            else f'<img src="{sprite_url}"  alt="{pokemon_name} (animated)">'
        )
    else:
        # Fallback to just text if no sprite
        sprite_img = ""

    # Add link to name if requested
    if sprite_img:
        name_html = f'<a href="{pokedex_base_path}/{pokemon_id}">{pokemon_name}</a>'
    else:
        name_html = pokemon_name

    # Combine sprite and name
    if sprite_img and linked:
        return f'<div align="center">{sprite_img}<br>{name_html}</div>'
    else:
        return f'<div align="center">{name_html}</div>'
