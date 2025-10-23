"""
Parser for Trainer Changes documentation file.

This parser:
1. Reads data/documentation/Trainer Changes.txt
2. Generates a markdown file to docs/trainer_changes.md
"""

import re
from typing import Any, Dict

from src.utils.markdown_util import get_checkbox
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
        ]

        # EV and Level Trainers' Information States
        self._is_table_open = False

        # Full Level Cap and Guide for Challenge mode (Spoilers!) States
        self._is_legend_open = False
        self._is_table_open = False

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
            self._markdown += f"| {number} | {text} | {get_checkbox(required)} |\n"
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
        self.parse_default(line)
