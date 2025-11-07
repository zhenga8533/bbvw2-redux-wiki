"""
Parser for Pokemon Changes documentation file.

This parser:
1. Reads data/documentation/Pokemon Changes.txt
2. Updates pokemon data in data/pokedb/parsed/
3. Generates a markdown file to docs/pokemon_changes.md
"""

import re

from src.data.pokedb_loader import PokeDBLoader
from src.utils.core.config import VERSION_GROUP
from src.utils.formatters.markdown_formatter import (
    format_ability,
    format_checkbox,
    format_item,
    format_move,
    format_pokemon,
    format_pokemon_card_grid,
    format_type_badge,
)
from src.utils.services.pokemon_service import PokemonService

from .base_parser import BaseParser


class PokemonChangesParser(BaseParser):
    """Parser for Pokemon Changes documentation.

    Args:
        BaseParser (_type_): Abstract base parser class.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Pokemon Changes parser.

        Args:
            input_file (str): Path to the input file.
            output_dir (str, optional): Path to the output directory. Defaults to "docs".
        """
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

    def get_title(self) -> str:
        """Get the title for the Pokémon Changes section.

        Returns:
            str: Title of the Pokémon Changes section.
        """
        return "Pokémon Changes"

    def parse_general_notes(self, line: str) -> None:
        """Parse general notes section.

        Args:
            line (str): Line of text to parse.
        """
        self.parse_default(line)

    def parse_type_changes(self, line: str) -> None:
        """Parse type changes section.

        Args:
            line (str): Line of text to parse.
        """
        # Match: " - Gen X: Pokemon1, Pokemon2, ..."
        if line.startswith(" - Gen"):
            gen, pokemon = line[3:].split(": ")
            self._markdown += f"- **{gen}**: "
            self._markdown += ", ".join(
                format_pokemon(p, has_sprite=False) for p in pokemon.split(", ")
            )
            self._markdown += "\n"
        # Default: regular text line
        else:
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
        """Parse specific changes section.

        Args:
            line (str): Line of text to parse.
        """
        next_line = self.peek_line(1) or ""
        # Match: "<number> - <pokemon>"
        if match := re.match(r"^(\d{3}) - (.*)$", line):
            # Flush data from previous Pokemon
            self._flush_accumulated_data()

            pokedex_number = match.group(1)
            self._current_pokemon = match.group(2)
            self._current_forme = ""  # Reset forme for new Pokemon
            self._markdown += f"### #{pokedex_number} {self._current_pokemon}\n\n"
            self._markdown += format_pokemon_card_grid(
                [self._current_pokemon], relative_path="../pokedex/pokemon"
            )
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

            self._markdown += self._format_attribute(
                self._current_attribute, is_changed=next_line.startswith("Old")
            )
        # Match: "<level> - <move>"
        elif match := re.match(r"^(\d+) - (.*)$", line):
            level = match.group(1)
            move = match.group(2)
            self._markdown += self._format_move_row(level, move)
        # Match: "Old <value>" or "New <value>"
        elif line.startswith("Old") or line.startswith("New"):
            is_new = line.startswith("New")
            line = line[4:].strip()

            # Format the value if it's an ability or type
            formatted_value = line
            if self._current_attribute.startswith("Ability"):
                formatted_value = self._format_ability_value(line)
            elif self._current_attribute.startswith("Type"):
                formatted_value = self._format_type_value(line)

            # Append to markdown table row
            self._markdown += f" {formatted_value} |"
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
        # Match: special attribute continuation lines (Moves, Evolution, etc.)
        elif self._current_attribute in [
            "Moves",
            "Evolution",
            "Growth Rate",
            "Held Item",
        ]:
            # Parse special attribute lines and get formatted line
            formatted_line = line
            if self._current_attribute == "Moves" and line.startswith(
                "Now compatible with"
            ):
                formatted_line = self._parse_moves_line(line)
            elif self._current_attribute == "Growth Rate" and line.startswith("Now"):
                formatted_line = self._parse_growth_rate_line(line)
            elif self._current_attribute == "Held Item" and line.startswith("Now"):
                formatted_line = self._parse_held_item_line(line)
            # Evolution is handled by evolution_changes_parser, just display as-is

            # Use formatted_line for markdown output
            if formatted_line:
                # Note: [*] escaping is already handled in parse methods
                formatted_line = f"- {formatted_line}"

            # Add to appropriate markdown buffer
            if self._is_table_open:
                self._temporary_markdown += f"{formatted_line}\n"
            else:
                self._markdown += f"{formatted_line}\n"
        # Match: continuation inside a table (but not special attributes)
        elif self._is_table_open:
            if line:
                line = line.replace("[*]", "[\\*]")
                line = f"- {line}"
            self._temporary_markdown += f"{line}\n"
        # Default: regular text line
        else:
            self.parse_default(line)

    def _format_attribute(self, attribute: str, is_changed: bool) -> str:
        """Format an attribute change section.

        Args:
            attribute (str): Attribute name
            is_changed (bool): Whether the attribute has changed.

        Returns:
            str: Formatted markdown for the attribute change section.
        """
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
        md = ""

        if is_changed and any(
            attribute.startswith(attr) for attr in changed_attributes
        ):
            if not self._is_table_open:
                self._is_table_open = True
                md += "| Attribute | Old Value | New Value |\n"
                md += "|:----------|:----------|:----------|\n"
            md += f"| **{self._current_attribute}** | "
            return md

        static_attributes = ["Evolution", "Moves", "Held Item", "Growth Rate"]
        if self._is_table_open:
            self._temporary_markdown += f"**{attribute}**:\n\n"
        else:
            md += f"**{attribute}**:\n\n"

        if attribute.startswith("Level Up"):
            md += self._temporary_markdown
            self._temporary_markdown = ""
            self._is_table_open = False
            md += "| Level | Move | Type | Class | Event |\n"
            md += "|:------|:-----|:-----|:------|:------|\n"
        elif attribute in static_attributes:
            pass
        else:
            self.logger.warning(
                f"Unrecognized attribute '{attribute}' for Pokemon '{self._current_pokemon}'"
            )

        return md

    def _format_move_row(self, level: str, move: str) -> str:
        """Format a move row for markdown table.

        Args:
            level (str): Level at which the move is learned.
            move (str): Name of the move.

        Returns:
            str: Formatted markdown table row.
        """
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
        move_type = getattr(move_data.type, VERSION_GROUP, None) if move_data else None
        move_type = move_type.title() if move_type else "Unknown"
        move_class = move_data.damage_class.title() if move_data else "Unknown"

        md = f"| {level} | {move_html} | {format_type_badge(move_type)} | {move_class} | {format_checkbox(event_move)} |\n"
        return md

    def _parse_moves_line(self, line: str) -> str:
        """Parse TM/HM compatibility line and update Pokemon JSON.

        Args:
            line (str): Line to parse.

        Returns:
            str: Formatted line with linked TM/HM for markdown output
        """
        # Skip move tutor lines (not TM/HM) - return original line
        if "Move Tutor" in line:
            return line

        # Pattern: "Now compatible with TM56, Weather Ball." or "... [*]"
        match = re.match(
            r"^Now compatible with (TM|HM)(\d+), (.*?)\.(?: \[\*\])?$", line
        )
        if not match:
            self.logger.warning(f"Could not parse Moves line: {line}")
            return line  # Return original line on parse failure

        machine_type = match.group(1)  # "TM" or "HM"
        number = match.group(2)  # "56"
        move_name = match.group(3)  # "Weather Ball" or "False Swipe"

        # Accumulate TM/HM move data
        self._tm_hm_moves.append((machine_type, number, move_name))

        # Format the line with links for markdown output
        tm_item = format_item(f"{machine_type}{number} {move_name}")
        formatted_line = f"Now compatible with {tm_item}."

        # Check if this was an event move
        if line.endswith("[*]"):
            formatted_line += " [\\*]"

        return formatted_line

    def _parse_held_item_line(self, line: str) -> str:
        """Parse held item line and update Pokemon JSON.

        Args:
            line (str): Line to parse.

        Returns:
            str: Formatted line with linked item for markdown output
        """
        # Pattern: "Now holds a <item> with a <percent>% rate."
        match = re.match(r"^Now holds a (.*?) with a (\d+)% rate\.$", line)
        if not match:
            self.logger.warning(f"Could not parse Held Item line: {line}")
            return line  # Return original line on parse failure

        item_name = match.group(1)  # "Griseous Orb"
        rarity = int(match.group(2))  # 100

        # Update held item immediately (no accumulation needed)
        PokemonService.update_held_item(
            pokemon=self._current_pokemon,
            item_name=item_name,
            rarity=rarity,
            forme=self._current_forme,
        )

        # Format the line with linked item for markdown output
        item_html = format_item(item_name)
        formatted_line = f"Now holds a {item_html} with a {rarity}% rate."

        return formatted_line

    def _parse_growth_rate_line(self, line: str) -> str:
        """Parse growth rate line and update Pokemon JSON.

        Args:
            line (str): Line to parse.

        Returns:
            str: Original line (no formatting changes for now)
        """
        # Pattern: "Now part of the '<growth_rate>' experience growth group (...)"
        match = re.match(r"^Now part of the '([^']+)' experience growth group", line)
        if not match:
            self.logger.warning(f"Could not parse Growth Rate line: {line}")
            return line  # Return original line on parse failure

        growth_rate = match.group(1)  # "fast", "medium-fast", "slow", etc.

        # Update growth rate immediately (no accumulation needed)
        PokemonService.update_attribute(
            pokemon=self._current_pokemon,
            attribute="growth_rate",
            value=growth_rate,
            forme=self._current_forme,
        )

        return line

    def _format_ability_value(self, ability_text: str) -> str:
        """Format ability value with links to individual abilities.

        Args:
            ability_text (str): Ability string in format "Ability1 / Ability2 / Ability3"

        Returns:
            str: Formatted ability string with links
        """
        if not ability_text or ability_text.strip() == "":
            return ability_text

        # Split by " / " and format each ability
        abilities = [a.strip() for a in ability_text.split("/")]
        formatted_abilities = [
            format_ability(ability, is_linked=True) for ability in abilities
        ]

        return " / ".join(formatted_abilities)

    def _format_type_value(self, type_text: str) -> str:
        """Format type value with links to individual types.

        Args:
            type_text (str): Type string in format "Type1 / Type2"

        Returns:
            str: Formatted type string with links
        """
        type1, type2 = (
            type_text.split(" / ") if " / " in type_text else (type_text, None)
        )

        formatted_type1 = format_type_badge(type1.strip())
        if type2:
            formatted_type2 = format_type_badge(type2.strip())
            return f"{formatted_type1} {formatted_type2}"

        return formatted_type1
