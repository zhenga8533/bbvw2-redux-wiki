"""
Parser for Wild Area Changes documentation file.

This parser:
1. Reads data/documentation/Wild Area Changes.txt
2. Generates a markdown file to docs/wild_area_changes.md
"""

from typing import Any, Dict
from .base_parser import BaseParser


class WildAreaChangesParser(BaseParser):
    """
    Parser for Wild Area Changes documentation.

    Extracts wild area change information and generates markdown.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Wild Area Changes parser."""
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = [
            "General Changes",
            "Main Story Changes",
            "Postgame Locations Changes",
            "Hidden Grotto Guide",
        ]

    def parse_general_changes(self, line: str) -> None:
        """Parse the General Changes section."""
        self.parse_default(line)

    def parse_main_story_changes(self, line: str) -> None:
        """Parse the Main Story Changes section."""
        self.parse_default(line)

    def parse_postgame_locations_changes(self, line: str) -> None:
        """Parse the Postgame Locations Changes section."""
        self.parse_default(line)

    def parse_hidden_grotto_guide(self, line: str) -> None:
        """Parse the Hidden Grotto Guide section."""
        self.parse_default(line)
