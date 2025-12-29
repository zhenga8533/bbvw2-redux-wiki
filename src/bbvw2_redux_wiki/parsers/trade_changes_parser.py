"""
Parser for Trade Changes documentation file.

This parser:
1. Reads data/documentation/Trade Changes.txt
2. Generates a markdown file to docs/trade_changes.md
"""

import re

from rom_wiki_core.utils.formatters.markdown_formatter import (
    format_pokemon_card_grid,
)

from .base_parser import BaseParser


class TradeChangesParser(BaseParser):
    """Parser for Trade Changes documentation.

    Args:
        BaseParser (_type_): Abstract base parser class.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Trade Changes parser.

        Args:
            input_file (str): Path to the input file.
            output_dir (str, optional): Path to the output directory. Defaults to "docs".
        """
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = ["General Notes", "Trade Pokémon", "Trade Items"]

        # Trade Pokémon states
        self._in_details = True
        self._current_pokemon = None

    def parse_general_notes(self, line: str) -> None:
        """Parse a line in the General Notes section.

        Args:
            line (str): Line of text to parse.
        """
        self.parse_default(line)

    def parse_trade_pokemon(self, line: str) -> None:
        """Parse a line in the Trade Pokémon section.

        Args:
            line (str): Line of text to parse.
        """
        # Match: "Pokémon Trade"
        if match := re.match(r"^([a-zA-z]+) Trade\.*", line):
            pokemon = match.group(1)
            self._current_pokemon = pokemon

            self._markdown += f"### {pokemon} Trade\n\n"
            self._markdown += format_pokemon_card_grid(
                [pokemon], relative_path="../pokedex/pokemon"
            )
            self._markdown += "\n\n"

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

    def parse_trade_items(self, line: str) -> None:
        """Parse a line in the Trade Items section.

        Args:
            line (str): Line of text to parse.
        """
        self.parse_default(line)
