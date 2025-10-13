"""
Utility functions for generating markdown content.

This module provides helpers for creating consistent markdown elements
like Pokemon displays with sprites and links.
"""

from typing import Optional

from src.models.pokedb import Pokemon
from src.data.pokedb_loader import PokeDBLoader
from src.utils.text_utils import name_to_id


def get_pokemon_sprite_url(pokemon: Pokemon) -> Optional[str]:
    """
    Get the default sprite URL for a Pokemon.

    Args:
        pokemon: Pokemon dataclass object

    Returns:
        URL to the Pokemon's front default sprite, or None if not available
    """
    if pokemon.sprites and pokemon.sprites.front_default:
        return pokemon.sprites.front_default
    return None


def format_pokemon_with_sprite(
    pokemon_name: str,
    sprite_url: Optional[str] = None,
    pokedex_link: bool = True,
    pokedex_base_path: str = "../pokedex",
) -> str:
    """
    Format a Pokemon name with its sprite stacked on top, optionally linked to its Pokedex page.

    Creates markdown with the sprite image above the Pokemon name, centered in a table cell.
    Uses HTML for better control over layout.

    Args:
        pokemon_name: The display name of the Pokemon (e.g., "Pikachu")
        sprite_url: URL to the Pokemon's sprite image. If None, attempts to load from PokeDB
        pokedex_link: Whether to link to the Pokemon's Pokedex page
        pokedex_base_path: Base path for Pokedex links (relative to current page)

    Returns:
        Markdown string with sprite and name

    Example output:
        <div align="center"><img src="sprite.png" width="96"><br><a href="../pokedex/pikachu">Pikachu</a></div>
    """
    pokemon_id = name_to_id(pokemon_name)

    # Try to load sprite URL if not provided
    if sprite_url is None:
        try:
            pokemon_data = PokeDBLoader.load_pokemon(pokemon_id)
            sprite_url = get_pokemon_sprite_url(pokemon_data)
        except FileNotFoundError:
            # If Pokemon not found, just use text
            pass

    # Build the HTML structure
    if sprite_url:
        sprite_img = f'<img src="{sprite_url}" width="96" alt="{pokemon_name}">'
    else:
        # Fallback to just text if no sprite
        sprite_img = ""

    # Add link to name if requested
    if pokedex_link:
        name_html = f'<a href="{pokedex_base_path}/{pokemon_id}">{pokemon_name}</a>'
    else:
        name_html = pokemon_name

    # Combine sprite and name
    if sprite_img:
        return f'<div align="center">{sprite_img}<br>{name_html}</div>'
    else:
        return f'<div align="center">{name_html}</div>'


def format_pokemon_pair_with_sprites(
    from_pokemon: str,
    to_pokemon: str,
    sprite_from: Optional[str] = None,
    sprite_to: Optional[str] = None,
    pokedex_base_path: str = "../pokedex",
) -> tuple[str, str]:
    """
    Format a pair of Pokemon (evolution from -> to) with sprites.

    Args:
        from_pokemon: Name of the Pokemon that evolves
        to_pokemon: Name of the evolution target
        sprite_from: URL to the first Pokemon's sprite
        sprite_to: URL to the second Pokemon's sprite
        pokedex_base_path: Base path for Pokedex links

    Returns:
        Tuple of (from_markdown, to_markdown)
    """
    from_md = format_pokemon_with_sprite(from_pokemon, sprite_from, pokedex_link=True, pokedex_base_path=pokedex_base_path)
    to_md = format_pokemon_with_sprite(to_pokemon, sprite_to, pokedex_link=True, pokedex_base_path=pokedex_base_path)
    return from_md, to_md


def escape_markdown(text: str) -> str:
    """
    Escape special markdown characters in text.

    Args:
        text: Text to escape

    Returns:
        Escaped text safe for markdown
    """
    special_chars = ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!', '|']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text
