"""
Parser for Evolution Changes documentation file.

This parser:
1. Reads data/documentation/Evolution Changes.txt
2. Updates pokemon evolution data in data/pokedb/parsed/
3. Generates a markdown file to docs/evolution_changes.md
"""

import re
from typing import Optional

from src.data.pokedb_loader import PokeDBLoader
from src.models.pokedb import EvolutionChain, EvolutionDetails, Gender
from src.utils.formatters.markdown_formatter import format_item, format_pokemon
from src.utils.services.evolution_service import EvolutionService
from src.utils.text.text_util import name_to_id

from .base_parser import BaseParser


class EvolutionChangesParser(BaseParser):
    """Parser for Evolution Changes documentation.

    Args:
        BaseParser (_type_): Abstract base parser class
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Evolution Changes parser.

        Args:
            input_file (str): Path to the input file.
            output_dir (str, optional): Path to the output directory. Defaults to "docs".
        """
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = ["General Notes", "Evolution Changes"]

        # Evolution Changes states
        self._is_table_open: bool = False
        self._parsed_cache: set[tuple[str, str]] = (
            set()
        )  # Track (pokemon, evolution) pairs
        self._current_dex_num: str = ""
        self._current_pokemon: str = ""

    def parse_general_notes(self, line: str) -> None:
        """Parse a line from the General Notes section.

        Args:
            line (str): A line from the General Notes section.
        """
        self.parse_default(line)

    def parse_evolution_changes(self, line: str) -> None:
        """Parse a line from the Evolution Changes section and update data.

        Args:
            line (str): A line from the Evolution Changes section.
        """
        # Match: table header "Pokémon              New Method"
        if line == "Pokémon              New Method":
            self._is_table_open = True
            self._markdown += '<div class="evolution-changes-table" markdown>\n\n'
            self._markdown += "| Dex # | Pokémon | Evolution | New Method |\n"
        # Match: table separator "---                  ---"
        elif line == "---                  ---":
            self._markdown += "|:------|:-------:|:---------:|:-----------|\n"
        # Match: "dex_num name (spaces) evolution_text"
        elif match := re.match(
            rf"^(\d+) ([A-Z][\w':.-]*(?:\s[A-Z][\w':.-]*)*)\s+(.*)", line
        ):
            self._current_dex_num, self._current_pokemon, evolution_text = (
                match.groups()
            )
            if result := self._extract_evolution_text(evolution_text):
                evolution, evolution_text = result
                self._markdown += self._format_evolution_row(evolution, evolution_text)
                self._update_evolution_method(evolution, evolution_text)
        # Match: continuation line with evolution text (same Pokemon as previous)
        elif line and self._current_pokemon:
            if result := self._extract_evolution_text(line.strip()):
                evolution, evolution_text = result
                self._markdown += self._format_evolution_row(evolution, evolution_text)
                self._update_evolution_method(evolution, evolution_text)
        # Unrecognized: log warning for unexpected format
        elif line:
            self.logger.warning(f"Unrecognized line format: '{line}'")
        # Match: empty line indicates end of table
        elif self._is_table_open:
            self._markdown += "\n</div>\n\n"
            self._is_table_open = False

    def _format_evolution_row(self, evolution: str, evolution_text: str) -> str:
        """Format a row for the evolution table.

        Args:
            evolution (str): The target evolution Pokemon name.
            evolution_text (str): The evolution method description.

        Returns:
            str: The formatted markdown table row.
        """
        # Format Pokemon with sprites and links
        from_pokemon_md = format_pokemon(self._current_pokemon)

        if evolution:
            to_pokemon_md = format_pokemon(evolution)
        else:
            to_pokemon_md = ""

        # Format the evolution method text
        formatted_text = self._format_evolution_text(evolution_text)

        # Add markdown table row
        md = f"| {self._current_dex_num} | {from_pokemon_md} | {to_pokemon_md} | {formatted_text} |\n"
        return md

    def _format_evolution_text(self, text: str) -> str:
        """Format evolution method text, replacing item mentions with formatted items.

        Args:
            text (str): The evolution method text (e.g., "Now evolves via the use of a Fire Stone")

        Returns:
            str: Formatted text with item sprites and names
        """

        def replace_item(match: re.Match[str]) -> str:
            item_name = match.group(1).strip()
            # Convert item name to ID format (replace spaces with hyphens)
            item_id = item_name.lower().replace(" ", "-")
            formatted = format_item(item_id, has_sprite=True, is_linked=True)
            return f"via the use of {formatted}"

        formatted_text = re.sub(
            r"via the use of a(?:n)? (.+?)(?=\s+in addition|\s+if|$)",
            replace_item,
            text,
        )
        return formatted_text

    def _extract_evolution_text(self, text: str) -> Optional[tuple[str, str]]:
        """Extract evolution and method from text.

        Args:
            text (str): The evolution text to parse

        Returns:
            Optional[tuple[str, str]]: A tuple of (evolution_pokemon_name, evolution_method_text) or None if no match
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
        """Update the evolution method for a specific evolution.

        Args:
            evolution (str): Target evolution Pokemon name
            method_text (str): Evolution method description
        """

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
