"""
Parser for Move Changes documentation file.

This parser:
1. Reads data/documentation/Move Changes.txt
2. Updates move data in data/pokedb/parsed/
3. Generates a markdown file to docs/move_changes.md
"""

from src.utils.markdown_util import format_move
from src.services.move_service import MoveService
from .base_parser import BaseParser
import re


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

            old_move_html = format_move(old_move)
            new_move_html = format_move(new_move)
            self._markdown += f"| {old_move_html} | {new_move_html} |\n"
        # Default: regular text line
        else:
            self.parse_default(line)

    def parse_type_changes(self, line: str) -> None:
        """Parse type changes."""
        self.parse_default(line)

    def parse_redux_move_modifications(self, line: str) -> None:
        """Parse Redux move modifications."""
        self.parse_default(line)

    def parse_legends_arceus_moves(self, line: str) -> None:
        """Parse Legends: Arceus moves."""
        self.parse_default(line)
