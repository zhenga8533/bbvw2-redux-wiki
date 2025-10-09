"""
Parser for Evolution Changes documentation file.

This parser:
1. Reads data/documentation/Evolution Changes.txt
2. Updates pokemon evolution data in data/pokedb/parsed/
3. Generates a markdown file to docs/evolution_changes.md
"""

import re
from typing import Any, Dict, List, Optional

from src.utils.constants import POKEMON_PATTERN
from src.utils.pokedb_structure import (
    EvolutionChain,
    EvolutionDetails,
    EvolutionNode,
    Pokemon,
)
from src.utils.text_utils import name_to_id
from src.services.evolution_service import EvolutionService

from .base_parser import BaseParser
from ..utils.pokedb_loader import PokeDBLoader


class EvolutionChangesParser(BaseParser):
    """
    Parser for Evolution Changes documentation.

    Extracts evolution method changes and updates Pokemon JSON files.
    """

    _SECTIONS = ["General Notes", "Evolution Changes"]

    _current_section: str = ""
    _current_dex_num: str = ""
    _current_pokemon: str = ""

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Evolution Changes parser."""
        super().__init__(
            input_file=input_file, output_dir=output_dir, log_file=__file__
        )
        self.loader = PokeDBLoader(use_parsed=True)

    def handle_section_change(self, new_section: str) -> None:
        """Handle logic when changing sections, if needed."""
        self._current_section = new_section

        if new_section == "Evolution Changes":
            self._markdown += "| Dex Num | Pokémon | Evolution | New Method |\n"
            self._markdown += "|---------|:-------:|-----------|------------|\n"
            self._parsed_data["evolution_changes"] = {}

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
        """Extract evolution and method from text."""
        pattern = rf"Now evolves into {POKEMON_PATTERN} (.*)\."
        if match := re.match(pattern, text):
            groups = match.groups()
            return groups[0].strip(), f"Now evolves {groups[1].strip()}"
        else:
            return "", ""

    def parse_evolution_method(self, evolution: str, method_text: str) -> None:
        """Parse the evolution method text into structured data and update Pokemon."""

        if not evolution:
            return

        method_text = method_text[len("Now evolves ") :].rstrip(".")

        # Check for "in addition to" clause
        keep_existing = "in addition to its normal evolution method" in method_text
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
            pokemon_data: Pokemon = self.loader.load_pokemon(pokemon_id)
        except FileNotFoundError:
            self.logger.error(f"Pokemon not found: {pokemon_id}")
            return

        # Validate that the evolution target exists
        try:
            self.loader.load_pokemon(evolution_id)
        except FileNotFoundError:
            self.logger.warning(
                f"Evolution target '{evolution}' (id: {evolution_id}) not found. "
                f"Evolution chain will still be updated for {self._current_pokemon}."
            )

        evolution_chain: EvolutionChain = pokemon_data.evolution_chain
        evolution_details: EvolutionDetails = EvolutionDetails()

        matched = False
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
                    evolution_chain,
                    pokemon_id,
                    evolution_id,
                    evolution_details,
                    keep_existing,
                )

        if not matched:
            self.logger.warning(
                f"Unrecognized evolution method for {self._current_pokemon}: {method_text}"
            )
        else:
            self._save_evolution_data(
                pokemon_id, evolution_chain, evolution_chain.evolves_to
            )

    def _save_evolution_data(
        self,
        pokemon_id: str,
        evolution_chain: EvolutionChain,
        evolves_to: List[EvolutionNode],
        check_forms: bool = True,
        subfolder: str = "default",
    ) -> None:
        """Recursively save updated pokemon data."""
        # When recursing to evolved forms, always use "default" subfolder
        # because evolved forms are typically in the default folder
        for evolution in evolves_to:
            self._save_evolution_data(
                evolution.species_name,
                evolution_chain,
                evolution.evolves_to,
                check_forms=False,
                subfolder="default",  # Always use default for evolved forms
            )

        try:
            pokemon_data = self.loader.load_pokemon(pokemon_id, subfolder=subfolder)
            pokemon_data.evolution_chain = evolution_chain
            path = self.loader.save_pokemon(pokemon_id, pokemon_data, subfolder=subfolder)

            if check_forms:
                for form in pokemon_data.forms:
                    # Skip the default form since it's the same as pokemon_id
                    if form.category == "default":
                        continue
                    try:
                        self._save_evolution_data(
                            form.name,
                            evolution_chain,
                            evolves_to,
                            check_forms=False,
                            subfolder=form.category,
                        )
                    except FileNotFoundError:
                        self.logger.warning(
                            f"Form variant not found: {form.name} in {form.category} folder"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Error saving form {form.name}: {e}"
                        )

            self._parsed_data["evolution_changes"][pokemon_id] = str(path)
            self.logger.info(f"Updated evolution for {pokemon_data.name}")
        except FileNotFoundError:
            self.logger.error(f"Pokemon not found: {pokemon_id} in {subfolder} folder")
        except Exception as e:
            self.logger.error(f"Error saving evolution data for {pokemon_id}: {e}")

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
