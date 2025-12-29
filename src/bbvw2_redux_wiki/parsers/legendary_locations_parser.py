"""
Parser for Legendary Locations documentation file.

This parser:
1. Reads data/documentation/Legendary Locations.txt
2. Generates a markdown file to docs/legendary_locations.md
"""

import re

from rom_wiki_core.parsers.base_parser import BaseParser
from rom_wiki_core.utils.core.loader import PokeDBLoader
from rom_wiki_core.utils.formatters.markdown_formatter import (
    format_pokemon,
    format_type_badge,
)


class LegendaryLocationsParser(BaseParser):
    """Parser for Legendary Locations documentation.

    Args:
        BaseParser (_type_): Abstract base parser class.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Legendary Locations parser.

        Args:
            input_file (str): Path to the input file.
            output_dir (str, optional): Path to the output directory. Defaults to "docs".
        """
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = ["General Information", "Legendary Encounters"]

        # Track encounters for current epitaph and table state
        self._encounters = set()
        self.in_encounter = False

    def parse_general_information(self, line: str) -> None:
        """Parse lines under the General Information section.

        Args:
            line (str): Line of text to parse.
        """
        self.parse_default(line)

    def parse_legendary_encounters(self, line: str) -> None:
        """Parse lines under the Legendary Encounters section.

        Args:
            line (str): Line of text to parse.
        """
        # Match: "Epitaph: encounter1, encounter2, and encounter3."
        if match := re.match(r"^([^:]+):\s*([^.]+)\.$", line):
            epitaph, encounters = match.groups()
            self._encounters = set(re.split(r", | and ", encounters))

            self._markdown += f"### {epitaph}\n\n"
        # Match: encounter name from the encounters set
        elif line in self._encounters:
            if not self.in_encounter:
                self._markdown += f"| Pokémon | Type(s) | Encounter Details |\n"
                self._markdown += f"|:-------:|:-------:|-------------------|\n"
                self.in_encounter = True

            self._markdown += f"| {format_pokemon(line)} | "

            pokemon_data = PokeDBLoader.load_pokemon(line)
            types = pokemon_data.types if pokemon_data else []
            self._markdown += f"<div class='badges-vstack'>{' '.join(format_type_badge(t) for t in types)}</div> | "

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
