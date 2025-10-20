"""
Parser for Gift Pokemon documentation file.

This parser:
1. Reads data/documentation/Gift Pokemon.txt
2. Generates a markdown file to docs/gift_pokemon.md
"""

from src.utils.markdown_util import format_pokemon
from .base_parser import BaseParser
import re


class GiftPokemonParser(BaseParser):
    """
    Parser for Gift Pokemon documentation.

    Extracts gift Pokemon information and generates markdown.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Gift Pokemon parser."""
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = ["General Notes", "Gift Pokémon", "Special Encounters"]

    def get_title(self) -> str:
        """Return the title with proper unicode character."""
        return "Gift Pokémon"

    def parse_general_notes(self, line: str) -> None:
        """Parse lines under the General Notes section."""
        self.parse_default(line)

    def parse_gift_pokemon(self, line: str) -> None:
        """Parse lines under the Gift Pokémon section."""
        next_line = self.peek_line(1)

        # Match: header line followed by "---" separator
        if next_line == "---":
            self._format_gift_pokemon(line)
        # Match: separator line "---"
        elif line == "---":
            return
        # Match: "Key: Value"
        elif match := re.match(r"([a-zA-z]+): (.*)", line):
            key, value = match.groups()
            self._markdown += f"**{key}**: {value}\n\n"
        # Default: regular text line
        else:
            self.parse_default(line)

    def _format_gift_pokemon(self, header: str) -> None:
        """Format gift Pokemon section with sprite table."""
        # Clean up header
        header = header.removesuffix(".")
        gift_pokemon = re.split(r", | or ", header.removesuffix(" Egg"))

        self._markdown += f"### {header}\n\n"

        # Build table rows in chunks of 3, centering if fewer than 3
        table = "|   |   |   |\n|:-:|:-:|:-:|\n"
        rows = [
            [format_pokemon(p) for p in gift_pokemon[i : i + 3]]
            for i in range(0, len(gift_pokemon), 3)
        ]

        for row in rows:
            # Pad row to always have 3 columns
            row_len = len(row)
            row += [""] * (3 - row_len)
            # If only one cell, center it in the middle column
            if row_len == 1:
                row = ["", row[0], ""]
            table += (
                "|" + "|".join(f" {cell} " if cell else "   " for cell in row) + "|\n"
            )

        self._markdown += f"{table}\n\n"

    def parse_special_encounters(self, line: str) -> None:
        """Parse lines under the Special Encounters section."""
        self.parse_gift_pokemon(line)
