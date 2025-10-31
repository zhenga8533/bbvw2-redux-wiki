"""
Parser for Evolution Changes documentation file.

This parser:
1. Reads data/documentation/Evolution Changes.txt
2. Updates pokemon evolution data in data/pokedb/parsed/
3. Generates a markdown file to docs/evolution_changes.md
"""

import re
from typing import Optional

from src.utils.text_util import name_to_id
from src.utils.markdown_util import format_pokemon, format_item
from src.models.pokedb import (
    EvolutionChain,
    EvolutionDetails,
    Gender,
)
from src.data.pokedb_loader import PokeDBLoader
from src.services.evolution_service import EvolutionService

from .base_parser import BaseParser


class EvolutionChangesParser(BaseParser):
    """
    Parser for Evolution Changes documentation.

    Extracts evolution method changes and updates Pokemon JSON files.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Evolution Changes parser."""
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = ["General Notes", "Evolution Changes"]

        # Evolution Changes states
        self._is_table_open: bool = False
        self._parsed_cache: set[tuple[str, str]] = set()  # Track (pokemon, evolution) pairs
        self._current_dex_num: str = ""
        self._current_pokemon: str = ""

    def parse_general_notes(self, line: str) -> None:
        """Parse a line from the General Notes section."""
        self.parse_default(line)

    def parse_evolution_changes(self, line: str) -> None:
        """Parse a line from the Evolution Changes section and update data."""
        # Match: table header "Pokémon              New Method"
        if line == "Pokémon              New Method":
            self._is_table_open = True
            self._markdown += "<table>\n  <thead>\n    <tr>\n"
            self._markdown += '      <th align="center">Dex #</th>\n'
            self._markdown += '      <th align="center">Pokémon</th>\n'
            self._markdown += '      <th align="center">Evolution</th>\n'
            self._markdown += '      <th align="left">New Method</th>\n'
            self._markdown += "    </tr>\n  </thead>\n"
        # Match: table separator "---                  ---"
        elif line == "---                  ---":
            self._markdown += "  <tbody>\n"
        # Match: "dex_num name (spaces) evolution_text"
        elif match := re.match(
            rf"^(\d+) ([A-Z][\w':.-]*(?:\s[A-Z][\w':.-]*)*)\s+(.*)", line
        ):
            self._current_dex_num, self._current_pokemon, evolution_text = (
                match.groups()
            )
            if result := self._extract_evolution_text(evolution_text):
                evolution, evolution_text = result
                self._add_evolution_row(evolution, evolution_text)
                self._update_evolution_method(evolution, evolution_text)
        # Match: continuation line with evolution text (same Pokemon as previous)
        elif line and self._current_pokemon:
            if result := self._extract_evolution_text(line.strip()):
                evolution, evolution_text = result
                self._add_evolution_row(evolution, evolution_text)
                self._update_evolution_method(evolution, evolution_text)
        # Unrecognized: log warning for unexpected format
        elif line:
            self.logger.warning(f"Unrecognized line format: '{line}'")
        # Match: empty line indicates end of table
        elif self._is_table_open:
            self._markdown += "  </tbody>\n</table>\n"
            self._is_table_open = False

    def _add_evolution_row(self, evolution: str, evolution_text: str) -> None:
        """
        Add an HTML table row to the evolution table.

        Args:
            evolution: Name of the evolution target Pokemon
            evolution_text: Description of the evolution method
        """
        # Format Pokemon with sprites and links
        from_pokemon_md = format_pokemon(self._current_pokemon)

        if evolution:
            to_pokemon_md = format_pokemon(evolution)
        else:
            to_pokemon_md = ""

        # Add HTML table row
        self._markdown += "    <tr>\n"
        # Dex # cell: center-aligned horizontally, middle-aligned vertically
        self._markdown += f'      <td align="center" style="vertical-align: middle;">{self._current_dex_num}</td>\n'

        # Pokémon cell: vertical-align: bottom (as requested)
        # format_pokemon() handles the inner div align="center"
        self._markdown += (
            f'      <td style="vertical-align: bottom;">{from_pokemon_md}</td>\n'
        )

        # Evolution cell: vertical-align: bottom (as requested)
        self._markdown += (
            f'      <td style="vertical-align: bottom;">{to_pokemon_md}</td>\n'
        )

        # New Method cell: left-aligned horizontally, middle-aligned vertically
        formatted_text = self._format_evolution_text(evolution_text)
        self._markdown += f'      <td align="left" style="vertical-align: middle;">{formatted_text}</td>\n'
        self._markdown += "    </tr>\n"

    def _format_evolution_text(self, text: str) -> str:
        """
        Format evolution text by replacing item names with formatted sprites.

        Args:
            text: The evolution method text (e.g., "Now evolves via the use of a Fire Stone")

        Returns:
            Formatted text with item sprites and names
        """

        def replace_item(match: re.Match[str]) -> str:
            """Replace item text with formatted item display."""
            item_name = match.group(1).strip()
            formatted = format_item(
                item_name, has_sprite=True, has_name=True, has_flavor_text=True
            )
            return f"via the use of {formatted}"

        formatted_text = re.sub(
            r"via the use of a(?:n)? (.+?)(?=\s+in addition|\s+if|$)",
            replace_item,
            text,
        )
        return formatted_text

    def _extract_evolution_text(self, text: str) -> Optional[tuple[str, str]]:
        """
        Extract evolution and method from text.

        Args:
            text: The evolution text to parse

        Returns:
            Tuple of (evolution_pokemon_name, evolution_method_text) or None if no match
        """
        if match := re.match(
            rf"Now evolves into ([A-Z][\w':.-]*(?:\s[A-Z][\w':.-]*)*) (.*)\.", text
        ):
            groups = match.groups()

            # Validate we have the expected number of groups
            if len(groups) >= 2:
                return groups[0].strip(), f"Now evolves {groups[1].strip()}"
            else:
                self.logger.warning(
                    f"Unexpected regex match format in evolution text: '{text}' "
                    f"(expected 2 groups, got {len(groups)})"
                )
                return None
        else:
            return None

    def _update_evolution_method(self, evolution: str, method_text: str) -> None:
        """Parse the evolution method text into structured data and update Pokemon."""

        if not evolution:
            return

        method_text = method_text[len("Now evolves ") :].rstrip(".")

        # Determine whether to ADD to existing evolution methods or REPLACE them.
        # Keep existing evolution methods if:
        # 1. The text explicitly says "in addition to its normal evolution method", OR
        # 2. We've already processed this (Pokemon, Evolution) pair (allows multiple methods to same target)
        evolution_pair = (self._current_pokemon, evolution)
        keep_existing = (
            "in addition to its normal evolution method" in method_text
            or evolution_pair in self._parsed_cache
        )
        method_text = method_text.replace(
            " in addition to its normal evolution method", ""
        )

        # Check for gender requirement
        gender = None
        if " if " in method_text and " is female" in method_text:
            gender = Gender.FEMALE
            method_text = re.sub(rf" if (.*) is female", "", method_text)
        elif " if " in method_text and " is male" in method_text:
            gender = Gender.MALE
            method_text = re.sub(rf" if (.*) is male", "", method_text)

        # Map of evolution method types to their pattern strings
        patterns = {
            "level": r"at Level (\d+)",
            "item": r"via the use of a(?:n)? (.+)",
            "friendship": r"by leveling up while at (\d+)\+ friendship at any time of day",
            "move": r"by leveling up while knowing the move (.+)",
            "party": rf"by leveling up when a (.*) is in the party",
        }

        # Load the Pokemon data
        pokemon_id = name_to_id(self._current_pokemon)
        evolution_id = name_to_id(evolution)

        pokemon_data = PokeDBLoader.load_pokemon(pokemon_id)
        if pokemon_data is None:
            self.logger.warning(f"Pokemon not found: {pokemon_id}")
            return

        evolution_chain: EvolutionChain = pokemon_data.evolution_chain
        evolution_details: EvolutionDetails = EvolutionDetails()

        matched = False

        # Try to match each known pattern
        for method_type, pattern in patterns.items():
            if match := re.match(pattern, method_text):
                matched = True

                if method_type == "level":
                    evolution_details.trigger = "level-up"
                    evolution_details.min_level = int(match.group(1))
                elif method_type == "item":
                    evolution_details.trigger = "use-item"
                    evolution_details.item = match.group(1).lower().replace(" ", "-")
                elif method_type == "friendship":
                    evolution_details.trigger = "level-up"
                    evolution_details.min_happiness = int(match.group(1))
                elif method_type == "move":
                    evolution_details.trigger = "level-up"
                    evolution_details.known_move = (
                        match.group(1).lower().replace(" ", "-")
                    )
                elif method_type == "party":
                    evolution_details.trigger = "level-up"
                    evolution_details.party_species = (
                        match.group(1).lower().replace(" ", "-")
                    )

                if gender:
                    evolution_details.gender = gender

                # Use the evolution service to update the chain
                EvolutionService.update_evolution_chain(
                    pokemon_id,
                    evolution_id,
                    evolution_chain,
                    evolution_details,
                    keep_existing,
                )

        if not matched:
            self.logger.warning(
                f"Unrecognized evolution method for {self._current_pokemon}: {method_text}"
            )
        else:
            self.logger.info(
                f"Updated evolution data for {self._current_pokemon} to {evolution} {method_text}"
            )
            self._parsed_cache.add(evolution_pair)
