"""
Parser for Item Changes documentation file.

This parser:
1. Reads data/documentation/Item Changes.txt
2. Generates a markdown file to docs/item_changes.md
"""

import re
from typing import Any, Dict

from src.utils.formatters.markdown_util import format_checkbox, format_item

from .base_parser import BaseParser


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
            "Modified Marts",
            "Modified TMs + Locations",
        ]

        # Modified Items states
        self._in_replace = False
        self._in_adjust_cost = False

        # Item Locations states
        self._current_location = ""
        self._is_table_open = False

        # Modified Marts states
        self._current_location = ""

        # Modified TMs + Locations states
        self._is_table_open = False

    def handle_section_change(self, new_section: str) -> None:
        """Handle state reset on section change."""
        self._current_location = ""
        self._is_table_open = False
        return super().handle_section_change(new_section)

    def parse_evless_mode_information(self, line: str) -> None:
        """Parse lines under the EVless Mode Information section."""
        self.parse_default(line)

    def parse_modified_items(self, line: str) -> None:
        """Parse lines under the Modified Items section."""
        # Match: " - <old_item> -> <new_item>"
        if match := re.match(r"^ - ([a-zA-Z\s]+) -> ([a-zA-Z\s]+)$", line):
            if not self._in_replace:
                self._markdown += "| Old Item | New Item |\n"
                self._markdown += "|:---------|:---------|\n"
                self._in_replace = True

            old_item, new_item = match.groups()
            old_item_md = format_item(old_item, relative_path="..")
            new_item_md = format_item(new_item, relative_path="..")

            self._markdown += f"| {old_item_md} | {new_item_md} |\n"
        # Match: " - <item> ($<old_cost> -> $<new_cost>)"
        elif match := re.match(r"^ - ([a-zA-Zé\s]+)\s+\(\$(\d+) -> \$(\d+)\)$", line):
            if not self._in_adjust_cost:
                self._markdown += "\n"
                self._markdown += "| Item | Old Cost | New Cost |\n"
                self._markdown += "|:-----|:---------|:---------|\n"
                self._in_adjust_cost = True

            item, old_cost, new_cost = match.groups()
            item_md = format_item(item, relative_path="..")

            self._markdown += f"| {item_md} | ${old_cost} | ${new_cost} |\n"
        # Match: " - <item>"
        elif match := re.match(r"^ - (.*)$", line):
            item = match.group(1)
            item_md = format_item(item, relative_path="..")

            self._markdown += f"- {item_md}\n"
        # Default: regular text line
        else:
            self.parse_default(line)

    def parse_pickup_table_changes(self, line: str) -> None:
        """Parse lines under the Pickup Table Changes section."""
        # Match: " - All instances of a <old_item> have been replaced with a <new_item>."
        if match := re.match(
            r"^ - All instances of a ([a-zA-Z\s']+) have been replaced with a ([a-zA-Z\s']+)\.$",
            line,
        ):
            old_item, new_item = match.groups()
            old_item_md = format_item(old_item, relative_path="..")
            new_item_md = format_item(new_item, relative_path="..")

            self._markdown += f"- All instances of a {old_item_md} have been replaced with a {new_item_md}.\n"
        # Default: regular text line
        else:
            self.parse_default(line)

    def parse_castelia_berry_guy_battle_subway_and_pwt_prizes(self, line: str) -> None:
        """Parse lines under the Castelia Berry Guy, Battle Subway and PWT Prizes section."""
        self.parse_default(line)

    def parse_item_locations(self, line: str) -> None:
        """Parse lines under the Item Locations section."""
        # Match: "~~~~~ <location> ~~~~~"
        if match := re.match(r"^~+\s*(.*?)\s*~+$", line):
            self._current_location = match.group(1)
            self._markdown += f"\n### {self._current_location}\n\n"
            self._is_table_open = False
        # Match: "*<line>"
        elif line.startswith("*"):
            self.parse_default(line)
        # Match: any truthy string if inside a location
        elif line and self._current_location:
            if not self._is_table_open:
                self._is_table_open = True
                self._markdown += "| Old Item | New Item | Hidden |\n"
                self._markdown += "|:---------|:---------|:------:|\n"

            self._format_items_line(line)
        # Default: regular text line
        else:
            self.parse_default(line)

    def _extract_item_quantities(
        self, items_list: list[str]
    ) -> tuple[list[str], list[str | None]]:
        """Parses item strings, separating item names from quantities."""
        items = []
        quantities = []
        for item_str in items_list:
            if " x" in item_str:
                # Split item name and quantity
                item, quantity = item_str.split(" x")
                items.append(item.strip())
                quantities.append(quantity.strip())
            else:
                # No quantity found
                items.append(item_str.strip())
                quantities.append(None)
        return items, quantities

    def _format_item_column(
        self,
        items: list[str],
        quantities: list[str | None],
        extra_text: str = "",
    ) -> str:
        """Formats a list of items and quantities into a markdown table cell."""
        # Handle empty column
        if not items:
            return "—"

        item_md_parts = []
        for i, item in enumerate(items):
            quantity = quantities[i]

            # Format the base item name
            item_md = format_item(item, relative_path="..")

            # Add quantity if it exists
            if quantity:
                item_md += f" x{quantity}"

            item_md_parts.append(item_md)

        # Join all items with a line break
        items_str = "<br>".join(item_md_parts)

        # Prepend extra text (like "Choice between a:") if it exists
        if extra_text:
            return f"{extra_text}{items_str}"

        return items_str

    def _format_items_line(self, line: str) -> None:
        raw_old_items, raw_new_items = [], []
        old_extra, new_extra = "", ""

        # Check for hidden status
        is_hidden = line.endswith(" (Hidden)")
        line = line.replace(" (Hidden)", "").strip()

        # Determine old and new item names
        if " -> " in line:
            old_str, new_str = line.split(" -> ")
            raw_old_items = old_str.split("/")
            raw_new_items = new_str.split("/")
        elif line.startswith("Choice between a "):
            choices = re.split(r", | or ", line.replace("Choice between a ", ""))
            raw_new_items = choices
            new_extra = "Choice between a:<br>"
        else:
            raw_new_items = [line]

        # 1. Parse quantities (replaces first duplicated block)
        old_items, old_quantities = self._extract_item_quantities(raw_old_items)
        new_items, new_quantities = self._extract_item_quantities(raw_new_items)

        # 2. Format columns (replaces second duplicated block)
        old_col_md = self._format_item_column(old_items, old_quantities, old_extra)
        new_col_md = self._format_item_column(new_items, new_quantities, new_extra)

        # 3. Format hidden status
        hidden_md = format_checkbox(is_hidden)

        # 4. Assemble the final table row
        self._markdown += f"| {old_col_md} | {new_col_md} | {hidden_md} |\n"

    def parse_modified_marts(self, line: str) -> None:
        """Parse lines under the Modified Marts section."""
        # Match: "~~~~~ <location> ~~~~~"
        if match := re.match(r"^~+\s*(.*?)\s*~+$", line):
            self._current_location = match.group(1)
            self._markdown += f"\n### {self._current_location}\n\n"
            self._is_table_open = False
        # Match: " - <item>"
        elif line.startswith(" - "):
            item = line[3:].strip()
            item_md = format_item(item, relative_path="..")
            self._markdown += f"- {item_md}\n"
        # Default: regular text line
        else:
            self.parse_default(line)

    def parse_modified_tms_locations(self, line: str) -> None:
        """Parse lines under the Modified TMs + Locations section."""
        # Match: table header "TM #    Move                            Location in Redux"
        if line == "TM #    Move                            Location in Redux":
            self._is_table_open = True
            self._markdown += "| TM # | Move | Location in Redux |\n"
        # Match: table separator "----    ----                            ----"
        elif line == "----    ----                            ----":
            self._markdown += "|:-----|:-----|:------------------|\n"
        # Match: table row "<tm_number>    <move_name>                            <location>"
        elif line and self._is_table_open:
            # Split the line into components
            parts = re.split(r"\s{3,}", line)
            if len(parts) == 3:
                tm_number, move_name, location = parts
                tm_html = format_item(tm_number, relative_path="..")
                self._markdown += f"| {tm_html} | {move_name} | {location} |\n"
            else:
                self.logger.warning(f"Unexpected TM table row format: '{line}'")
                self.parse_default(line)
        # Default: regular text line
        else:
            self.parse_default(line)
