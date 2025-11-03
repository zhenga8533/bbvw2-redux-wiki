"""
Utility functions for generating consistent markdown tables.

This module provides helpers for creating standardized tables that follow
the wiki's formatting guidelines as defined in TABLE_STANDARDS.md.
"""

from typing import List, Optional, Literal

# Type aliases for clarity
Alignment = Literal["left", "center", "right"]


def create_table_header(
    columns: List[str], alignments: Optional[List[Alignment]] = None
) -> str:
    """
    Create a markdown table header with proper alignment markers.

    Args:
        columns: List of column names
        alignments: List of alignment values ('left', 'center', 'right'). If None, all columns default to 'left'.

    Returns:
        Markdown string with table header and separator line

    Example:
        >>> create_table_header(['Name', 'Type', 'Power'], ['left', 'left', 'center'])
        '| Name | Type | Power |\n|------|------|:-----:|'
    """
    if alignments is None:
        alignments = ["left"] * len(columns)  # type: ignore
    elif len(alignments) != len(columns):
        raise ValueError(
            f"Number of alignments ({len(alignments)}) must match number of columns ({len(columns)})"
        )

    # Create header row
    header = "| " + " | ".join(columns) + " |"

    # Create separator row with alignment markers
    separators = []
    for alignment in alignments or []:
        if alignment == "center":
            separators.append(":-----:")
        elif alignment == "right":
            separators.append("-----:")
        else:  # left (default)
            separators.append("------")

    separator = "| " + " | ".join(separators) + " |"

    table = f"{header}\n{separator}"
    return table


def create_table_row(cells: List[str]) -> str:
    """
    Create a markdown table row.

    Args:
        cells: List of cell contents

    Returns:
        Markdown string for the table row

    Example:
        >>> create_table_row(['Bulbasaur', 'Grass', '45'])
        '| Bulbasaur | Grass | 45 |'
    """
    return "| " + " | ".join(str(cell) for cell in cells) + " |"


def create_table(
    headers: List[str],
    rows: List[List[str]],
    alignments: Optional[List[Alignment]] = None,
) -> str:
    """
    Create a complete markdown table.

    Args:
        headers: List of column headers
        rows: List of rows, where each row is a list of cell contents
        alignments: List of alignment values for each column

    Returns:
        Complete markdown table as a string

    Example:
        >>> headers = ['Name', 'Type', 'Power']
        >>> rows = [['Tackle', 'Normal', '40'], ['Ember', 'Fire', '40']]
        >>> create_table(headers, rows, ['left', 'left', 'center'])
    """
    table_lines = [create_table_header(headers, alignments)]

    for row in rows:
        table_lines.append(create_table_row(row))

    return "\n".join(table_lines) + "\n"


def format_null_value() -> str:
    """
    Return the standard null value representation for tables.

    Returns:
        Em dash character (—) for null/missing values
    """
    return "—"


# Predefined table configurations following TABLE_STANDARDS.md


def create_pokemon_index_table(rows: List[List[str]]) -> str:
    """
    Create a Pokemon index table with standardized formatting.

    Columns: Dex #, Sprite, Name, Type(s), Abilities

    Args:
        rows: List of rows with [dex_num, sprite, name, types, abilities]

    Returns:
        Formatted markdown table
    """
    headers = ["Dex #", "Sprite", "Name", "Type(s)", "Abilities"]
    alignments: List[Alignment] = ["center", "center", "left", "left", "left"]
    return create_table(headers, rows, alignments)


def create_move_index_table(rows: List[List[str]]) -> str:
    """
    Create a move index table with standardized formatting.

    Columns: Move, Type, Category, Power, Acc, PP

    Args:
        rows: List of rows with [move, type, category, power, acc, pp]

    Returns:
        Formatted markdown table
    """
    headers = ["Move", "Type", "Category", "Power", "Acc", "PP"]
    alignments: List[Alignment] = ["left", "left", "left", "left", "left", "left"]
    return create_table(headers, rows, alignments)


def create_item_index_table(rows: List[List[str]]) -> str:
    """
    Create an item index table with standardized formatting.

    Columns: Sprite, Item, Category, Effect

    Args:
        rows: List of rows with [sprite, item, category, effect]

    Returns:
        Formatted markdown table
    """
    headers = ["Sprite", "Item", "Category", "Effect"]
    alignments: List[Alignment] = ["center", "left", "left", "left"]
    return create_table(headers, rows, alignments)


def create_ability_index_table(rows: List[List[str]]) -> str:
    """
    Create an ability index table with standardized formatting.

    Columns: Ability, Effect

    Args:
        rows: List of rows with [ability, effect]

    Returns:
        Formatted markdown table
    """
    headers = ["Ability", "Effect"]
    alignments: List[Alignment] = ["left", "left"]
    return create_table(headers, rows, alignments)


def create_held_items_table(rows: List[List[str]]) -> str:
    """
    Create a wild held items table with standardized formatting.

    Columns: Item, Black 2, White 2

    Args:
        rows: List of rows with [item, black2_percent, white2_percent]

    Returns:
        Formatted markdown table
    """
    headers = ["Item", "Black 2", "White 2"]
    alignments: List[Alignment] = ["left", "center", "center"]
    return create_table(headers, rows, alignments)


def create_move_learnset_table(
    rows: List[List[str]], include_level: bool = True
) -> str:
    """
    Create a move learnset table with standardized formatting.

    Columns: Level, Move, Type, Category, Power, Acc, PP (Level is optional)

    Args:
        rows: List of rows with [level, move, type, category, power, acc, pp] or
              [move, type, category, power, acc, pp] if include_level is False
        include_level: Whether to include the Level column

    Returns:
        Formatted markdown table
    """
    if include_level:
        headers = ["Level", "Move", "Type", "Category", "Power", "Acc", "PP"]
        alignments: List[Alignment] = [
            "left",
            "left",
            "left",
            "left",
            "left",
            "left",
            "left",
        ]
    else:
        headers = ["Move", "Type", "Category", "Power", "Acc", "PP"]
        alignments = ["left", "left", "left", "left", "left", "left"]

    return create_table(headers, rows, alignments)


def create_pokemon_with_item_table(rows: List[List[str]]) -> str:
    """
    Create a table showing which Pokemon can hold a specific item.

    Columns: Pokemon, Black 2, White 2

    Args:
        rows: List of rows with [pokemon_name, black2_percent, white2_percent]

    Returns:
        Formatted markdown table
    """
    headers = ["Pokémon", "Black 2", "White 2"]
    alignments: List[Alignment] = ["left", "center", "center"]
    return create_table(headers, rows, alignments)


def create_evolution_changes_table(rows: List[List[str]]) -> str:
    """
    Create an evolution changes table with standardized formatting.

    Columns: Dex #, Pokemon, Evolution, New Method

    Args:
        rows: List of rows with [dex_num, pokemon, evolution, new_method]

    Returns:
        Formatted markdown table
    """
    headers = ["Dex #", "Pokémon", "Evolution", "New Method"]
    alignments: List[Alignment] = ["center", "center", "center", "left"]
    return create_table(headers, rows, alignments)
