"""
Parser for Trade Changes documentation file.

This parser:
1. Reads data/documentation/Trade Changes.txt
2. Generates a markdown file to docs/trade_changes.md
"""

from typing import Any, Dict

from src.utils.markdown_util import format_pokemon_with_sprite
from .base_parser import BaseParser
import re


class TradeChangesParser(BaseParser):
    """
    Parser for Trade Changes documentation.

    Extracts trade change information and generates markdown.
    """

    _TRADE_PATTERN = re.compile(r"^([a-zA-z]+) Trade\.*")
    _DETAIL_PATTERN = re.compile(r"^([a-zA-z]+): (.*)\.*")

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Trade Changes parser."""
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = ["General Notes", "Trade Pokémon", "Trade Items"]

        self._in_details = True

    def parse_general_notes(self, line: str) -> None:
        """Parse a line in the General Notes section."""
        self._markdown += f"{line}\n"

    def parse_trade_pokemon(self, line: str) -> None:
        """Parse a line in the Trade Pokémon section."""

        if match := self._TRADE_PATTERN.match(line):
            pokemon = match.group(1)

            self._markdown += f"### {pokemon} Trade\n\n"
            self._markdown += f"{format_pokemon_with_sprite(pokemon)}\n\n"

            self._in_details = False
        elif match := self._DETAIL_PATTERN.match(line):
            key, value = match.groups()
            self._markdown += f"**{key}**: {value}\n\n"
        elif line == "---":
            return
        else:
            if not self._in_details:
                self._markdown += "**Details**:\n"
                self._in_details = True
            self._markdown += f"{line}\n"

    def parse_trade_items(self, line: str) -> None:
        """Parse a line in the Trade Items section."""
        self._markdown += f"{line}\n"
