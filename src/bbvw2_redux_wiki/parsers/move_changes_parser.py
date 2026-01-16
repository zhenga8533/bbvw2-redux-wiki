"""
Parser for Move Changes documentation file.

This parser:
1. Reads data/documentation/Move Changes.txt
2. Updates move data in data/pokedb/parsed/
3. Generates a markdown file to docs/move_changes.md
"""

import re

import orjson
from rom_wiki_core.parsers.base_parser import BaseParser
from rom_wiki_core.utils.core.loader import PokeDBLoader
from rom_wiki_core.utils.formatters.markdown_formatter import (
    format_checkbox,
    format_move,
    format_type_badge,
)
from rom_wiki_core.utils.services.move_service import MoveService
from rom_wiki_core.utils.text.text_util import name_to_id


class MoveChangesParser(BaseParser):
    """Parser for Move Changes documentation.

    Args:
        BaseParser (_type_): Abstract base parser class.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Move Changes parser.

        Args:
            input_file (str): Path to the input file.
            output_dir (str, optional): Path to the output directory. Defaults to "docs".
        """
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

    def _update_all_moves_to_gen8(self) -> None:
        """Update all existing moves in parsed data to match gen8 stats.

        This method:
        1. Loads all moves from gen8 source data
        2. For each move that exists in parsed data, updates its stats to match gen8
        3. Skips moves that don't exist in parsed data (they'll be copied separately)

        Updates the following attributes:
        - Power
        - Accuracy
        - PP
        - Priority
        - Effect Chance
        """
        # Get the data directory
        data_dir = PokeDBLoader.get_data_dir()

        # Get gen8 source directory
        source_gen = self.config.pokedb_generations[-1]
        source_move_dir = data_dir.parent / source_gen / "move"
        parsed_move_dir = data_dir / "move"

        if not source_move_dir.exists():
            self.logger.warning(f"Gen8 source directory not found: {source_move_dir}")
            return

        if not parsed_move_dir.exists():
            self.logger.warning(f"Parsed move directory not found: {parsed_move_dir}")
            return

        # Iterate over all moves in parsed data
        updated_count = 0
        skipped_count = 0

        for move_file in parsed_move_dir.glob("*.json"):
            move_id = move_file.stem
            source_file = source_move_dir / f"{move_id}.json"

            # Skip if move doesn't exist in gen8
            if not source_file.exists():
                skipped_count += 1
                continue

            # Load both moves
            move = PokeDBLoader.load_move(move_id)
            if move is None:
                skipped_count += 1
                continue

            # Load gen8 source data
            try:
                with open(source_file, "rb") as f:
                    gen8_data = orjson.loads(f.read())
            except (OSError, IOError, ValueError) as e:
                self.logger.warning(f"Error loading gen8 data for {move_id}: {e}")
                skipped_count += 1
                continue

            # Helper function to extract value from gen8 data
            def get_gen8_value(field_data):
                """Extract the most recent value from gen8 field data."""
                if isinstance(field_data, dict):
                    # Get the last version group's value (most recent in gen8)
                    return list(field_data.values())[-1]
                return field_data

            # Update attributes from gen8
            # Note: We only update if the attribute exists in gen8 data
            if "power" in gen8_data:
                gen8_value = get_gen8_value(gen8_data["power"])
                for version_key in move.power.keys():
                    setattr(move.power, version_key, gen8_value)

            if "accuracy" in gen8_data:
                gen8_value = get_gen8_value(gen8_data["accuracy"])
                for version_key in move.accuracy.keys():
                    setattr(move.accuracy, version_key, gen8_value)

            if "pp" in gen8_data:
                gen8_value = get_gen8_value(gen8_data["pp"])
                for version_key in move.pp.keys():
                    setattr(move.pp, version_key, gen8_value)

            if "priority" in gen8_data:
                move.priority = gen8_data["priority"]

            if "effect_chance" in gen8_data:
                gen8_value = get_gen8_value(gen8_data["effect_chance"])
                for version_key in move.effect_chance.keys():
                    setattr(move.effect_chance, version_key, gen8_value)

            # Save the updated move
            PokeDBLoader.save_move(move_id, move)
            updated_count += 1

        self.logger.info(
            f"Updated {updated_count} moves to gen8 stats (skipped {skipped_count})"
        )

    def handle_section_change(self, new_section: str) -> None:
        """Handle state reset on section change.

        Args:
            new_section (str): The new section being parsed.
        """

        if new_section == "General Changes":
            self._update_all_moves_to_gen8()

        if self._is_table_open:
            self._is_table_open = False
            self._markdown += "\n"
        self._current_move = ""
        return super().handle_section_change(new_section)

    def parse_general_changes(self, line: str) -> None:
        """Parse general move changes.

        Args:
            line (str): Line of text to parse.
        """
        self.parse_default(line)

    def parse_move_replacements(self, line: str) -> None:
        """Parse move replacements.

        Args:
            line (str): Line of text to parse.
        """
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

            # Copy the new move from latest generation to parsed data
            MoveService.copy_new_move(new_move)

            old_move_html = format_move(old_move)
            new_move_html = format_move(new_move)
            self._markdown += f"| {old_move_html} | {new_move_html} |\n"
        # Default: regular text line
        else:
            self.parse_default(line)

    def parse_type_changes(self, line: str) -> None:
        """Parse type changes.

        Args:
            line (str): Line of text to parse.
        """
        next_line = self.peek_line(1) or ""
        # Match: "<move_name>"
        if next_line.startswith(" - "):
            self._current_move = line
            if not self._is_table_open:
                self._is_table_open = True
                self._markdown += "| Move | Old Type | New Type | Custom |\n"
                self._markdown += "|:-----|:---------|:--------:|:------:|\n"
            self._markdown += f"| {format_move(self._current_move)} "
        # Match: " - <old_type> -> <new_type>"
        elif line.startswith(" - "):
            old_type, new_type = line[3:].split(" -> ")
            custom = False
            if new_type.endswith(" [!]"):
                new_type = new_type[:-4]
                custom = True

            # Update the move's type in the data
            MoveService.update_move_type(
                move_id=name_to_id(self._current_move),
                type_id=name_to_id(new_type),
            )

            self._markdown += f"| {format_type_badge(old_type)} | {format_type_badge(new_type)} | {format_checkbox(custom)} |"
        # Default: regular text line
        else:
            self.parse_default(line)

    def parse_redux_move_modifications(self, line: str) -> None:
        """Parse Redux move modifications.

        Args:
            line (str): Line of text to parse.
        """
        next_line = self.peek_line(1) or ""
        # Match: " - <old_type> -> <new_type>"
        if line.startswith(" - "):
            self._markdown += self._format_move_row(line[3:])
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

    def _format_move_row(self, line: str) -> str:
        """Format a move row for markdown table.

        Args:
            line (str): Line containing move attribute change.

        Returns:
            str: Formatted markdown table row.
        """
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

        new_field = new_field.strip("*")

        # Update move data if attribute is supported
        move_id = name_to_id(self._current_move)
        if attribute == "Power":
            power = int(new_field) if new_field != "—" else None
            MoveService.update_move_power(move_id, power)
        elif attribute == "PP":
            MoveService.update_move_pp(move_id, int(new_field))
        elif attribute == "Priority":
            priority = new_field.strip("+")
            MoveService.update_move_priority(move_id, int(priority))
        elif attribute == "Accuracy":
            accuracy = int(new_field) if "Never Miss" not in new_field else None
            MoveService.update_move_accuracy(move_id, accuracy)
        elif attribute == "Type":
            MoveService.update_move_type(move_id, name_to_id(new_field))

        # Add to markdown table
        move_html = "└──"
        if not self._is_move_open:
            move_html = format_move(self._current_move)
            self._is_move_open = True

        md = f"| {move_html} | {attribute} | {old_field} | {new_field} | {format_checkbox(custom)} | {format_checkbox(la)} |\n"
        return md

    def parse_legends_arceus_moves(self, line: str) -> None:
        """Parse Legends: Arceus moves.

        Args:
            line (str): Line of text to parse.
        """
        self.parse_redux_move_modifications(line)
