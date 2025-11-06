"""
Parser for Type Changes documentation file.

This parser:
1. Reads data/documentation/Type Changes.txt
2. Updates pokemon type data in data/pokedb/parsed/
3. Generates a markdown file to docs/type_changes.md
"""

import re

from src.utils.formatters.markdown_formatter import format_pokemon, format_type_badge

from .base_parser import BaseParser


class TypeChangesParser(BaseParser):
    """
    Parser for Type Changes documentation.

    Extracts type changes and updates Pokemon JSON files.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Type Changes parser."""
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = ["General Notes", "Pokémon Type Changes"]

    def parse_general_notes(self, line: str) -> None:
        """Parse the General Notes section."""
        self.parse_default(line)

    def parse_pokemon_type_changes(self, line: str) -> None:
        """
        Parse the Pokémon Type Changes section containing the type change table.

        Processes lines that describe Pokemon type modifications in the hack, including:
        - Table headers showing column names
        - Table separator rows with dashes
        - Data rows: "#<number> <pokemon>   <old type>   <new type>   <justification>"

        The parser generates a markdown table with columns for:
        - Pokedex number
        - Pokemon name (with sprite and link)
        - Old type combination
        - New type combination
        - Justification for the change

        Args:
            line: A single line from the Type Changes documentation file
        """
        # Match: "Pokémon                 Old Type            New Type                Justification"
        if (
            line
            == "Pokémon                 Old Type            New Type                Justification"
        ):
            self._markdown += (
                "| Number | Pokémon | Old Type | New Type | Justification |\n"
            )
        # Match: "---                     ---                 ---                     ---"
        elif (
            line
            == "---                     ---                 ---                     ---"
        ):
            self._markdown += (
                "|:-------|:-------:|:---------|:---------|:--------------|\n"
            )
        # Match: "#<number> <pokemon>   <old type>   <new type>   <justification>"
        elif line.startswith("#"):
            self._format_type_change_row(line)
        # Default: regular text line
        else:
            self.parse_default(line)

    def _format_type_change_row(self, line: str) -> None:
        """Format a row in the type change table.

        Args:
            line (str): A line from the type change table.
        """
        pokemon, old_type, new_type, justification = re.split(r"\s{3,}", line)
        number, pokemon = pokemon.split(" ", 1)
        pokemon_html = format_pokemon(pokemon, relative_path="..")

        # Format old and new types with badges
        old_types = old_type.split(" / ")
        new_types = new_type.split(" / ")
        old_type_badges = " ".join([format_type_badge(t) for t in old_types])
        new_type_badges = " ".join([format_type_badge(t) for t in new_types])
        old_type_html = f"<div class='badges-vstack'>{old_type_badges}</div>"
        new_type_html = f"<div class='badges-vstack'>{new_type_badges}</div>"

        # Format justification with line breaks
        justification_lines = "<br>".join(
            [
                f"{idx+1}. {line.strip()}"
                for idx, line in enumerate(justification.split("; "))
            ]
        )

        self._markdown += f"| {number} | {pokemon_html} | {old_type_html} | {new_type_html} | {justification_lines} |\n"
