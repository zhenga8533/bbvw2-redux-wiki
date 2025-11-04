"""
Parser for Trade Changes documentation file.

This parser:
1. Reads data/documentation/Trade Changes.txt
2. Generates a markdown file to docs/trade_changes.md
"""

import re

from src.utils.formatters.markdown_util import format_pokemon_card

from .base_parser import BaseParser


class TradeChangesParser(BaseParser):
    """
    Parser for Trade Changes documentation.

    Extracts trade change information and generates markdown.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Trade Changes parser."""
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = ["General Notes", "Trade Pokémon", "Trade Items"]

        # Trade Pokémon states
        self._in_details = True
        self._current_pokemon = None

    def parse_general_notes(self, line: str) -> None:
        """Parse a line in the General Notes section."""
        self.parse_default(line)

    def parse_trade_pokemon(self, line: str) -> None:
        """Parse a line in the Trade Pokémon section."""
        # Match: "Pokémon Trade"
        if match := re.match(r"^([a-zA-z]+) Trade\.*", line):
            pokemon = match.group(1)
            self._current_pokemon = pokemon

            self._markdown += f"### {pokemon} Trade\n\n"
            self._format_trade_pokemon(pokemon)

            self._in_details = False
        # Match: "Key: Value"
        elif match := re.match(r"^([a-zA-z]+): (.*)\.*", line):
            key, value = match.groups()
            self._markdown += f"**{key}**: {value}\n\n"
        # Match: separator line "---"
        elif line == "---":
            return
        # Default: regular text line
        else:
            if not self._in_details:
                self._markdown += "**Details**:\n"
                self._in_details = True
            self.parse_default(line)

    def _format_trade_pokemon(self, pokemon_name: str) -> None:
        """Format trade Pokemon with card display."""
        # Card structure with grid
        self._markdown += '<div class="grid cards" markdown>\n\n'
        # Use utility function to create card (must be in a list item)
        self._markdown += "-   "
        self._markdown += format_pokemon_card(pokemon_name, relative_path="../pokedex/pokemon")
        self._markdown += "\n\n</div>\n\n"

    def parse_trade_items(self, line: str) -> None:
        """Parse a line in the Trade Items section."""
        self.parse_default(line)
