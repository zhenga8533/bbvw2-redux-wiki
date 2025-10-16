"""
Parser for Evolution Changes documentation file.

This parser:
1. Reads data/documentation/Evolution Changes.txt
2. Updates pokemon evolution data in data/pokedb/parsed/
3. Generates a markdown file to docs/evolution_changes.md
"""

import re

from src.utils.text_util import name_to_id
from src.utils.markdown_util import format_pokemon_with_sprite
from src.models.pokedb import (
    EvolutionChain,
    EvolutionDetails,
    Gender,
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

    _POKEMON_PATTERN_STR = r"([A-Z][\w':.-]*(?:\s[A-Z][\w':.-]*)*)"

    # Pre-compiled regex patterns for better performance
    _POKEMON_LINE_PATTERN = re.compile(rf"^(\d+) {_POKEMON_PATTERN_STR}\s+(.*)")
    _EVOLVES_INTO_PATTERN = re.compile(
        rf"Now evolves into {_POKEMON_PATTERN_STR} (.*)\."
    )
    _GENDER_FEMALE_PATTERN = re.compile(rf" if {_POKEMON_PATTERN_STR} is female")
    _GENDER_MALE_PATTERN = re.compile(rf" if {_POKEMON_PATTERN_STR} is male")

    # Pre-compiled evolution method patterns
    _LEVEL_PATTERN = re.compile(r"at Level (\d+)")
    _ITEM_PATTERN = re.compile(r"via the use of a(?:n)? (.+)")
    _FRIENDSHIP_PATTERN = re.compile(
        r"by leveling up while at (\d+)\+ friendship at any time of day"
    )
    _MOVE_PATTERN = re.compile(r"by leveling up while knowing the move (.+)")
    _PARTY_PATTERN = re.compile(
        rf"by leveling up when a {_POKEMON_PATTERN_STR} is in the party"
    )

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Evolution Changes parser."""
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = ["General Notes", "Evolution Changes"]

        # Initialize instance variables to avoid shared state between parser instances
        self._parsed_cache: set[str] = set()
        self._current_dex_num: str = ""
        self._current_pokemon: str = ""

    def parse_general_notes(self, line: str) -> None:
        """Parse a line from the General Notes section."""
        self._markdown += f"{line}\n"

    def parse_evolution_changes(self, line: str) -> None:
        """Parse a line from the Evolution Changes section and update data."""

        # Table header match
        if line == "Pokémon              New Method":
            self._markdown += "| Dex # | Pokémon | Evolution | New Method |\n"
        elif line == "---                  ---":
            self._markdown += "|:-----:|:-------:|:---------:|------------|\n"

        # Matches: dex_num name (spaces) evolution_text
        elif match := self._POKEMON_LINE_PATTERN.match(line):
            self._current_dex_num, self._current_pokemon, evolution_text = (
                match.groups()
            )
            evolution, evolution_text = self.parse_evolution_text(evolution_text)
            self._add_evolution_row(evolution, evolution_text)
            self.parse_evolution_method(evolution, evolution_text)
        elif line and self._current_pokemon:
            evolution, evolution_text = self.parse_evolution_text(line)
            self._add_evolution_row(evolution, evolution_text)
            self.parse_evolution_method(evolution, evolution_text)

    def _add_evolution_row(self, evolution: str, evolution_text: str) -> None:
        """
        Add a row to the evolution table with Pokemon sprites.

        Args:
            evolution: Name of the evolution target Pokemon
            evolution_text: Description of the evolution method
        """
        # Format Pokemon with sprites and links
        from_pokemon_md = format_pokemon_with_sprite(self._current_pokemon)

        if evolution:
            to_pokemon_md = format_pokemon_with_sprite(evolution)
        else:
            to_pokemon_md = ""

        # Add table row
        self._markdown += f"| {self._current_dex_num} | {from_pokemon_md} | {to_pokemon_md} | {evolution_text} |\n"

    def parse_evolution_text(self, text: str) -> tuple[str, str]:
        """
        Extract evolution and method from text.

        Args:
            text: The evolution text to parse

        Returns:
            Tuple of (evolution_pokemon_name, evolution_method_text)
            Returns ("", "") if the text doesn't match the expected pattern
        """
        if match := self._EVOLVES_INTO_PATTERN.match(text):
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
        # This flag determines whether we ADD to existing evolution methods or REPLACE them
        # We keep existing if:
        # 1. The text explicitly says "in addition to its normal evolution method", OR
        # 2. We've already processed this Pokemon once in this parse session (multiple evolutions)
        keep_existing = (
            "in addition to its normal evolution method" in method_text
            or self._current_pokemon in self._parsed_cache
        )
        method_text = method_text.replace(
            " in addition to its normal evolution method", ""
        )

        # Check for gender requirement
        gender = None
        if " if " in method_text and " is female" in method_text:
            gender = Gender.FEMALE
            method_text = self._GENDER_FEMALE_PATTERN.sub("", method_text)
        elif " if " in method_text and " is male" in method_text:
            gender = Gender.MALE
            method_text = self._GENDER_MALE_PATTERN.sub("", method_text)

        # Map of evolution method types to their pre-compiled patterns
        patterns = {
            "level": self._LEVEL_PATTERN,
            "item": self._ITEM_PATTERN,
            "friendship": self._FRIENDSHIP_PATTERN,
            "move": self._MOVE_PATTERN,
            "party": self._PARTY_PATTERN,
        }

        # Load the Pokemon data
        pokemon_id = name_to_id(self._current_pokemon)
        evolution_id = name_to_id(evolution)

        try:
            pokemon_data: Pokemon = PokeDBLoader.load_pokemon(pokemon_id)
        except FileNotFoundError:
            self.logger.error(f"Pokemon not found: {pokemon_id}")
            return

        evolution_chain: EvolutionChain = pokemon_data.evolution_chain
        evolution_details: EvolutionDetails = EvolutionDetails()

        matched = False

        # Try to match each known pattern
        for method_type, pattern in patterns.items():
            if match := pattern.match(method_text):
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
            self._parsed_cache.add(self._current_pokemon)
