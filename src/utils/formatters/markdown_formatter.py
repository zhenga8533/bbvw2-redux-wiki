"""
Utility functions for generating markdown content.

This module provides helpers for creating consistent markdown elements
like Pokemon displays with sprites and links.
"""

import re

from src.utils.core.config import PARSER_DEX_RELATIVE_PATH, POKEDB_SPRITE_VERSION
from src.utils.core.loader import PokeDBLoader
from src.utils.data.constants import TYPE_CATEGORY_COLORS, TYPE_COLORS
from src.utils.data.models import Ability, Item, Move, Pokemon
from src.utils.data.pokemon import get_pokemon_sprite
from src.utils.text.text_util import format_display_name, name_to_id


def format_checkbox(checked: bool) -> str:
    """Generate a checkbox input element.

    Args:
        checked (bool): Whether the checkbox should be checked.

    Returns:
        str: HTML string for the checkbox input element.

    Example:
        >>> format_checkbox(True)
        '<input type="checkbox" disabled checked />'
        >>> format_checkbox(False)
        '<input type="checkbox" disabled />'
    """
    return f'<input type="checkbox" disabled{" checked" if checked else ""} />'


def format_type_badge(type_name: str) -> str:
    """Format a Pokemon type name with a colored badge using HTML span element.

    Args:
        type_name (str): The type name to format (e.g., "fire", "water", "grass")

    Returns:
        str: HTML span element with styled badge

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


def format_category_badge(category_name: str) -> str:
    """Format a move category name with a styled badge using HTML span element.

    Args:
        category_name (str): The category name to format (e.g., "physical", "special", "status")

    Returns:
        str: HTML span element with styled badge

    Example:
        >>> format_category_badge("physical")
        '<span class="category-badge category-physical">Physical</span>'
    """
    formatted_name = category_name.title()
    category_color = TYPE_CATEGORY_COLORS.get(category_name.lower(), "#777777")

    # Apply only the dynamic background color as inline style
    background_style = f"background: linear-gradient(135deg, {category_color} 0%, {category_color}dd 100%);"

    return f'<span class="category-badge" style="{background_style}">{formatted_name}</span>'


def format_stat_bar(value: int, max_value: int) -> str:
    """Create a visual progress bar for a stat.

    Args:
        value (int): The stat value to represent
        max_value (int, optional): The maximum value for the stat. Defaults to MAX_STAT_VALUE.

    Returns:
        str: HTML representation of the progress bar.
    """
    percentage = min(100, (value / max_value) * 100)

    # Create a proper progress bar with background and filled portion
    bar_html = f'<div style="background: var(--md-default-fg-color--lightest); border-radius: 4px; overflow: hidden; height: 20px; width: 100%;">'
    bar_html += f'<div style="background: linear-gradient(90deg, #4CAF50 0%, #8BC34A 100%); height: 100%; width: {percentage}%;"></div>'
    bar_html += "</div>"
    return bar_html


def format_ability(
    ability: str | Ability,
    is_linked: bool = True,
    relative_path: str = PARSER_DEX_RELATIVE_PATH,
) -> str:
    """Format an ability name with optional link to its page.

    Args:
        ability (str | Ability): The ability identifier or object
        is_linked (bool, optional): Whether to create a link to the ability's page
        relative_path (str, optional): Path to docs root.

    Returns:
        Formatted markdown string for the ability (link or plain text)

    Example:
        >>> format_ability("overgrow", True, PARSER_DEX_RELATIVE_PATH)
        '[Overgrow](../pokedex/abilities/overgrow.md)'
        >>> format_ability("chlorophyll", False)
        'Chlorophyll'
    """
    # Try to load ability data to check if it exists
    if isinstance(ability, str):
        ability_data = PokeDBLoader.load_ability(ability)
        if not ability_data:
            # If data doesn't exist, return plain text with formatted name
            return ability.replace("-", " ").title()
    else:
        ability_data = ability

    # Use the normalized name from the loaded data for the link
    normalized_name = ability_data.name
    display_name = format_display_name(ability_data.name)

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
    relative_path: str = PARSER_DEX_RELATIVE_PATH,
) -> str:
    """Format a Pokemon with its sprite and name.

    Args:
        pokemon (str | Pokemon): The Pokemon name or object
        has_sprite (bool, optional): Whether to include the sprite image. Defaults to True.
        is_animated (bool, optional): Whether to use the animated sprite if available. Defaults to True.
        is_linked (bool, optional): Whether to link the name to its Pokedex entry. Defaults to True.
        is_named (bool, optional): Whether to show the Pokemon name as text (when not linked). Defaults to False.
        relative_path (str, optional): Path to docs root.

    Returns:
        str: Formatted markdown string for the Pokemon

    Example::
        >>> format_pokemon("bulbasaur", True, True, True, False, PARSER_DEX_RELATIVE_PATH)
        '![bulbasaur](sprite_url){ .sprite }<br>[Bulbasaur](../pokedex/pokemon/bulbasaur.md)'
        >>> format_pokemon("charmander", False, False, False, True)
        'Charmander'
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
        sprite_url = get_pokemon_sprite(pokemon_data)
        parts.append(f"![{pokemon_id}]({sprite_url}){{ .sprite }}")

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
    item: str | Item,
    has_sprite: bool = True,
    is_linked: bool = True,
    relative_path: str = PARSER_DEX_RELATIVE_PATH,
) -> str:
    """Format an item with optional sprite and link to its page.

    Args:
        item (str | Item): The item identifier or object
        has_sprite (bool, optional): Whether to include the item's sprite image. Defaults to True.
        is_linked (bool, optional): Whether to create a link to the item's page. Defaults to True.
        relative_path (str, optional): Path to docs root.

    Returns:
        str: Formatted markdown string for the item

    Example:
        >>> format_item("potion", True, True, PARSER_DEX_RELATIVE_PATH)
        '![Potion](sprite_url){ .item-sprite } [Potion](../pokedex/items/potion.md)'
        >>> format_item("rare-candy", False, False)
        'Rare Candy'
    """
    move = None
    extra = ""

    if isinstance(item, str):
        # Special case for TM/HM items
        item_name = item
        if item.lower().startswith(("tm", "hm")):
            item_name, move = item.split(" ", 1) if " " in item else (item, None)
            item_name = name_to_id(item_name)

        # Special case for quantity
        if match := re.match(r"^(.*?)( x\d+)$", item_name):
            item_name = match.group(1)
            extra = match.group(2)

        # Try to load item data to check if it exists
        item_data = PokeDBLoader.load_item(item_name)
        if not item_data:
            # If data doesn't exist, return plain text with formatted name
            return format_display_name(item)
    else:
        item_data = item

    # Use the normalized name from the loaded data for the link
    normalized_name = item_data.name
    display_name = format_display_name(item_data.name) + extra

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
    move: str | Move,
    is_linked: bool = True,
    relative_path: str = PARSER_DEX_RELATIVE_PATH,
) -> str:
    """Format a move name with optional link to its page.

    Args:
        move (str | Move): The move identifier or object
        is_linked (bool, optional): Whether to create a link to the move's page. Defaults to True.
        relative_path (str, optional): Path to docs root.

    Returns:
        str: Formatted markdown string for the move (link or plain text)

    Example:
        >>> format_move("tackle", True, PARSER_DEX_RELATIVE_PATH)
        '[Tackle](../pokedex/moves/tackle.md)'
        >>> format_move("ember", False)
        'Ember'
    """
    # Try to load move data to check if it exists
    if isinstance(move, str):
        move_data = PokeDBLoader.load_move(move)
        if not move_data:
            # If data doesn't exist, return plain text with formatted name
            return move.replace("-", " ").title()
    else:
        move_data = move

    # Use the normalized name from the loaded data for the link
    normalized_name = move_data.name
    display_name = format_display_name(move_data.name)

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
    """Format a list of Pokemon into a markdown grid.

    Args:
        pokemon (list[str | Pokemon]): A list of Pokemon names or objects to include in the grid.
        relative_path (str, optional): The relative path to the Pokemon documentation. Defaults to "../pokemon".
        extra_info (list[str] | None, optional): Additional information to include for each Pokemon. Defaults to None.

    Returns:
        str: The formatted markdown grid for the Pokemon.
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

        # Format display name and link
        display_name = format_display_name(pokemon_data.name)
        link = f"{relative_path}/{pokemon_data.name}.md"

        # Build card content using pure markdown
        card = ""

        # Sprite with link
        sprite_url = get_pokemon_sprite(pokemon_data)
        card += (
            f"-\t[![{display_name}]({sprite_url}){{: .pokemon-sprite-img }}]({link})"
        )

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
