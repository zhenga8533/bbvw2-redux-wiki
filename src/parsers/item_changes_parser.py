"""
Parser for Item Changes documentation file.

This parser:
1. Reads data/documentation/Item Changes.txt
2. Generates a markdown file to docs/item_changes.md
"""

from typing import Any, Dict

from src.utils.markdown_util import format_item
from .base_parser import BaseParser
import re


class ItemChangesParser(BaseParser):
    """
    Parser for Item Changes documentation.

    Extracts item change information and generates markdown.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Item Changes parser."""
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = [
            "EVless Mode Information",
            "Modified Items",
            "Pickup Table Changes",
            "Castelia Berry Guy, Battle Subway and PWT Prizes",
            "Item Locations",
        ]

        # Modified Items state
        self._in_replace = False
        self._in_adjust_cost = False

    def parse_evless_mode_information(self, line: str) -> None:
        """Parse lines under the EVless Mode Information section."""
        self.parse_default(line)

    def parse_modified_items(self, line: str) -> None:
        """Parse lines under the Modified Items section."""
        # Match: " - old_item -> new_item"
        if match := re.match(r"^ - ([a-zA-Z\s]+) -> ([a-zA-Z\s]+)$", line):
            if not self._in_replace:
                self._markdown += "| Old Item | New Item |\n"
                self._markdown += "|:--------:|:--------:|\n"
                self._in_replace = True

            old_item, new_item = match.groups()
            old_item_md = format_item(old_item)
            new_item_md = format_item(new_item)

            self._markdown += f"| {old_item_md} | {new_item_md} |\n"
        # Match: " - item ($old_cost -> $new_cost)"
        elif match := re.match(r"^ - ([a-zA-Zé\s]+)\s+\(\$(\d+) -> \$(\d+)\)$", line):
            if not self._in_adjust_cost:
                self._markdown += "\n"
                self._markdown += "| Item | Old Cost | New Cost |\n"
                self._markdown += "|:----:|:--------:|:--------:|\n"
                self._in_adjust_cost = True

            item, old_cost, new_cost = match.groups()
            item_md = format_item(item)

            self._markdown += f"| {item_md} | ${old_cost} | ${new_cost} |\n"
        # Match: " - item" (simple list item)
        elif match := re.match(r"^ - (.*)$", line):
            item = match.group(1)
            item_md = format_item(item)

            self._markdown += f"- {item_md}\n"
        # Default: regular text line
        else:
            self.parse_default(line)

    def parse_pickup_table_changes(self, line: str) -> None:
        """Parse lines under the Pickup Table Changes section."""
        self.parse_default(line)

    def parse_castelia_berry_guy_battle_subway_and_pwt_prizes(self, line: str) -> None:
        """Parse lines under the Castelia Berry Guy, Battle Subway and PWT Prizes section."""
        self.parse_default(line)

    def parse_item_locations(self, line: str) -> None:
        """Parse lines under the Item Locations section."""
        self.parse_default(line)
