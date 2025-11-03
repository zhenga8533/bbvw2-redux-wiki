"""
Parser for Move Changes documentation file.

This parser:
1. Reads data/documentation/Move Changes.txt
2. Updates move data in data/pokedb/parsed/
3. Generates a markdown file to docs/move_changes.md
"""

import re

from src.services.move_service import MoveService
from src.utils.formatters.markdown_util import format_checkbox, format_move

from .base_parser import BaseParser


class MoveChangesParser(BaseParser):
    """
    Parser for Move Changes documentation.

    Extracts move changes and updates Pokemon JSON files.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Move Changes parser."""
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = [
            "General Changes",
            "Move Replacements",
            "Type Changes",
            "Redux Move Modifications",
            "Legends: Arceus Moves",
        ]

        # Move Replacement States
        self._is_table_open = False

        # Type Change States
        self._is_table_open = False
        self._current_move = ""

        # Move Modification States
        self._is_table_open = False
        self._current_move = ""
        self._is_move_open = False

    def handle_section_change(self, new_section: str) -> None:
        """Handle state reset on section change."""
        if self._is_table_open:
            self._is_table_open = False
            self._markdown += "\n"
        self._current_move = ""
        return super().handle_section_change(new_section)

    def parse_general_changes(self, line: str) -> None:
        """Parse general move changes."""
        self.parse_default(line)

    def parse_move_replacements(self, line: str) -> None:
        """Parse move replacements and copy new moves from gen8."""
        # Match: "Old Move                New Move"
        if line == "Old Move                New Move":
            self._is_table_open = True
            self._markdown += "| Old Move | New Move |\n"
        # Match: "---------               ---------"
        elif line == "---------               ---------":
            self._markdown += "|:---------|:---------|\n"
        # Match: table row
        elif self._is_table_open and line:
            old_move, new_move = re.split(r"\s{3,}", line)

            # Copy the new move from gen8 to parsed data
            MoveService.copy_new_move(new_move)

            old_move_html = format_move(old_move, relative_path="..")
            new_move_html = format_move(new_move, relative_path="..")
            self._markdown += f"| {old_move_html} | {new_move_html} |\n"
        # Default: regular text line
        else:
            self.parse_default(line)

    def parse_type_changes(self, line: str) -> None:
        """Parse type changes."""
        next_line = self.peek_line(1) or ""
        # Match: "<move_name>"
        if next_line.startswith(" - "):
            self._current_move = line
            if not self._is_table_open:
                self._is_table_open = True
                self._markdown += "| Move | Old Type | New Type | Custom |\n"
                self._markdown += "|:-----|:---------|:---------|:------:|\n"
            self._markdown += f"| {format_move(self._current_move, relative_path="..")} "
        # Match: " - <old_type> -> <new_type>"
        elif line.startswith(" - "):
            old_type, new_type = line[3:].split(" -> ")
            custom = False
            if new_type.endswith(" [!]"):
                new_type = new_type[:-4]
                custom = True

            self._markdown += f"| {old_type} | {new_type} | {format_checkbox(custom)} |"
        # Default: regular text line
        else:
            self.parse_default(line)

    def parse_redux_move_modifications(self, line: str) -> None:
        """Parse Redux move modifications."""
        next_line = self.peek_line(1) or ""
        # Match: " - <old_type> -> <new_type>"
        if line.startswith(" - "):
            self._format_move_row(line[3:])
        # Match: "<move_name>"
        elif next_line.startswith(" - "):
            self._current_move = line
            self._is_move_open = False

            if not self._is_table_open:
                self._is_table_open = True
                self._markdown += "| Move | Attribute | Old | New | Custom | L:A |\n"
                self._markdown += "|:-----|:----------|:----|:----|:------:|:---:|\n"
        # Match: "* <some text>"
        elif line.startswith("*"):
            self._markdown += "\n"
            self.parse_default(line)
        # Default: regular text line
        elif not self._is_table_open:
            self.parse_default(line)

    def _format_move_row(self, line: str) -> None:
        """Format a move row for markdown table."""
        old_field, new_field = line.split(" -> ") if " -> " in line else (line, "")
        attribute, old_field = old_field.split(" ", 1)

        # Handle case where only old field is given
        if new_field == "":
            old_field, new_field = "—", old_field

        # Check for custom and L:A flags
        custom = False
        if new_field.endswith(" [!]"):
            new_field = new_field[:-4]
            custom = True
        la = False
        if new_field.endswith(" [L:A]"):
            new_field = new_field[:-5]
            la = True

        # Update move data if attribute is supported
        supported_attributes = ["Power", "PP", "Priority", "Accuracy", "Type"]
        if attribute in supported_attributes:
            MoveService.update_move_attribute(
                move_name=self._current_move,
                attribute=attribute,
                new_value=new_field,
            )

        # Add to markdown table
        move_html = ""
        if not self._is_move_open:
            move_html = format_move(self._current_move, relative_path="..")
            self._is_move_open = True
        self._markdown += f"| {move_html} | {attribute} | {old_field} | {new_field} | {format_checkbox(custom)} | {format_checkbox(la)} |\n"

    def parse_legends_arceus_moves(self, line: str) -> None:
        """Parse Legends: Arceus moves."""
        self.parse_redux_move_modifications(line)
