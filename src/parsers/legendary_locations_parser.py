"""
Parser for Legendary Locations documentation file.

This parser:
1. Reads data/documentation/Legendary Locations.txt
2. Generates a markdown file to docs/legendary_locations.md
"""

import re
from typing import Any, Dict

from src.utils.formatters.markdown_util import format_pokemon

from .base_parser import BaseParser


class LegendaryLocationsParser(BaseParser):
    """
    Parser for Legendary Locations documentation.

    Extracts legendary Pokemon location information and generates markdown.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Legendary Locations parser."""
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = ["General Information", "Legendary Encounters"]

        # Track encounters for current epitaph and table state
        self._encounters = set()
        self.in_encounter = False

    def parse_general_information(self, line: str) -> None:
        """Parse lines under the General Information section."""
        self.parse_default(line)

    def parse_legendary_encounters(self, line: str) -> None:
        """
        Parse the Legendary Encounters section containing location data.

        Processes lines describing where legendary Pokemon can be found, organized by epitaph.
        Each epitaph groups several legendary encounters together, followed by detailed
        location information for each Pokemon.

        Format expected:
            Epitaph Name: Pokemon1, Pokemon2, and Pokemon3.
            Pokemon1
             - Location detail line
            Pokemon2
             - Location detail line
            Pokemon3
             - Location detail line

        The parser generates a markdown table for each epitaph group with columns:
        - Pokemon name (with sprite and link)
        - Encounter details (location, level, conditions)

        Args:
            line: A single line from the Legendary Locations documentation file

        Side Effects:
            - Updates self._encounters set to track Pokemon names in current epitaph
            - Sets self.in_encounter flag when processing an encounter table
        """
        # Match: "Epitaph: encounter1, encounter2, and encounter3."
        if match := re.match(r"^([^:]+):\s*([^.]+)\.$", line):
            epitaph, encounters = match.groups()
            self._encounters = set(re.split(r", | and ", encounters))

            self._markdown += f"### {epitaph}\n\n"
        # Match: encounter name from the encounters set
        elif line in self._encounters:
            if not self.in_encounter:
                self._markdown += f"| Pokémon | Encounter Details |\n"
                self._markdown += f"|:-------:|-------------------|\n"
                self.in_encounter = True

            self._markdown += f"| {format_pokemon(line)} | "
            self._encounters.remove(line)
        # Match: " - detail" (encounter detail line)
        elif self.in_encounter and line.startswith(" - "):
            self._markdown += f"{line.removeprefix(" - ")} |"

            if len(self._encounters) == 0:
                self._markdown += "\n"
                self.in_encounter = False
        # Default: regular text line
        else:
            self.parse_default(line)
