"""
Parser for Legendary Locations documentation file.

This parser:
1. Reads data/documentation/Legendary Locations.txt
2. Generates a markdown file to docs/legendary_locations.md
"""

from typing import Any, Dict

from src.utils.markdown_utils import format_pokemon_with_sprite
from .base_parser import BaseParser
import re


class LegendaryLocationsParser(BaseParser):
    """
    Parser for Legendary Locations documentation.

    Extracts legendary Pokemon location information and generates markdown.
    """

    _LEGENDARY_PATTERN = re.compile(r"^([^:]+):\s*([^.]+)\.$")

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Legendary Locations parser."""
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = ["General Information", "Legendary Encounters"]

        self._encounters = set()
        self.in_encounter = False

    def parse_general_information(self, line: str) -> None:
        """Parse lines under the General Information section."""
        self._markdown += f"{line}\n"

    def parse_legendary_encounters(self, line: str) -> None:
        """Parse lines under the Legendary Encounters section."""

        if match := self._LEGENDARY_PATTERN.match(line):
            epitaph, encounters = match.groups()
            self._encounters = set(re.split(r", | and ", encounters))

            self._markdown += f"### {epitaph}\n\n"
        elif line in self._encounters:
            if not self.in_encounter:
                self._markdown += f"| Pokémon | Encounter Details |\n"
                self._markdown += f"|:-------:|-------------------|\n"
                self.in_encounter = True

            self._markdown += f"| {format_pokemon_with_sprite(line, animated=True)} | "
            self._encounters.remove(line)
        elif self.in_encounter and line.startswith(" - "):
            self._markdown += f"{line.removeprefix(" - ")} |"

            if len(self._encounters) == 0:
                self._markdown += "\n"
                self.in_encounter = False
        else:
            self._markdown += f"{line}\n"
