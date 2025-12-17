"""
Parser for Wild Area Changes documentation file.

This parser:
1. Reads data/documentation/Wild Area Changes.txt
2. Generates a markdown file to docs/wild_area_changes.md
3. Generates/updates JSON data files to data/locations/ for each location with wild encounter information
"""

import re

from bbvw2_redux_wiki.utils.core.loader import PokeDBLoader
from bbvw2_redux_wiki.utils.formatters.markdown_formatter import (
    format_pokemon,
    format_pokemon_card_grid,
    format_type_badge,
)
from bbvw2_redux_wiki.utils.text.text_util import (
    strip_common_prefix,
    strip_common_suffix,
)

from .location_parser import LocationParser


class WildAreaChangesParser(LocationParser):
    """Parser for Wild Area Changes documentation.

    Args:
        LocationParser (_type_): Location parser base class.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Wild Area Changes parser.

        Args:
            input_file (str): Path to the input file.
            output_dir (str, optional): Path to the output directory. Defaults to "docs".
        """
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = [
            "General Changes",
            "Main Story Changes",
            "Postgame Location Changes",
            "Hidden Grotto Guide",
        ]

        # Main Story Changes States
        self._tab_markdown = ""

        # Hidden Grotto Guide States
        self._encounter_type = ""
        self._encounters = []

        # Wild area-specific tracking
        self._current_encounter_method = ""

        # Register tracking keys for wild encounters and hidden grotto
        self._register_tracking_key("wild_encounters")
        self._register_tracking_key("hidden_grotto")

    def parse_general_changes(self, line: str) -> None:
        """Parse the General Changes section.

        Args:
            line (str): Line of text to parse.
        """
        self.parse_default(line)

    def parse_main_story_changes(self, line: str) -> None:
        """Parse the Main Story Changes section.

        Args:
            line (str): line of text to parse.
        """
        pokemon_row_pattern = r"(.+?) Lv\. (.+?) (.+?)%"
        table_header = "| Pokémon | Type(s) | Level(s) | Chance |"
        table_seperator = "|:-------:|:-------:|:---------|:-------|"

        # Match: "~ <location> ~"
        if match := re.match(r"^\~{1,} (.+) \~{1,}$", line):
            location_raw = match.group(1)
            self._initialize_location_data(
                location_raw
            )  # This sets _current_location and _current_sublocation
            self._markdown += f"\n### {location_raw}\n"
        # Match: table headers
        elif match := re.match(r"^(.+?):\s{3,}(.+?):$", line):
            method1, method2 = match.group(1), match.group(2)
            parsed1 = strip_common_suffix(method2, method1)
            parsed2 = strip_common_prefix(method1, method2)
            self._markdown += f"#### {parsed1} & {parsed2}\n\n"

            self._markdown += f'=== "{method1}"\n\n'
            self._markdown += f"\t{table_header}\n"

            self._tab_markdown += f'=== "{method2}"\n\n'
            if method2 != "Hidden Grotto":
                self._tab_markdown += f"\t{table_header}\n"

            # Track encounter methods for data
            self._current_encounter_method = method1
        elif line.endswith(":"):
            self._markdown += f"#### {line[:-1]}\n\n"
            self._markdown += f"{table_header}\n"
            self._current_encounter_method = line[:-1]
        # Match: table seperators
        elif match := re.match(r"^\-{3,}\s{1,}\-{3,}$", line):
            self._markdown += f"\t{table_seperator}\n"
            if "Hidden Grotto" not in self._tab_markdown:
                self._tab_markdown += f"\t{table_seperator}\n"
        elif line.startswith("-"):
            self._markdown += f"{table_seperator}\n"
        # Match: table rows
        elif match := re.match(rf"^{pokemon_row_pattern}(.+?)$", line):
            pkmn1, level1, chance1, extra = match.groups()
            match2 = re.match(rf"\s{pokemon_row_pattern}$", extra)
            if match2:
                pkmn2, level2, chance2 = match2.groups()
                self._add_wild_encounter(
                    pkmn1, level1, chance1, self._current_encounter_method
                )
                self._markdown += (
                    f"\t{self._format_pokemon_row(pkmn1, level1, chance1)}\n"
                )
                self._tab_markdown += (
                    f"\t{self._format_pokemon_row(pkmn2, level2, chance2)}\n"
                )
            else:
                self._add_wild_encounter(
                    pkmn1, level1, chance1, self._current_encounter_method
                )
                self._markdown += (
                    f"\t{self._format_pokemon_row(pkmn1, level1, chance1)}\n"
                )
                self._tab_markdown += f"\t{extra.strip()}\n\n"
        elif match := re.match(rf"^{pokemon_row_pattern}$", line):
            pkmn, level, chance = match.groups()
            self._add_wild_encounter(
                pkmn, level, chance, self._current_encounter_method
            )
            if self._tab_markdown:
                self._markdown += "\t"
            self._markdown += f"{self._format_pokemon_row(pkmn, level, chance)}\n"
        # Match: empty line
        elif line == "":
            if self._tab_markdown:
                self._markdown += f"\n{self._tab_markdown}"
                self._tab_markdown = ""
            self.parse_default(line)
        # Default: regular text line
        else:
            self.parse_default(line)

    def _format_pokemon_row(self, pokemon: str, level: str, chance: str) -> str:
        """Format a Pokemon wild encounter as a markdown table row.

        Args:
            pokemon (str): The name of the Pokémon.
            level (str): The level(s) of the Pokémon.
            chance (str): The encounter chance percentage.

        Returns:
            str: A formatted markdown table row.
        """
        pokemon_md = format_pokemon(pokemon)

        pokemon_data = PokeDBLoader.load_pokemon(pokemon)
        types = pokemon_data.types if pokemon_data else []
        types_md = f"<div class='badges-vstack'>{' '.join(format_type_badge(t) for t in types)}</div>"

        return f"| {pokemon_md} | {types_md} | {level} | {chance}% |"

    def parse_postgame_location_changes(self, line: str) -> None:
        """Parse the Postgame Locations Changes section.

        Args:
            line (str): Line of text to parse.
        """
        self.parse_main_story_changes(line)

    def parse_hidden_grotto_guide(self, line: str) -> None:
        """Parse the Hidden Grotto Guide section.

        Args:
            line (str): Line of text to parse.
        """
        # Match: "~ <location> ~"
        if match := re.match(r"^\~{1,} (.+) \~{1,}$", line):
            location_raw = match.group(1)
            self._initialize_location_data(
                location_raw
            )  # This sets _current_location and _current_sublocation
            self._markdown += f"\n### {location_raw}\n"
        # Match: "<encounter>:"
        elif line.endswith(":"):
            self._encounter_type = line[:-1]
            self._markdown += f'=== "{self._encounter_type}"\n'
        # Match: encounter Pokémon line
        elif line and self._encounter_type:
            if self._encounter_type == "Guaranteed Encounters":
                # Pattern: " - You will always encounter a Lv. XX <Pokemon> here."
                if match := re.search(r"Lv\.\s*\d+\s+(\w+)", line):
                    pokemon_name = match.group(1)
                    self._add_hidden_grotto_encounter(
                        pokemon_name, self._encounter_type
                    )

                # Otherwise, just output the line as markdown text
                self._markdown += f"\t{line}\n"
                return

            pokemon_name = line.strip(" -")
            self._add_hidden_grotto_encounter(pokemon_name, self._encounter_type)
            self._encounters.append(pokemon_name)
        # Match: empty line after encounters
        elif len(self._encounters) > 0 and line == "":
            pokemon_cards = format_pokemon_card_grid(
                self._encounters,
                relative_path="../pokedex/pokemon",
                extra_info=[f"*{self._encounter_type.split(' ')[0]}*"]
                * len(self._encounters),
            )
            self._markdown += f"{'\n'.join(f'\t{l}'.rstrip() for l in pokemon_cards.splitlines())}\n\n"

            self._encounters = []
            self._encounter_type = ""
        # Default: regular text line
        else:
            self.parse_default(line)

    def _initialize_location_data(self, location_raw: str) -> None:
        """Initialize data structure for a location or load existing data.

        Args:
            location_raw (str): The raw location name (may include sublocation).
        """
        # Call parent class initialization
        super()._initialize_location_data(location_raw)

        # Determine current section to know what to clear
        current_section = self._current_section

        # Use centralized method to clear data on first encounter based on section
        if current_section in ["Main Story Changes", "Postgame Location Changes"]:
            self._clear_location_data_on_first_encounter(
                "wild_encounters", "wild_encounters"
            )

        if current_section == "Hidden Grotto Guide":
            self._clear_location_data_on_first_encounter(
                "hidden_grotto", "hidden_grotto"
            )

        # Ensure both keys always exist (even if not initialized yet)
        if self._current_location in self._locations_data:
            target = (
                self._get_or_create_sublocation(
                    self._locations_data[self._current_location],
                    self._current_sublocation,
                )
                if self._current_sublocation
                else self._locations_data[self._current_location]
            )

            if "wild_encounters" not in target:
                target["wild_encounters"] = {}
            if "hidden_grotto" not in target:
                target["hidden_grotto"] = {}

    def _add_wild_encounter(
        self, pokemon: str, level: str, chance: str, method: str
    ) -> None:
        """Add a wild encounter to the current location or sublocation.

        Args:
            pokemon (str): The name of the Pokemon.
            level (str): The level range of the Pokemon.
            chance (str): The encounter chance percentage.
            method (str): The encounter method (e.g., "Grass, Normal", "Surf, Dark Spot").
        """
        if not self._current_location or not method:
            return

        pokemon_data = PokeDBLoader.load_pokemon(pokemon)
        types = pokemon_data.types if pokemon_data else []

        # Handle special cases like '--' for chance
        try:
            chance_value = float(chance)
        except ValueError:
            chance_value = None

        encounter_entry = {
            "pokemon": pokemon,
            "level": level,
            "chance": chance_value,
            "types": types,
        }

        # Determine where to add the encounter (sublocation or main location)
        if self._current_sublocation:
            sublocation = self._get_or_create_sublocation(
                self._locations_data[self._current_location], self._current_sublocation
            )
            if "wild_encounters" not in sublocation:
                sublocation["wild_encounters"] = {}
            target = sublocation["wild_encounters"]
        else:
            target = self._locations_data[self._current_location]["wild_encounters"]

        # Initialize method in wild_encounters if not exists
        if method not in target:
            target[method] = []

        target[method].append(encounter_entry)

    def _add_hidden_grotto_encounter(self, pokemon: str, encounter_type: str) -> None:
        """Add a hidden grotto encounter to the current location or sublocation.

        Args:
            pokemon (str): The name of the Pokemon.
            encounter_type (str): The type of encounter (e.g., "Wild Pokémon", "Items").
        """
        if not self._current_location:
            return

        pokemon_data = PokeDBLoader.load_pokemon(pokemon)
        types = pokemon_data.types if pokemon_data else []

        # Determine where to add the encounter (sublocation or main location)
        if self._current_sublocation:
            target = self._get_or_create_sublocation(
                self._locations_data[self._current_location], self._current_sublocation
            )
        else:
            target = self._locations_data[self._current_location]

        # Initialize hidden_grotto if not exists
        if "hidden_grotto" not in target:
            target["hidden_grotto"] = {}

        if encounter_type not in target["hidden_grotto"]:
            target["hidden_grotto"][encounter_type] = []

        encounter_entry = {
            "pokemon": pokemon,
            "types": types,
        }

        target["hidden_grotto"][encounter_type].append(encounter_entry)
