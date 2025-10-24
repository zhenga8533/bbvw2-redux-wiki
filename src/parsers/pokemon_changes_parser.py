"""
Parser for Pokemon Changes documentation file.

This parser:
1. Reads data/documentation/Pokemon Changes.txt
2. Updates pokemon data in data/pokedb/parsed/
3. Generates a markdown file to docs/pokemon_changes.md
"""

from src.data.pokedb_loader import PokeDBLoader
from src.services.pokemon_service import PokemonService
from src.utils.markdown_util import format_move, format_pokemon, format_checkbox
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
        self._current_forme = ""  # Store current forme (e.g., "attack", "defense")
        self._current_attribute = ""
        self._is_table_open = False
        self._temporary_markdown = ""

        # Data accumulation for multi-line attributes
        self._levelup_moves = []  # List of (level, move_name) tuples
        self._tm_hm_moves = []  # List of (machine_type, number, move_name) tuples

    def parse_general_notes(self, line: str) -> None:
        """Parse general notes section."""
        self.parse_default(line)

    def parse_type_changes(self, line: str) -> None:
        """Parse type changes section."""
        self.parse_default(line)

    def _flush_accumulated_data(self) -> None:
        """Flush accumulated data (level-up moves, TMs) to Pokemon JSON."""
        if not self._current_pokemon:
            return

        # Update level-up moves if we have any
        if self._levelup_moves:
            PokemonService.update_levelup_moves(
                pokemon=self._current_pokemon,
                moves=self._levelup_moves,
                forme=self._current_forme,
            )
            self._levelup_moves = []

        # Update TM/HM moves if we have any
        if self._tm_hm_moves:
            PokemonService.update_machine_moves(
                pokemon=self._current_pokemon,
                moves=self._tm_hm_moves,
                forme=self._current_forme,
            )
            self._tm_hm_moves = []

    def parse_specific_changes(self, line: str) -> None:
        """Parse specific changes section."""
        next_line = self.peek_line(1) or ""
        # Match: "<number> - <pokemon>"
        if match := re.match(r"^(\d{3}) - (.*)$", line):
            # Flush data from previous Pokemon
            self._flush_accumulated_data()

            pokedex_number = match.group(1)
            self._current_pokemon = match.group(2)
            self._current_forme = ""  # Reset forme for new Pokemon
            self._markdown += f"### #{pokedex_number} {self._current_pokemon}\n\n"
            self._markdown += f"{format_pokemon(self._current_pokemon)}\n\n"
        # Match: "<attribute>:"
        elif line.endswith(":"):
            # Flush accumulated data from previous attribute if needed
            if self._current_attribute.startswith("Level Up"):
                self._flush_accumulated_data()

            self._current_attribute = line[:-1]

            # Extract forme from attribute if present
            # Pattern: "Ability (Complete / Attack Forme)" -> "attack"
            if " Forme)" in self._current_attribute:
                forme_match = re.search(
                    r"/ ([A-Za-z\s]+) Forme\)", self._current_attribute
                )
                if forme_match:
                    # Convert "Attack Forme" to "attack", "Normal Forme" to "normal"
                    forme_name = forme_match.group(1).strip().lower()
                    # Handle special cases: "Regular" becomes base forme (empty string)
                    self._current_forme = "" if forme_name == "regular" else forme_name
                else:
                    self._current_forme = ""

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
                forme=self._current_forme,
            )
        # Match: continuation outside a table
        elif self._is_table_open:
            # Parse special attribute lines
            if self._current_attribute == "Moves" and line.startswith(
                "Now compatible with"
            ):
                self._parse_moves_line(line)
            elif self._current_attribute == "Evolution" and line.startswith("Now"):
                self._parse_evolution_line(line)
            elif self._current_attribute == "Growth Rate" and line.startswith("Now"):
                self._parse_growth_rate_line(line)
            elif self._current_attribute == "Held Item" and line.startswith("Now"):
                self._parse_held_item_line(line)

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

        # Accumulate level-up move data
        self._levelup_moves.append((int(level), move))

        # Format move name
        move_html = format_move(move)

        # Load move data from PokeDB
        move_data = PokeDBLoader.load_move(move)
        move_type = move_data.type.black_2_white_2 if move_data else "Unknown"
        move_type = move_type.title() if move_type else "Unknown"
        move_class = move_data.damage_class.title() if move_data else "Unknown"

        self._markdown += f"| {level} | {move_html} | {move_type} | {move_class} | {format_checkbox(event_move)} |\n"

    def _parse_moves_line(self, line: str) -> None:
        """
        Parse TM/HM compatibility line and update Pokemon JSON.

        Formats:
        - "Now compatible with TM56, Weather Ball."
        - "Now compatible with TM54, False Swipe. [*]"
        - "Now compatible with Draco Meteor from the Move Tutor." (ignored)
        """
        # Skip move tutor lines (not TM/HM)
        if "Move Tutor" in line:
            return

        # Pattern: "Now compatible with TM56, Weather Ball." or "... [*]"
        match = re.match(
            r"^Now compatible with (TM|HM)(\d+), (.*?)\.(?: \[\*\])?$", line
        )
        if not match:
            self.logger.warning(f"Could not parse Moves line: {line}")
            return

        machine_type = match.group(1)  # "TM" or "HM"
        number = match.group(2)  # "56"
        move_name = match.group(3)  # "Weather Ball" or "False Swipe"

        # Accumulate TM/HM move data
        self._tm_hm_moves.append((machine_type, number, move_name))

    def _parse_held_item_line(self, line: str) -> None:
        """
        Parse held item line and update Pokemon JSON.

        Format: "Now holds a Griseous Orb with a 100% rate."
        """
        # Pattern: "Now holds a <item> with a <percent>% rate."
        match = re.match(r"^Now holds a (.*?) with a (\d+)% rate\.$", line)
        if not match:
            self.logger.warning(f"Could not parse Held Item line: {line}")
            return

        item_name = match.group(1)  # "Griseous Orb"
        rarity = int(match.group(2))  # 100

        # Update held item immediately (no accumulation needed)
        PokemonService.update_held_item(
            pokemon=self._current_pokemon,
            item_name=item_name,
            rarity=rarity,
            forme=self._current_forme,
        )

    def _parse_evolution_line(self, line: str) -> None:
        """
        Parse evolution line (display-only, no JSON update).

        Various formats:
        - "Now evolves into Fearow at Level 21."
        - "Now able to evolve into Golduck at level 25."
        - "Now able to evolve into Politoed by using a King's Rock."
        - "Now evolves into Cherrim when happy regardless of the time."
        - etc.
        """
        # Evolution data is complex and would require significant refactoring
        # of the evolution_chain structure. For now, this is display-only.
        # Log for debugging purposes
        self.logger.debug(f"Evolution line (display-only): {line}")

    def _parse_growth_rate_line(self, line: str) -> None:
        """
        Parse growth rate line (display-only, no JSON update).

        Format: "Now part of the 'fast' experience growth group (800,000 Exp to level 100)."
        """
        # Growth rate is not stored in the Pokemon JSON (no field for it).
        # This is display-only information.
        # Log for debugging purposes
        self.logger.debug(f"Growth rate line (display-only): {line}")
