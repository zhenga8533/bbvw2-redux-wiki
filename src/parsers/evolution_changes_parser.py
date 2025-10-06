"""
Parser for Evolution Changes documentation file.

This parser:
1. Reads data/documentation/Evolution Changes.txt
2. Updates pokemon evolution data in data/pokedb/parsed/
3. Generates a markdown file to docs/evolution_changes.md
"""

import re
from typing import Any, Dict

from src.utils.constants import POKEMON_PATTERN
from src.utils.pokedb_structure import EvolutionDetails
from src.utils.text_utils import name_to_id

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

    _evolution_cache: Dict[str, Any] = {}

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
            self._parsed_data["evolution_changes"] = []

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
            gender = "female"
            method_text = re.sub(rf" if {POKEMON_PATTERN} is female", "", method_text)
        elif " if " in method_text and " is male" in method_text:
            gender = "male"
            method_text = re.sub(rf" if {POKEMON_PATTERN} is male", "", method_text)

        patterns = {
            "level": r"at Level (\d+)",
            "item": r"via the use of a(?:n)? (.+)",
            "friendship": r"by leveling up while at (\d+)\+ friendship at any time of day",
            "move": r"by leveling up while knowing the move (.+)",
            "party": rf"by leveling up when a {POKEMON_PATTERN} is in the party",
        }

        evolution_data = {
            "species": evolution.lower().replace(" ", "-"),
            "trigger": None,
            "level": None,
            "item": None,
            "move": None,
            "party_species": None,
            "happiness": None,
            "gender": gender,
            "keep_existing": keep_existing,
        }

        matched = False
        for method_type, pattern in patterns.items():
            if match := re.match(pattern, method_text):
                matched = True

                if method_type == "level":
                    evolution_data["trigger"] = "level-up"
                    evolution_data["level"] = int(match.group(1))
                elif method_type == "item":
                    evolution_data["trigger"] = "use-item"
                    evolution_data["item"] = match.group(1).lower().replace(" ", "-")
                elif method_type == "friendship":
                    evolution_data["trigger"] = "level-up"
                    evolution_data["happiness"] = int(match.group(1))
                elif method_type == "move":
                    evolution_data["trigger"] = "level-up"
                    evolution_data["move"] = match.group(1).lower().replace(" ", "-")
                elif method_type == "party":
                    evolution_data["trigger"] = "level-up"
                    evolution_data["party_species"] = (
                        match.group(1).lower().replace(" ", "-")
                    )
                break
        if not matched:
            self.logger.warning(
                f"Could not parse evolution method for {self._current_pokemon}: {method_text}"
            )
            return

        # Update Pokemon data
        self._update_pokemon_evolution(evolution_data)

    def _update_pokemon_evolution(self, evolution_data: Dict[str, Any]) -> None:
        """Update the Pokemon JSON file with new evolution data in evolution_chain."""
        try:
            # Load the Pokemon data
            pokemon_filename = name_to_id(self._current_pokemon)
            pokemon_data = self.loader.load_pokemon(pokemon_filename)

            # Get the evolution data
            evolution_species = evolution_data["species"]
            evolution_chain = pokemon_data.get("evolution_chain", {})
            evolves_to = evolution_chain.get("evolves_to", [])

            # Clear existing evolutions if not keeping existing
            keep_existing = evolution_data.pop("keep_existing", False)
            if not keep_existing and self._current_pokemon not in self._evolution_cache:
                self._evolution_cache[self._current_pokemon] = evolution_chain
                self._clear_evolutions(evolves_to, evolution_species)

            # Find the evolution entry for this target species
            self._update_evolutions(evolves_to, evolution_data)

            # Save the updated Pokemon data
            files_updated = self._save_evolutions(pokemon_data)

            # Track in parsed data
            self._parsed_data["evolution_changes"].append(
                {
                    "dex_number": self._current_dex_num,
                    "pokemon": self._current_pokemon,
                    "evolution_data": evolution_data,
                    "files_updated": files_updated,
                }
            )

        except FileNotFoundError as e:
            self.logger.warning(
                f"Could not find Pokemon file for {self._current_pokemon}: {e}"
            )
        except Exception as e:
            self.logger.error(
                f"Error updating evolution for {self._current_pokemon}: {e}",
                exc_info=True,
            )

    def _clear_evolutions(
        self, evolves_to: list[Dict[str, Any]], evolution_species: str
    ) -> None:
        """Recursively clear evolution entries for the given species."""
        for i in range(len(evolves_to)):
            evolution = evolves_to[i]
            next_evolution = evolution.get("evolves_to", [])

            # If this evolution matches the target species, clear its evolution_details
            if evolution.get("species_name") == evolution_species:
                evolves_to[i] = {
                    "species_name": evolution["species_name"],
                    "evolution_details": EvolutionDetails(),
                    "evolves_to": next_evolution,
                }

            # Recursively clear in next evolutions
            self._clear_evolutions(next_evolution, evolution_species)

    def _update_evolutions(
        self, evolves_to: list[Dict[str, Any]], evolution_data: Dict[str, Any]
    ) -> None:
        """Recursively update evolution entries with new evolution data."""
        for evolution in evolves_to:
            if evolution.get("species_name") == evolution_data["species"]:
                evo_details = evolution.get("evolution_details", {})

                # Update the trigger
                if evolution_data.get("trigger"):
                    evo_details["trigger"] = evolution_data["trigger"]

                # Update level
                if evolution_data.get("level"):
                    evo_details["min_level"] = evolution_data["level"]
                else:
                    evo_details["min_level"] = None

                # Update item
                if evolution_data.get("item"):
                    evo_details["item"] = evolution_data["item"]
                else:
                    evo_details["item"] = None

                # Update happiness
                if evolution_data.get("happiness"):
                    evo_details["min_happiness"] = evolution_data["happiness"]
                else:
                    evo_details["min_happiness"] = None

                # Update move
                if evolution_data.get("move"):
                    evo_details["known_move"] = evolution_data["move"]
                else:
                    evo_details["known_move"] = None

                # Update party species
                if evolution_data.get("party_species"):
                    evo_details["party_species"] = evolution_data["party_species"]
                else:
                    evo_details["party_species"] = None

    def _save_evolutions(self, pokemon_data: Dict[str, Any]) -> None:
        """Recursively save updated pokemon data."""
        for evolution in pokemon_data.get("evolves_to", []):
            self._save_evolutions(evolution)
        self.loader.save_pokemon(pokemon_data["species_name"], pokemon_data)

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
