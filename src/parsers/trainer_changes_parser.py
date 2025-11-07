"""
Parser for Trainer Changes documentation file.

This parser:
1. Reads data/documentation/Trainer Changes.txt
2. Generates a markdown file to docs/trainer_changes.md
3. Generates JSON data files to data/locations/ for each location with trainer information
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.data.pokedb_loader import PokeDBLoader
from src.utils.formatters.markdown_formatter import (
    format_ability,
    format_checkbox,
    format_item,
    format_move,
    format_pokemon,
    format_type_badge,
)

from .base_parser import BaseParser


class TrainerChangesParser(BaseParser):
    """Parser for Trainer Changes documentation.

    Args:
        BaseParser (_type_): Abstract base parser class.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Trainer Changes parser.

        Args:
            input_file (str): Path to the input file.
            output_dir (str, optional): Path to the output directory. Defaults to "docs".
        """
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = [
            "General Changes and Information",
            "EV and Level Trainers' Information",
            "Level Cap and Guide (Spoiler Free!)",
            "Full Level Cap and Guide for Challenge mode (Spoilers!)",
            "Challenge Mode Level Bug - Important info for Challenge Runs!",
            "Trainer Changes",
            "The Postgame",
        ]

        # EV and Level Trainers' Information States
        self._is_table_open = False

        # Full Level Cap and Guide for Challenge mode (Spoilers!) States
        self._is_legend_open = False
        self._is_table_open = False

        # Trainer Changes States
        self._is_table_open = False
        self._current_trainer = ""
        self._indent_level = 0

        # Location data tracking
        self._locations_data: Dict[str, Dict[str, Any]] = {}
        self._current_location = ""
        self._current_sublocation = ""
        self._base_sublocation = ""  # The sublocation from "XXX - YYY" pattern
        self._current_trainer_data: Optional[Dict[str, Any]] = None
        self._location_data_dir = Path("data/locations")

    def handle_section_change(self, new_section: str) -> None:
        """Handle state reset on section change.

        Args:
            new_section (str): The new section being parsed.
        """
        self._is_table_open = False
        return super().handle_section_change(new_section)

    def parse_general_changes_and_information(self, line: str) -> None:
        """Parse the General Changes and Information section.

        Args:
            line (str): Line of text to parse.
        """
        self.parse_default(line)

    def parse_ev_and_level_trainers_information(self, line: str) -> None:
        """Parse the EV and Level Trainers' Information section.

        Args:
            line (str): Line of text to parse.
        """
        # Match: "Training Level      Requirement"
        if line == "Training Level      Requirement":
            self._is_table_open = True
            self._markdown += "| Training Level | Requirement |\n"
        # Match: "---                 ---"
        elif line == "---                 ---":
            self._markdown += "|:---------------|:------------|\n"
        # Match table rows
        elif self._is_table_open and line:
            training_level, requirement = re.split(r"\s{3,}", line)
            self._markdown += f"| {training_level} | {requirement} |\n"
        # Default: regular text line
        else:
            self.parse_default(line)

    def parse_level_cap_and_guide_spoiler_free(self, line: str) -> None:
        """Parse the Level Cap and Guide (Spoiler Free!) section.

        Args:
            line (str): Line of text to parse.
        """
        self.parse_default(line)

    def parse_full_level_cap_and_guide_for_challenge_mode_spoilers(
        self, line: str
    ) -> None:
        """Parse the Full Level Cap and Guide for Challenge mode (Spoilers!) section.

        Args:
            line (str): Line of text to parse.
        """
        # Match: empty line
        if line == "":
            self._is_legend_open = False
            self.parse_default(line)
        # Match: "Legend:"
        elif line == "Legend:":
            self._is_legend_open = True
            self._markdown += "| Symbol | Meaning |\n"
            self._markdown += "|:------:|:--------|\n"
        # Match legend entries
        elif self._is_legend_open:
            symbol, meaning = line.split(" = ")
            self._markdown += f"| {symbol} | {meaning} |\n"
        # Match level cap entries
        elif match := re.match(r"^(●|○) (\d+) (.*)$", line):
            if not self._is_table_open:
                self._is_table_open = True
                self._markdown += "| Level Cap | Trainer | Required |\n"
                self._markdown += "|:----------|:--------|:--------:|\n"

            bullet, number, text = match.groups()
            required = True if bullet == "●" else False
            self._markdown += f"| {number} | {text} | {format_checkbox(required)} |\n"
        # Default: regular text line
        else:
            self.parse_default(line)

    def parse_challenge_mode_level_bug_important_info_for_challenge_runs(
        self, line: str
    ) -> None:
        """Parse the Challenge Mode Level Bug - Important info for Challenge Runs! section.

        Args:
            line (str): Line of text to parse.
        """
        self.parse_default(line)

    def parse_trainer_changes(self, line: str) -> None:
        """Parse the Trainer Changes section.

        Args:
            line (str): Line of text to parse.
        """
        line = line.replace("*", "\\*")
        next_line = self.peek_line(1) or ""

        # Match: main headings (locations)
        if next_line == "+++":
            # Save previous location data if any
            if self._current_location and self._current_location in self._locations_data:
                self._save_location_data(self._current_location)

            # Parse location name for sublocation pattern "XXX - YYY"
            location_raw = line
            if " - " in location_raw:
                parts = location_raw.split(" - ", 1)
                self._current_location = parts[0]
                self._base_sublocation = parts[1]
                self._current_sublocation = parts[1]
            else:
                self._current_location = location_raw
                self._base_sublocation = ""
                self._current_sublocation = ""

            self._initialize_location_data(self._current_location)
            self._markdown += f"### {location_raw}\n\n"
        elif line == "+++":
            pass
        # Match: dividers
        elif line == "---":
            self._markdown += "\n"
        # Match: sub-headings (nested sublocations from ~~~~)
        # These should be nested under the base sublocation if one exists
        elif next_line.startswith("~") and line:
            nested_sublocation = line.strip(': ')
            # If we have a base sublocation (from "XXX - YYY"), nest this under it
            if self._base_sublocation:
                self._current_sublocation = f"{self._base_sublocation}/{nested_sublocation}"
            else:
                self._current_sublocation = nested_sublocation
            self._markdown += f"#### {nested_sublocation}\n"
        elif match := re.match(r"^\~{1,} (.+) \~{1,}$", line):
            nested_sublocation = match.group(1).strip(': ')
            # If we have a base sublocation (from "XXX - YYY"), nest this under it
            if self._base_sublocation:
                self._current_sublocation = f"{self._base_sublocation}/{nested_sublocation}"
            else:
                self._current_sublocation = nested_sublocation
            self._markdown += f"#### {nested_sublocation}\n"
        elif line.startswith("~"):
            pass
        # Match: "<pokemon> [(<ability>)], lv.<level>: <moves>"
        elif match := re.match(r"^(.+?) \[(.+?)\], lv\.(\d+): (.+?)$", line):
            pokemon, ability, level, moves = match.groups()
            self._add_pokemon_to_trainer(pokemon, ability, level, None, moves)
            self._markdown += self._format_pokemon_row(
                pokemon, ability, level, None, moves
            )
        # Match: "<pokemon> [(<ability>)], lv.<level> @<item>: <moves>"
        elif match := re.match(r"^(.+?) \[(.+?)\], lv\.(\d+) @(.+?): (.+?)$", line):
            pokemon, ability, level, item, moves = match.groups()
            self._add_pokemon_to_trainer(pokemon, ability, level, item, moves)
            self._markdown += self._format_pokemon_row(
                pokemon, ability, level, item, moves
            )
        # Match: "(If you picked <starter>):"
        elif match := re.match(r"^\(If you picked (.+?)\):$", line):
            self._indent_level = 2 if self._current_trainer.startswith("Partner") else 1
            self._is_table_open = False

            starter = match.group(1)
            # Handle starter variations in data
            if self._current_trainer_data:
                if "starter_variations" not in self._current_trainer_data:
                    self._current_trainer_data["starter_variations"] = {}
                self._current_trainer_data["starter_variations"][starter] = {"team": []}

            self._markdown += f'{"\t" * (self._indent_level - 1)}=== "{starter}"\n\n'
        # Match: "<trainer>:"
        elif match := re.match(r"^(.*):$", line):
            self._current_trainer = match.group(1)
            self._current_trainer_data = self._create_trainer_data(self._current_trainer)
            self._add_trainer_to_location(self._current_trainer_data)
            self._markdown += self._format_trainer(self._current_trainer)
            self._is_table_open = False
        # Default: regular text line
        else:
            self._indent_level = 0
            self.parse_default(line)

    def _format_trainer(self, trainer: str) -> str:
        """Format a trainer name and extract optional metadata.

        Args:
            trainer (str): The raw trainer name string with optional metadata

        Returns:
            str: Formatted markdown string for the trainer header.
        """
        md = ""

        if " Side" in trainer or trainer.startswith("Partner"):
            md += f'=== "{trainer}"\n\n'
            self._indent_level = 1
            return md

        # Extract optional fields (reward in {}, mode in [], battle type in ())
        fields = {"reward": "", "mode": "", "battle_type": ""}
        patterns = {
            "reward": r"\{(.+?)\}",
            "mode": r"\[(.+?)\]",
            "battle_type": r"\((.+?)\)",
        }

        for key, pat in patterns.items():
            m = re.search(pat, trainer)
            if m:
                fields[key] = m.group(1).strip()
                trainer = re.sub(r"\s*" + re.escape(m.group(0)) + r"\s*", " ", trainer)

        trainer = trainer.strip(" -")
        md += f"**{trainer}**\n\n"

        # Format optional fields
        if fields["reward"]:
            md += "**Reward:** "
            md += ", ".join(
                format_item(item.strip()) for item in fields["reward"].split(",")
            )
            md += "\n\n"
        if fields["mode"]:
            md += f"**Mode:** {fields['mode']}\n\n"
        if fields["battle_type"]:
            md += f"**Battle Type:** {fields['battle_type']}\n\n"

        return md

    def _format_pokemon_row(
        self, pokemon: str, ability: str, level: str, item: Optional[str], moves: str
    ) -> str:
        """Format a Pokémon team member as a row in the trainer's markdown table.

        Args:
            pokemon (str): The name of the Pokémon.
            ability (str): The ability of the Pokémon.
            level (str): The level of the Pokémon.
            item (Optional[str]): The held item of the Pokémon.
            moves (str): The moves of the Pokémon.

        Returns:
            str: Formatted markdown string for the Pokémon row.
        """
        md = ""

        if not self._is_table_open:
            md += "\t" * self._indent_level + "| Pokémon | Attributes | Moves |\n"
            md += "\t" * self._indent_level + "|:-------:|:-----------|:------|\n"
            self._is_table_open = True

        # Pokémon column
        row = f"| {format_pokemon(pokemon)} | "

        # Attributes column
        pokemon_data = PokeDBLoader.load_pokemon(pokemon)
        types = pokemon_data.types if pokemon_data else []

        row += f"**Level:** {level}"
        row += f"<br>**Ability:** {format_ability(ability)}"
        if item:
            row += f"<br>**Item:** {format_item(item)}"
        if types:
            row += f"<br><div class='badges-hstack' style='margin-top:4px;'>{' '.join(format_type_badge(t) for t in types)}</div>"
        row += " | "

        # Moves column
        for i, move in enumerate(re.split(r",\s*", moves)):
            if i > 0:
                row += "<br>"
            row += f"{i + 1}. {format_move(move)}"

        md += "\t" * self._indent_level + row + "\n"
        return md

    def parse_the_postgame(self, line: str) -> None:
        """Parse The Postgame section."""
        self.parse_trainer_changes(line)

    def _initialize_location_data(self, location: str) -> None:
        """Initialize data structure for a location.

        Args:
            location (str): The location name.
        """
        if location not in self._locations_data:
            self._locations_data[location] = {
                "name": location,
                "sublocations": {},
                "trainers": [],
            }

    def _create_trainer_data(self, trainer_raw: str) -> Dict[str, Any]:
        """Create a trainer data dictionary from raw trainer string.

        Args:
            trainer_raw (str): The raw trainer name string with optional metadata.

        Returns:
            Dict[str, Any]: Trainer data dictionary.
        """
        # Extract optional fields (reward in {}, mode in [], battle type in ())
        fields = {"reward": [], "mode": "", "battle_type": ""}
        patterns = {
            "reward": r"\{(.+?)\}",
            "mode": r"\[(.+?)\]",
            "battle_type": r"\((.+?)\)",
        }

        trainer_name = trainer_raw
        for key, pat in patterns.items():
            m = re.search(pat, trainer_raw)
            if m:
                if key == "reward":
                    fields[key] = [item.strip() for item in m.group(1).split(",")]
                else:
                    fields[key] = m.group(1).strip()
                trainer_name = re.sub(r"\s*" + re.escape(m.group(0)) + r"\s*", " ", trainer_name)

        trainer_name = trainer_name.strip(" -")

        trainer_data = {
            "name": trainer_name,
            "raw_name": trainer_raw,
            "team": [],
            "sublocation": self._current_sublocation,
        }

        if fields["reward"]:
            trainer_data["reward"] = fields["reward"]
        if fields["mode"]:
            trainer_data["mode"] = fields["mode"]
        if fields["battle_type"]:
            trainer_data["battle_type"] = fields["battle_type"]

        return trainer_data

    def _add_trainer_to_location(self, trainer_data: Dict[str, Any]) -> None:
        """Add trainer data to the current location or sublocation.

        Args:
            trainer_data (Dict[str, Any]): The trainer data to add.
        """
        if not self._current_location:
            return

        if self._current_location not in self._locations_data:
            self._initialize_location_data(self._current_location)

        # Add to sublocation if specified
        if self._current_sublocation:
            # Navigate/create nested sublocation structure
            target = self._get_or_create_sublocation(
                self._locations_data[self._current_location],
                self._current_sublocation
            )
            if "trainers" not in target:
                target["trainers"] = []
            target["trainers"].append(trainer_data)
        else:
            self._locations_data[self._current_location]["trainers"].append(trainer_data)

    def _get_or_create_sublocation(
        self, location_data: Dict[str, Any], sublocation_path: str
    ) -> Dict[str, Any]:
        """Get or create a nested sublocation using path notation (e.g., "Battle Company/47F").

        Args:
            location_data (Dict[str, Any]): The parent location data.
            sublocation_path (str): The sublocation path (can contain "/" for nesting).

        Returns:
            Dict[str, Any]: The target sublocation dictionary.
        """
        if "sublocations" not in location_data:
            location_data["sublocations"] = {}

        # Split path by "/" to handle nesting
        parts = sublocation_path.split("/")
        current = location_data["sublocations"]

        for i, part in enumerate(parts):
            if part not in current:
                current[part] = {
                    "name": part,
                    "sublocations": {} if i < len(parts) - 1 else {},
                }

            # If this is not the last part, navigate into nested sublocations
            if i < len(parts) - 1:
                if "sublocations" not in current[part]:
                    current[part]["sublocations"] = {}
                current = current[part]["sublocations"]
            else:
                # Return the final sublocation
                return current[part]

        return current[parts[-1]]

    def _add_pokemon_to_trainer(
        self, pokemon: str, ability: str, level: str, item: Optional[str], moves: str
    ) -> None:
        """Add a Pokemon to the current trainer's team.

        Args:
            pokemon (str): The name of the Pokemon.
            ability (str): The ability of the Pokemon.
            level (str): The level of the Pokemon.
            item (Optional[str]): The held item of the Pokemon.
            moves (str): The moves of the Pokemon.
        """
        if not self._current_trainer_data:
            return

        pokemon_data = PokeDBLoader.load_pokemon(pokemon)
        types = pokemon_data.types if pokemon_data else []

        pokemon_entry = {
            "pokemon": pokemon,
            "ability": ability,
            "level": int(level),
            "moves": [move.strip() for move in re.split(r",\s*", moves)],
            "types": types,
        }

        if item:
            pokemon_entry["item"] = item

        # Check if we're in a starter variation
        if "starter_variations" in self._current_trainer_data and self._current_trainer_data["starter_variations"]:
            # Add to the last starter variation
            last_starter = list(self._current_trainer_data["starter_variations"].keys())[-1]
            self._current_trainer_data["starter_variations"][last_starter]["team"].append(pokemon_entry)
        else:
            self._current_trainer_data["team"].append(pokemon_entry)

    def _save_location_data(self, location: str) -> None:
        """Save location data to a JSON file.

        Args:
            location (str): The location name.
        """
        if location not in self._locations_data:
            return

        # Create data directory if it doesn't exist
        self._location_data_dir.mkdir(parents=True, exist_ok=True)

        # Sanitize filename
        filename = re.sub(r'[<>:"/\\|?*]', '_', location)
        filename = f"{filename}.json"

        output_path = self._location_data_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self._locations_data[location], f, indent=2, ensure_ascii=False)

    def finalize(self) -> None:
        """Finalize parsing and save remaining data."""
        # Save the last location if any
        if self._current_location and self._current_location in self._locations_data:
            self._save_location_data(self._current_location)

        super().finalize()
