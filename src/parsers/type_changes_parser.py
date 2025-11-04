"""
Parser for Type Changes documentation file.

This parser:
1. Reads data/documentation/Type Changes.txt
2. Updates pokemon type data in data/pokedb/parsed/
3. Generates a markdown file to docs/type_changes.md
"""

import re

from src.utils.formatters.markdown_formatter import format_pokemon

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
            pokemon, old_type, new_type, justification = re.split(r"\s{3,}", line)
            number, pokemon = pokemon.split(" ", 1)
            pokemon_html = format_pokemon(pokemon)

            self._markdown += f"| {number} | {pokemon_html} | {old_type} | {new_type} | {justification} |\n"
        # Default: regular text line
        else:
            self.parse_default(line)
