"""
Sprite utilities for generating sprite URLs and markdown image tags.

This module provides functions to generate sprite URLs for Pokemon, items,
moves, and other game assets.
"""

from typing import Optional


def get_pokemon_sprite_url(
    pokemon_id: int,
    variant: str = "front_default",
    use_showdown: bool = False
) -> str:
    """
    Get sprite URL for a Pokemon.

    Args:
        pokemon_id: National Pokedex number
        variant: Sprite variant (front_default, front_shiny, etc.)
        use_showdown: Use Pokemon Showdown sprites instead of PokeAPI

    Returns:
        str: URL to the sprite image
    """
    if use_showdown:
        # Pokemon Showdown sprites (animated, higher quality)
        return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/showdown/{pokemon_id}.gif"

    # PokeAPI sprites
    if variant == "front_default":
        return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon_id}.png"
    elif variant == "front_shiny":
        return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{pokemon_id}.png"
    elif variant.startswith("back_"):
        back_type = variant.replace("back_", "")
        if back_type == "default":
            return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/{pokemon_id}.png"
        else:
            return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/back/{back_type}/{pokemon_id}.png"
    else:
        # Default to front sprite
        return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon_id}.png"


def get_item_sprite_url(item_name: str) -> str:
    """
    Get sprite URL for an item.

    Args:
        item_name: Item name (slug format, e.g., 'master-ball')

    Returns:
        str: URL to the item sprite
    """
    return f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/{item_name}.png"


def pokemon_sprite_md(
    pokemon_id: int,
    pokemon_name: str,
    variant: str = "front_default",
    use_showdown: bool = False,
    size: Optional[int] = None
) -> str:
    """
    Generate markdown image tag for a Pokemon sprite.

    Args:
        pokemon_id: National Pokedex number
        pokemon_name: Pokemon name for alt text
        variant: Sprite variant
        use_showdown: Use Pokemon Showdown sprites
        size: Optional size in pixels (width)

    Returns:
        str: Markdown image tag
    """
    url = get_pokemon_sprite_url(pokemon_id, variant, use_showdown)

    if size:
        # Use HTML img tag for size control
        return f'<img src="{url}" alt="{pokemon_name}" width="{size}" />'
    else:
        return f"![{pokemon_name}]({url})"


def item_sprite_md(item_name: str, display_name: Optional[str] = None) -> str:
    """
    Generate markdown image tag for an item sprite.

    Args:
        item_name: Item name (slug format)
        display_name: Display name for alt text (defaults to item_name)

    Returns:
        str: Markdown image tag
    """
    url = get_item_sprite_url(item_name)
    alt = display_name or item_name
    return f"![{alt}]({url})"


def type_badge_md(type_name: str) -> str:
    """
    Generate a type badge using HTML/CSS.

    Args:
        type_name: Pokemon type name

    Returns:
        str: HTML badge for the type
    """
    # Type colors based on official Pokemon colors
    type_colors = {
        "normal": "#A8A878",
        "fire": "#F08030",
        "water": "#6890F0",
        "electric": "#F8D030",
        "grass": "#78C850",
        "ice": "#98D8D8",
        "fighting": "#C03028",
        "poison": "#A040A0",
        "ground": "#E0C068",
        "flying": "#A890F0",
        "psychic": "#F85888",
        "bug": "#A8B820",
        "rock": "#B8A038",
        "ghost": "#705898",
        "dragon": "#7038F8",
        "dark": "#705848",
        "steel": "#B8B8D0",
        "fairy": "#EE99AC",
    }

    color = type_colors.get(type_name.lower(), "#777777")
    return f'<span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85em;">{type_name.upper()}</span>'


def evolution_arrow_md() -> str:
    """
    Generate an evolution arrow for markdown.

    Returns:
        str: Evolution arrow symbol
    """
    return "→"


def mkdocs_admonition(
    title: str,
    content: str,
    admonition_type: str = "note"
) -> str:
    """
    Generate a MkDocs admonition block.

    Args:
        title: Admonition title
        content: Admonition content
        admonition_type: Type of admonition (note, tip, warning, danger, etc.)

    Returns:
        str: Formatted admonition block
    """
    lines = [f'!!! {admonition_type} "{title}"']
    for line in content.split('\n'):
        lines.append(f'    {line}')
    return '\n'.join(lines)
