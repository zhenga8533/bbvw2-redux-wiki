"""
Parser for Trainer Changes documentation file.

This parser:
1. Reads data/documentation/Trainer Changes.txt
2. Generates a markdown file to docs/trainer_changes.md
"""

import re
from typing import Any, Dict, Optional

from src.utils.markdown_util import (
    format_ability,
    format_item,
    format_move,
    format_pokemon,
    format_checkbox,
)
from .base_parser import BaseParser


class TrainerChangesParser(BaseParser):
    """
    Parser for Trainer Changes documentation.

    Extracts trainer change information and generates markdown.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Trainer Changes parser."""
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

    def handle_section_change(self, new_section: str) -> None:
        """Handle state reset on section change."""
        self._is_table_open = False
        return super().handle_section_change(new_section)

    def parse_general_changes_and_information(self, line: str) -> None:
        """Parse the General Changes and Information section."""
        self.parse_default(line)

    def parse_ev_and_level_trainers_information(self, line: str) -> None:
        """Parse the EV and Level Trainers' Information section."""
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
        """Parse the Level Cap and Guide (Spoiler Free!) section."""
        self.parse_default(line)

    def parse_full_level_cap_and_guide_for_challenge_mode_spoilers(
        self, line: str
    ) -> None:
        """Parse the Full Level Cap and Guide for Challenge mode (Spoilers!) section."""
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
        """Parse the Challenge Mode Level Bug - Important info for Challenge Runs! section."""
        self.parse_default(line)

    def parse_trainer_changes(self, line: str) -> None:
        """Parse the Trainer Changes section."""
        line = line.replace("*", "\\*")
        next_line = self.peek_line(1) or ""

        # Match: main headings
        if next_line == "+++":
            self._markdown += f"### {line}\n\n"
        elif line == "+++":
            pass
        # Match: dividers
        elif line == "---":
            self._markdown += "\n"
        # Match: sub-headings
        elif next_line.startswith("~") and line:
            self._markdown += f"#### {line.strip(': ')}\n"
        elif match := re.match(r"^\~{1,} (.+) \~{1,}$", line):
            self._markdown += f"#### {match.group(1).strip(': ')}\n"
        elif line.startswith("~"):
            pass
        # Match: "<pokemon> [(<ability>)], lv.<level>: <moves>"
        elif match := re.match(r"^(.+?) \[(.+?)\], lv\.(\d+): (.+?)$", line):
            pokemon, ability, level, moves = match.groups()
            self._format_pokemon_row(pokemon, ability, level, None, moves)
        # Match: "<pokemon> [(<ability>)], lv.<level> @<item>: <moves>"
        elif match := re.match(r"^(.+?) \[(.+?)\], lv\.(\d+) @(.+?): (.+?)$", line):
            pokemon, ability, level, item, moves = match.groups()
            self._format_pokemon_row(pokemon, ability, level, item, moves)
        # Match: "(If you picked <starter>):"
        elif match := re.match(r"^\(If you picked (.+?)\):$", line):
            self._indent_level = 2 if self._current_trainer.startswith("Partner") else 1
            self._is_table_open = False

            starter = match.group(1)
            self._markdown += f'{"\t" * (self._indent_level - 1)}=== "{starter}"\n\n'
        # Match: "<trainer>:"
        elif match := re.match(r"^(.*):$", line):
            self._current_trainer = match.group(1)
            self._format_trainer(self._current_trainer)
            self._is_table_open = False
        # Default: regular text line
        else:
            self._indent_level = 0
            self.parse_default(line)

    def _format_trainer(self, trainer: str) -> None:
        """Format a trainer name."""
        if " Side" in trainer or trainer.startswith("Partner"):
            self._markdown += f'=== "{trainer}"\n\n'
            self._indent_level = 1
            return

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
        self._markdown += f"**{trainer}**\n\n"

        # Format optional fields
        if fields["reward"]:
            self._markdown += "**Reward:** "
            self._markdown += ", ".join(
                format_item(item.strip(), relative_path="..") for item in fields["reward"].split(",")
            )
            self._markdown += "\n\n"
        if fields["mode"]:
            self._markdown += f"**Mode:** {fields['mode']}\n\n"
        if fields["battle_type"]:
            self._markdown += f"**Battle Type:** {fields['battle_type']}\n\n"

    def _format_pokemon_row(
        self, pokemon: str, ability: str, level: str, item: Optional[str], moves: str
    ) -> None:
        """Format a Pokémon row for the markdown table."""
        if not self._is_table_open:
            self._markdown += (
                "\t" * self._indent_level + "| Pokémon | Attributes | Moves |\n"
            )
            self._markdown += (
                "\t" * self._indent_level + "|:-------:|:-----------|:------|\n"
            )
            self._is_table_open = True

        row = f"| {format_pokemon(pokemon)} | "

        row += f"**Level:** {level}"
        row += f"<br>**Ability:** {format_ability(ability, relative_path="..")}"
        if item:
            row += f"<br>**Item:** {format_item(item, relative_path="..")}"
        row += " | "

        for i, move in enumerate(re.split(r",\s*", moves)):
            if i > 0:
                row += "<br>"
            row += f"{i + 1}. {format_move(move, relative_path="..")}"

        self._markdown += "\t" * self._indent_level + row + "\n"

    def parse_the_postgame(self, line: str) -> None:
        """Parse The Postgame section."""
        self.parse_trainer_changes(line)
