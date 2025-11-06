"""
Utility functions for generating markdown content.

This module provides helpers for creating consistent markdown elements
like Pokemon displays with sprites and links.
"""

from src.data.pokedb_loader import PokeDBLoader
from src.models.pokedb import Pokemon
from src.utils.text.text_util import format_display_name, name_to_id
from src.utils.core.config import POKEDB_SPRITE_VERSION
from src.utils.data.constants import (
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

    The badge styling is defined in docs/stylesheets/extra.css (.type-badge class),
    with only the dynamic background gradient applied as inline style.

    Args:
        type_name: The type name to format (e.g., "fire", "water", "grass")

    Returns:
        HTML span element with styled badge

    Example:
        >>> format_type_badge("fire")
        '<span class="type-badge" style="background: ...">Fire</span>'
    """
    formatted_name = type_name.title()
    type_color = TYPE_COLORS.get(type_name.lower(), "#777777")

    # Apply only the dynamic background gradient as inline style
    background_style = (
        f"background: linear-gradient(135deg, {type_color} 0%, {type_color}dd 100%);"
    )

    return (
        f'<span class="type-badge" style="{background_style}">{formatted_name}</span>'
    )


def format_ability(
    ability_name: str,
    is_linked: bool = True,
    relative_path: str = "../..",
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
    pokemon: str | Pokemon,
    has_sprite: bool = True,
    is_animated: bool = True,
    is_linked: bool = True,
    is_named: bool = False,
    relative_path: str = "../..",
) -> str:
    """
    Format a Pokemon name with its sprite stacked on top, optionally has_link to its Pokedex page.

    Creates markdown with the sprite image above the Pokemon name, centered using attribute lists.

    Args:
        pokemon: The Pokemon name (str) or Pokemon object
        has_sprite: Whether to include the sprite image
        is_animated: Whether to use the animated sprite if available
        is_linked: Whether to link the name to its Pokedex entry
        is_named: Whether to show the Pokemon name as text (when not linked)
        relative_path: Path to docs root (default: "../.." for pages in subdirectories when use_directory_urls is true)

    Returns:
        Markdown string with sprite and name
    """
    # Try to load Pokemon data
    if isinstance(pokemon, str):
        pokemon_data = PokeDBLoader.load_pokemon(pokemon)
        if not pokemon_data:
            return pokemon

        # Get the normalized ID for links
        pokemon_id = pokemon_data.name
    else:
        pokemon_data = pokemon
        pokemon_id = pokemon_data.name

    display_name = format_display_name(pokemon_id)
    parts = []

    # Add sprite image if requested
    if has_sprite:
        # Safely access sprite version
        sprite_version = getattr(
            pokemon_data.sprites.versions, POKEDB_SPRITE_VERSION, None
        )
        animated_url = (
            sprite_version.animated.front_default
            if sprite_version and sprite_version.animated
            else None
        )
        sprite_url = pokemon_data.sprites.front_default

        if is_animated and animated_url:
            parts.append(f"![{pokemon_id} (gif)]({animated_url}){{ .sprite }}")
        elif sprite_url:
            parts.append(f"![{pokemon_id}]({sprite_url}){{ .sprite }}")
        # If no sprite available, don't add an image

    # Add linked or plain name
    if is_linked:
        parts.append(
            f"[{display_name}]({relative_path}/pokedex/pokemon/{pokemon_id}.md)"
        )
    elif is_named:
        parts.append(display_name)

    # Return combined content
    content = "<br>".join(parts)
    return content


def format_item(
    item_name: str,
    has_sprite: bool = True,
    is_linked: bool = True,
    relative_path: str = "../..",
) -> str:
    """
    Format an item with optional sprite and link to its page.

    Args:
        item_name: The item identifier (e.g., "potion" or "Potion")
        has_sprite: Whether to include the item's sprite image
        is_linked: Whether to create a link to the item's page
        relative_path: Path to docs root (default: "../.." for pokemon pages, use ".." for changes pages)

    Returns:
        Markdown string with sprite and/or link
    """

    # Special case for TM/HM items
    move = None
    if item_name.lower().startswith(("tm", "hm")):
        item_name, move = (
            item_name.split(" ", 1) if " " in item_name else (item_name, None)
        )
        item_name = name_to_id(item_name)

    # Try to load item data to check if it exists
    item_data = PokeDBLoader.load_item(item_name)
    if not item_data:
        # If data doesn't exist, return plain text with formatted name
        return format_display_name(item_name)

    # Use the normalized name from the loaded data for the link
    normalized_name = item_data.name
    display_name = format_display_name(item_name)

    parts = []

    # Add sprite if requested
    if has_sprite and item_data.sprite:
        # Use markdown image with attribute list
        parts.append(f"![{display_name}]({item_data.sprite}){{ .item-sprite }}")

    # Add linked or plain name
    if is_linked:
        # Create link to item page using normalized name
        link_path = f"{relative_path}/pokedex/items/{normalized_name}.md"
        # Use markdown syntax
        parts.append(f"[{display_name}]({link_path})")
    else:
        parts.append(display_name)

    md = " ".join(parts)

    # Add move info for TM/HM items
    if move:
        md += f", {format_move(move, is_linked, relative_path)}"

    return md


def format_move(
    move_name: str,
    is_linked: bool = True,
    relative_path: str = "../..",
) -> str:
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

    if is_linked:
        # Create link to move page using normalized name
        link_path = f"{relative_path}/pokedex/moves/{normalized_name}.md"
        # Use markdown syntax
        return f"[{display_name}]({link_path})"
    else:
        return display_name


def format_pokemon_card_grid(
    pokemon: list[str | Pokemon],
    relative_path: str = "../pokemon",
    extra_info: list[str] | None = None,
) -> str:
    """
    Format one or more Pokemon as markdown content for MkDocs Material grid cards.

    Args:
        pokemon: List of Pokemon names (str) or Pokemon objects
        relative_path: Relative path to the pokemon directory

    Returns:
        Concatenated markdown string for card content (each item suitable to be used inside a list item)
    """
    cards = []

    for idx, p in enumerate(pokemon):
        # Load Pokemon data if string is provided
        if isinstance(p, str):
            pokemon_data = PokeDBLoader.load_pokemon(p.lower().replace(" ", "-"))
            if not pokemon_data:
                # Fallback if Pokemon data not found
                cards.append(p)
                continue
        else:
            pokemon_data = p

        # Get dex number
        dex_num = pokemon_data.pokedex_numbers.get("national", "???")

        # Get sprite URL
        sprite_url = None
        sprite_version = getattr(
            pokemon_data.sprites.versions, POKEDB_SPRITE_VERSION, None
        )
        animated_sprite = (
            sprite_version.animated.front_default
            if sprite_version and sprite_version.animated
            else None
        )
        default_sprite = pokemon_data.sprites.front_default

        form_category = next(
            (f.category for f in pokemon_data.forms if f.name == pokemon_data.name),
            "default",
        )
        sprite_url = animated_sprite if form_category != "cosmetic" else default_sprite

        if sprite_url is None:
            sprite_url = default_sprite

        # Format display name and link
        display_name = format_display_name(pokemon_data.name)
        link = f"{relative_path}/{pokemon_data.name}.md"

        # Build card content using pure markdown
        card = ""

        # Sprite with link
        if sprite_url:
            card += f"-\t[![{display_name}]({sprite_url}){{: .pokemon-sprite-img }}]({link})"
        else:
            card += f"\t[{display_name}]({link})"

        card += "\n\n\t***\n\n"

        # Dex number and name
        card += f"\t**#{dex_num:03d} [{display_name}]({link})**"

        # Extra info lines
        if extra_info:
            info = extra_info[idx] if idx < len(extra_info) else ""
            if info:
                card += f"\n\n\t{info}"

        cards.append(card)

    # Combine all cards into a grid container
    markdown = '<div class="grid cards" markdown>\n\n'
    markdown += "\n\n".join(cards)
    markdown += "\n\n</div>"

    return markdown
