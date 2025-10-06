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

    _cleared_evolutions: set[str] = set()

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
            # Convert current Pokemon name to filename format
            pokemon_filename = (
                self._current_pokemon.lower().replace(" ", "-").replace(".", "")
            )

            # Load the Pokemon data
            pokemon_data = self.loader.load_pokemon(pokemon_filename)

            # Get the evolution_chain
            evolution_chain = pokemon_data.get("evolution_chain", {})
            evolves_to = evolution_chain.get("evolves_to", [])

            # Check if we should keep existing evolutions
            keep_existing = evolution_data.pop("keep_existing", False)

            # Clear existing evolutions if this is the first time we're seeing this Pokemon
            if (
                not keep_existing
                and self._current_pokemon not in self._cleared_evolutions
            ):
                evolves_to = []
                self._cleared_evolutions.add(self._current_pokemon)
                self.logger.info(
                    f"Cleared existing evolutions for {self._current_pokemon}"
                )

            # Find the evolution entry for this target species
            evolution_exists = False
            target_species = evolution_data["species"]

            for evo in evolves_to:
                if evo.get("species_name") == target_species:
                    # Update existing evolution details
                    evo_details = evo.get("evolution_details", {})

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

                    # Update gender
                    if evolution_data.get("gender"):
                        evo_details["gender"] = evolution_data["gender"]
                    else:
                        evo_details["gender"] = None

                    evo["evolution_details"] = evo_details
                    evolution_exists = True
                    break

            if not evolution_exists:
                # Create new evolution entry in evolution_chain format
                new_evo = {
                    "species_name": target_species,
                    "evolution_details": {
                        "item": evolution_data.get("item"),
                        "trigger": evolution_data.get("trigger"),
                        "gender": evolution_data.get("gender"),
                        "held_item": None,
                        "known_move": evolution_data.get("move"),
                        "known_move_type": None,
                        "location": None,
                        "min_level": evolution_data.get("level"),
                        "min_happiness": evolution_data.get("happiness"),
                        "min_beauty": None,
                        "min_affection": None,
                        "needs_overworld_rain": False,
                        "party_species": evolution_data.get("party_species"),
                        "party_type": None,
                        "relative_physical_stats": None,
                        "time_of_day": "",
                        "trade_species": None,
                        "turn_upside_down": False,
                    },
                    "evolves_to": [],
                }
                evolves_to.append(new_evo)

            evolution_chain["evolves_to"] = evolves_to
            pokemon_data["evolution_chain"] = evolution_chain

            # Save the updated Pokemon data
            save_path = self.loader.save_pokemon(pokemon_filename, pokemon_data)
            self.logger.info(
                f"Updated evolution for {self._current_pokemon} -> {evolution_data['species']}"
            )

            # Track in parsed data
            self._parsed_data["evolution_changes"].append(
                {
                    "dex_number": self._current_dex_num,
                    "pokemon": self._current_pokemon,
                    "evolution_data": evolution_data,
                    "file_updated": str(save_path),
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
