"""
Utility functions for generating consistent markdown tables.

This module provides helpers for creating standardized tables that follow
the wiki's formatting guidelines as defined in TABLE_STANDARDS.md.
"""

from typing import Optional

from src.utils.core.config import POKEDB_GAME_VERSIONS
from src.utils.text.text_util import format_display_name


def create_table_header(
    columns: list[str], alignments: Optional[list[str]] = None
) -> str:
    """
    Create a markdown table header with proper alignment markers.

    Args:
        columns: list of column names
        alignments: list of alignment values ('left', 'center', 'right'). If None, all columns default to 'left'.

    Returns:
        Markdown string with table header and separator line

    Example:
        >>> create_table_header(['Name', 'Type', 'Power'], ['left', 'left', 'center'])
        '| Name | Type | Power |\n|------|------|:-----:|'
    """
    if alignments is None:
        alignments = ["left"] * len(columns)
    elif len(alignments) != len(columns):
        raise ValueError(
            f"Number of alignments ({len(alignments)}) must match number of columns ({len(columns)})"
        )

    # Create header row
    header = "| " + " | ".join(columns) + " |"

    # Create separator row with alignment markers
    separators = []
    for column, alignment in zip(columns, alignments):
        width = len(column)
        if alignment == "center":
            sep = ":" + "-" * width + ":"
        elif alignment == "right":
            sep = "-" * (width + 1) + ":"
        else:  # left or default
            sep = ":" + "-" * (width + 1)
        separators.append(sep)

    separator = "|" + "|".join(separators) + "|"

    table = f"{header}\n{separator}"
    return table


def create_table_row(cells: list[str]) -> str:
    """
    Create a markdown table row.

    Args:
        cells: list of cell contents

    Returns:
        Markdown string for the table row

    Example:
        >>> create_table_row(['Bulbasaur', 'Grass', '45'])
        '| Bulbasaur | Grass | 45 |'
    """
    return "| " + " | ".join(str(cell) for cell in cells) + " |"


def create_table(
    headers: list[str],
    rows: list[list[str]],
    alignments: Optional[list[str]] = None,
) -> str:
    """
    Create a complete markdown table.

    Args:
        headers: list of column headers
        rows: list of rows, where each row is a list of cell contents
        alignments: list of alignment values for each column

    Returns:
        Complete markdown table as a string

    Example:
        >>> headers = ['Name', 'Type', 'Power']
        >>> rows = [['Tackle', 'Normal', '40'], ['Ember', 'Fire', '40']]
        >>> create_table(headers, rows, ['left', 'left', 'center'])
    """
    table = create_table_header(headers, alignments)

    for row in rows:
        table += "\n" + create_table_row(row)

    return table
