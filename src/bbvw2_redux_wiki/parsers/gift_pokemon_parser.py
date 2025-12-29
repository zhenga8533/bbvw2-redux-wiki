"""
Parser for Gift Pokemon documentation file.

This parser:
1. Reads data/documentation/Gift Pokemon.txt
2. Generates a markdown file to docs/gift_pokemon.md
"""

import re

from rom_wiki_core.parsers.base_parser import BaseParser
from rom_wiki_core.utils.formatters.markdown_formatter import (
    format_pokemon_card_grid,
)


class GiftPokemonParser(BaseParser):
    """Parser for Gift Pokemon documentation.

    Args:
        BaseParser (_type_): Abstract base parser class.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Gift Pokemon parser.

        Args:
            input_file (str): Path to the input file.
            output_dir (str, optional): Path to the output directory. Defaults to "docs".
        """
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = ["General Notes", "Gift Pokémon", "Special Encounters"]

    def get_title(self) -> str:
        """Get the title for the Gift Pokémon section.

        Returns:
            str: Title of the Gift Pokémon section.
        """
        return "Gift Pokémon"

    def parse_general_notes(self, line: str) -> None:
        """Parse lines under the General Notes section.

        Args:
            line (str): Line of text to parse.
        """
        self.parse_default(line)

    def parse_gift_pokemon(self, line: str) -> None:
        """Parse lines under the Gift Pokémon section.

        Args:
            line (str): Line of text to parse.
        """
        next_line = self.peek_line(1)

        # Match: header line followed by "---" separator
        if next_line == "---":
            self._markdown += self._format_gift_pokemon(line)
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

    def _format_gift_pokemon(self, header: str) -> str:
        """Format gift Pokemon section with grid cards.

        Args:
            header (str): Header text for the section.

        Returns:
            str: Formatted markdown string for the gift Pokemon section.
        """
        # Clean up header
        header = header.removesuffix(".")
        gift_pokemon_names = re.split(r", | or ", header.removesuffix(" Egg"))

        md = f"### {header}\n\n"
        md += format_pokemon_card_grid(
            gift_pokemon_names, relative_path="../pokedex/pokemon"
        )
        md += "\n\n"

        return md

    def parse_special_encounters(self, line: str) -> None:
        """Parse lines under the Special Encounters section.

        Args:
            line (str): Line of text to parse.
        """
        self.parse_gift_pokemon(line)
