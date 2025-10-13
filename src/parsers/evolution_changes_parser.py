"""
Parser for Evolution Changes documentation file.

This parser:
1. Reads data/documentation/Evolution Changes.txt
2. Updates pokemon evolution data in data/pokedb/parsed/
3. Generates a markdown file to docs/evolution_changes.md
"""

import re

from src.utils.constants import POKEMON_PATTERN
from src.utils.text_utils import name_to_id
from src.models.pokedb import (
    EvolutionChain,
    EvolutionDetails,
    Pokemon,
)
from src.data.pokedb_loader import PokeDBLoader
from src.services.evolution_service import EvolutionService

from .base_parser import BaseParser


class EvolutionChangesParser(BaseParser):
    """
    Parser for Evolution Changes documentation.

    Extracts evolution method changes and updates Pokemon JSON files.
    """

    _SECTIONS = ["General Notes", "Evolution Changes"]

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Evolution Changes parser."""
        super().__init__(input_file=input_file, output_dir=output_dir)

        # Initialize instance variables to avoid shared state between parser instances
        self._parsed_data: dict = {}
        self._current_section: str = ""
        self._current_dex_num: str = ""
        self._current_pokemon: str = ""

    def handle_section_change(self, new_section: str) -> None:
        """Handle logic when changing sections, if needed."""
        self._current_section = new_section

        if new_section == "Evolution Changes":
            self._markdown += "| Dex Num | Pokémon | Evolution | New Method |\n"
            self._markdown += "|---------|:-------:|-----------|------------|\n"

    def parse_general_notes(self, line: str) -> None:
        """Parse a line from the General Notes section."""
        self._markdown += f"{line}\n"

    def parse_evolution_change(self, line: str) -> None:
        """Parse a line from the Evolution Changes section and update data."""

        # Matches: dex_num name (spaces) evolution_text
        pattern = rf"^(\d+) {POKEMON_PATTERN}\s+(.*)"

        if match := re.match(pattern, line):
            self._current_dex_num, self._current_pokemon, evolution_text = (
                match.groups()
            )
            evolution, evolution_text = self.parse_evolution_text(evolution_text)
            self._markdown += f"| {self._current_dex_num} | {self._current_pokemon} | {evolution} | {evolution_text} |\n"
            self.parse_evolution_method(evolution, evolution_text)
        elif line and self._current_pokemon:
            evolution, evolution_text = self.parse_evolution_text(line)
            self._markdown += f"| {self._current_dex_num} | {self._current_pokemon} | {evolution} | {evolution_text} |\n"
            self.parse_evolution_method(evolution, evolution_text)

    def parse_evolution_text(self, text: str) -> tuple[str, str]:
        """
        Extract evolution and method from text.

        Args:
            text: The evolution text to parse

        Returns:
            Tuple of (evolution_pokemon_name, evolution_method_text)
            Returns ("", "") if the text doesn't match the expected pattern
        """
        pattern = rf"Now evolves into {POKEMON_PATTERN} (.*)\."
        if match := re.match(pattern, text):
            groups = match.groups()

            # Validate we have the expected number of groups
            if len(groups) >= 2:
                return groups[0].strip(), f"Now evolves {groups[1].strip()}"
            else:
                self.logger.warning(
                    f"Unexpected regex match format in evolution text: '{text}' "
                    f"(expected 2 groups, got {len(groups)})"
                )
                return "", ""
        else:
            return "", ""

    def parse_evolution_method(self, evolution: str, method_text: str) -> None:
        """Parse the evolution method text into structured data and update Pokemon."""

        if not evolution:
            return

        method_text = method_text[len("Now evolves ") :].rstrip(".")

        # Check for "in addition to" clause
        keep_existing = (
            "in addition to its normal evolution method" in method_text
            or self._current_pokemon in self._parsed_data
        )
        method_text = method_text.replace(
            " in addition to its normal evolution method", ""
        )

        # Check for gender requirement
        gender = None
        if " if " in method_text and " is female" in method_text:
            gender = 1
            method_text = re.sub(rf" if {POKEMON_PATTERN} is female", "", method_text)
        elif " if " in method_text and " is male" in method_text:
            gender = 0
            method_text = re.sub(rf" if {POKEMON_PATTERN} is male", "", method_text)

        patterns = {
            "level": r"at Level (\d+)",
            "item": r"via the use of a(?:n)? (.+)",
            "friendship": r"by leveling up while at (\d+)\+ friendship at any time of day",
            "move": r"by leveling up while knowing the move (.+)",
            "party": rf"by leveling up when a {POKEMON_PATTERN} is in the party",
        }

        # Load the Pokemon data
        pokemon_id = name_to_id(self._current_pokemon)
        evolution_id = name_to_id(evolution)

        try:
            pokemon_data: Pokemon = PokeDBLoader.load_pokemon(pokemon_id)
        except FileNotFoundError:
            self.logger.error(f"Pokemon not found: {pokemon_id}")
            return

        # Validate that the evolution target exists
        try:
            PokeDBLoader.load_pokemon(evolution_id)
        except FileNotFoundError:
            self.logger.warning(
                f"Evolution target '{evolution}' (id: {evolution_id}) not found. "
                f"Evolution chain will still be updated for {self._current_pokemon}."
            )

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
            self._parsed_data[pokemon_id] = {
                "pokemon": self._current_pokemon,
                "evolution": evolution,
                "method": method_text,
            }

    def parse(self) -> None:
        """Parse the Evolution Changes documentation file."""

        input_lines = self.read_input_lines()
        self._markdown = "# Evolution Changes\n\n"

        for line in input_lines:
            if line in self._SECTIONS:
                self._markdown += f"## {line}\n\n"
                self.handle_section_change(line)
            elif self._current_section == "General Notes":
                self.parse_general_notes(line)
            elif self._current_section == "Evolution Changes":
                self.parse_evolution_change(line)
