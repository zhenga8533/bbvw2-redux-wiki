"""
Utility functions for generating consistent markdown tables.

This module provides helpers for creating standardized tables that follow
the wiki's formatting guidelines as defined in TABLE_STANDARDS.md.
"""

from typing import Optional


def create_table_header(
    columns: list[str], alignments: Optional[list[str]] = None
) -> str:
    """Create a markdown table header with proper alignment markers.

    Args:
        columns (list[str]): List of column names
        alignments (Optional[list[str]], optional): List of alignment values ('left', 'center', 'right'). If None, all columns default to 'left'.

    Raises:
        ValueError: If the number of alignments does not match the number of columns

    Returns:
        str: Markdown string with table header and separator line

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
    """Create a markdown table row.

    Args:
        cells (list[str]): List of cell contents

    Returns:
        str: Markdown string for the table row

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
    """Create a complete markdown table.

    Args:
        headers (list[str]): List of column headers
        rows (list[list[str]]): List of rows, where each row is a list of cell contents
        alignments (Optional[list[str]], optional): List of alignment values for each column. Defaults to None.

    Returns:
        str: Complete markdown table as a string

    Example::
        >>> create_table(['Name', 'Type', 'Power'], [['Tackle', 'Normal', '40'], ['Ember', 'Fire', '40']], ['left', 'left', 'center'])
        '| Name   | Type   | Power |\n|--------|--------|:-----:|\n| Tackle | Normal |  40  |\n| Ember  | Fire   |  40  |'
    """
    table = create_table_header(headers, alignments)

    for row in rows:
        table += "\n" + create_table_row(row)

    return table
