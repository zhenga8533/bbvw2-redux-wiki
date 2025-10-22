"""
Parser for Pokemon Changes documentation file.

This parser:
1. Reads data/documentation/Pokemon Changes.txt
2. Updates pokemon data in data/pokedb/parsed/
3. Generates a markdown file to docs/pokemon_changes.md
"""

from src.data.pokedb_loader import PokeDBLoader
from src.services.pokemon_service import PokemonService
from src.utils.markdown_util import format_move, format_pokemon, get_checkbox
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

        # Specific Changes states
        self._current_pokemon = ""
        self._current_forme = ""
        self._current_attribute = ""
        self._is_table_open = False
        self._temporary_markdown = ""

    def parse_general_notes(self, line: str) -> None:
        """Parse general notes section."""
        self.parse_default(line)

    def parse_type_changes(self, line: str) -> None:
        """Parse type changes section."""
        self.parse_default(line)

    def parse_specific_changes(self, line: str) -> None:
        """Parse specific changes section."""
        next_line = self.peek_line(1) or ""
        # Match: "<number> - <pokemon>"
        if match := re.match(r"^(\d{3}) - (.*)$", line):
            pokedex_number = match.group(1)
            self._current_pokemon = match.group(2)
            self._markdown += f"### #{pokedex_number} {self._current_pokemon}\n\n"
            self._markdown += f"{format_pokemon(self._current_pokemon)}<br>\n\n"
        # Match: "<attribute>:"
        elif line.endswith(":"):
            self._current_attribute = line[:-1]
            self._format_attribute(
                self._current_attribute, is_changed=next_line.startswith("Old")
            )
        # Match: "<level> - <move>"
        elif match := re.match(r"^(\d+) - (.*)$", line):
            level = match.group(1)
            move = match.group(2)
            self._format_move_row(level, move)
        # Match: "Old <value>" or "New <value>"
        elif line.startswith("Old") or line.startswith("New"):
            is_new = line.startswith("New")
            line = line[4:].strip()

            # Append to markdown table row
            self._markdown += f" {line} |"
            if not is_new:
                return
            self._markdown += "\n"

            # Update Pokemon attribute in JSON file
            PokemonService.update_attribute(
                pokemon=self._current_pokemon,
                attribute=self._current_attribute,
                value=line,
            )
        # Match: continuation outside a table
        elif self._is_table_open:
            if line:
                line = line.replace("[*]", "[\\*]")
                line = f"- {line}"
            self._temporary_markdown += f"{line}\n"
        # Default: regular text line
        else:
            self.parse_default(line)

    def _format_attribute(self, attribute: str, is_changed: bool) -> None:
        """Format an attribute change section."""
        changed_attributes = [
            "Base Stats",
            "Type",
            "Ability",
            "Base Happiness",
            "Base Experience",
            "EVs",
            "Catch Rate",
            "Gender Ratio",
        ]
        if is_changed and any(
            attribute.startswith(attr) for attr in changed_attributes
        ):
            if not self._is_table_open:
                self._is_table_open = True
                self._markdown += "| Attribute | Old Value | New Value |\n"
                self._markdown += "|:----------|:----------|:----------|\n"
            self._markdown += f"| **{self._current_attribute}** | "
            return

        static_attributes = ["Evolution", "Moves", "Held Item", "Growth Rate"]
        if self._is_table_open:
            self._temporary_markdown += f"**{attribute}**:\n\n"
        else:
            self._markdown += f"**{attribute}**:\n\n"

        if attribute.startswith("Level Up"):
            self._markdown += self._temporary_markdown
            self._temporary_markdown = ""
            self._is_table_open = False
            self._markdown += "| Level | Move | Type | Class | Event |\n"
            self._markdown += "|:------|:-----|:-----|:------|:------|\n"
        elif attribute in static_attributes:
            pass
        else:
            self.logger.warning(
                f"Unrecognized attribute '{attribute}' for Pokemon '{self._current_pokemon}'"
            )

    def _format_move_row(self, level: str, move: str) -> None:
        """Format a move row for markdown table."""
        event_move = False
        if move.endswith(" [*]"):
            move = move[:-4]
            event_move = True

        # Format move name
        move_html = format_move(move)

        # Load move data from PokeDB
        move_data = PokeDBLoader.load_move(move)
        move_type = move_data.type.black_2_white_2 if move_data else "Unknown"
        move_type = move_type.title() if move_type else "Unknown"
        move_class = move_data.damage_class.title() if move_data else "Unknown"

        self._markdown += f"| {level} | {move_html} | {move_type} | {move_class} | {get_checkbox(event_move)} |\n"
