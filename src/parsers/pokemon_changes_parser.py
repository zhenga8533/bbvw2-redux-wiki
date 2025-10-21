"""
Parser for Pokemon Changes documentation file.

This parser:
1. Reads data/documentation/Pokemon Changes.txt
2. Updates pokemon data in data/pokedb/parsed/
3. Generates a markdown file to docs/pokemon_changes.md
"""

from src.data.pokedb_loader import PokeDBLoader
from src.utils.markdown_util import format_move, format_pokemon
from .base_parser import BaseParser
import re


class PokemonChangesParser(BaseParser):
    """
    Parser for Pokemon Changes documentation.

    Extracts Pokemon changes and updates Pokemon JSON files.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Pokemon Changes parser."""
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = [
            "General Notes",
            "Type Changes",
            "Specific Changes",
        ]

        self._current_pokemon = ""

    def parse_general_notes(self, line: str) -> None:
        """Parse general notes section."""
        self.parse_default(line)

    def parse_type_changes(self, line: str) -> None:
        """Parse type changes section."""
        self.parse_default(line)

    def parse_specific_changes(self, line: str) -> None:
        """Parse specific changes section."""
        # Match: "<number> - <pokemon>"
        if match := re.match(r"^(\d{3}) - (.*)$", line):
            pokedex_number = match.group(1)
            self._current_pokemon = match.group(2)
            self._markdown += f"### #{pokedex_number} {self._current_pokemon}\n\n"
            self._markdown += format_pokemon(self._current_pokemon) + "\n\n"
        # Match: "<attribute>:"
        elif line.endswith(":"):
            attribute = line[:-1]
            self._format_attribute_change(attribute)
        # Match: "<level> - <move>"
        elif match := re.match(r"^(\d+) - (.*)$", line):
            level = match.group(1)
            move = match.group(2)
            self._format_move_row(level, move)
        # Default: regular text line
        else:
            self.parse_default(line)

    def _format_attribute_change(self, attribute: str) -> None:
        """Format an attribute change section."""
        self._markdown += f"**{attribute}**:\n\n"

        if attribute == "Level Up":
            self._markdown += "| Level | Move | Type | Class | Event |\n"
            self._markdown += "|:------|:-----|:-----|:------|:------|\n"

    def _format_move_row(self, level: str, move: str) -> None:
        """Format a move row for markdown table."""
        # Format event move checkbox
        event_move = '<input type="checkbox" disabled>'
        if move.endswith(" [*]"):
            move = move[:-4]
            event_move = '<input type="checkbox" checked disabled>'

        # Format move name
        move_html = format_move(move)

        # Load move data from PokeDB
        move_data = PokeDBLoader.load_move(move)
        move_type = move_data.type.black_2_white_2 if move_data else "Unknown"
        move_type = move_type.title() if move_type else "Unknown"
        move_class = move_data.damage_class.title() if move_data else "Unknown"

        self._markdown += (
            f"| {level} | {move_html} | {move_type} | {move_class} | {event_move} |\n"
        )
