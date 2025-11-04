"""
Parser for Wild Area Changes documentation file.

This parser:
1. Reads data/documentation/Wild Area Changes.txt
2. Generates a markdown file to docs/wild_area_changes.md
"""

import re

from src.utils.formatters.markdown_formatter import format_pokemon
from src.utils.text.text_util import strip_common_prefix, strip_common_suffix

from .base_parser import BaseParser


class WildAreaChangesParser(BaseParser):
    """
    Parser for Wild Area Changes documentation.

    Extracts wild area change information and generates markdown.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Wild Area Changes parser."""
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = [
            "General Changes",
            "Main Story Changes",
            "Postgame Location Changes",
            "Hidden Grotto Guide",
        ]

        # Main Story Changes States
        self._current_location = ""
        self._tab_markdown = ""

        # Hidden Grotto Guide States
        self._encounter_type = ""

    def parse_general_changes(self, line: str) -> None:
        """Parse the General Changes section."""
        self.parse_default(line)

    def parse_main_story_changes(self, line: str) -> None:
        """
        Parse the Main Story Changes section for wild encounter tables.

        This method handles complex parsing logic for wild encounter data that may include:
        - Location headers marked with tildes: "~ Route 1 ~"
        - Multiple encounter methods side-by-side: "Grass:   Water:"
        - Pokemon encounter rows: "Pidgey Lv. 5-7 30%"
        - Dual-column tables for comparing two encounter methods
        - Tabbed sections using Material for MkDocs tabs

        The parser maintains state using self._tab_markdown to buffer the second
        column when processing dual-method tables, then emits both columns together.

        Args:
            line: A single line from the Wild Area Changes documentation file

        Side Effects:
            - Updates self._current_location when encountering location headers
            - Accumulates markdown in self._tab_markdown for dual-column tables
            - Appends formatted content to self._markdown
        """
        pokemon_row_pattern = r"(.+?) Lv\. (.+?) (.+?)%"
        table_header = "| Pokémon | Level(s) | Chance |"
        table_seperator = "|:-------:|:---------|:-------|"

        # Match: "~ <location> ~"
        if match := re.match(r"^\~{1,} (.+) \~{1,}$", line):
            self._current_location = match.group(1)
            self._markdown += f"\n### {self._current_location}\n"
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
        elif line.endswith(":"):
            self._markdown += f"#### {line[:-1]}\n\n"
            self._markdown += f"{table_header}\n"
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
                self._markdown += (
                    f"\t{self._format_pokemon_row(pkmn1, level1, chance1)}\n"
                )
                self._tab_markdown += (
                    f"\t{self._format_pokemon_row(pkmn2, level2, chance2)}\n"
                )
            else:
                self._markdown += (
                    f"\t{self._format_pokemon_row(pkmn1, level1, chance1)}\n"
                )
                self._tab_markdown += f"\t{extra.strip()}\n"
        elif match := re.match(rf"^{pokemon_row_pattern}$", line):
            pkmn, level, chance = match.groups()
            if self._tab_markdown:
                self._markdown += "\t"
            self._markdown += f"{self._format_pokemon_row(pkmn, level, chance)}\n"
        # Match: empty line
        elif line == "":
            self._markdown += f"\n{self._tab_markdown}"
            self._tab_markdown = ""
            self.parse_default(line)
        # Default: regular text line
        else:
            self.parse_default(line)

    def _format_pokemon_row(self, pokemon: str, level: str, chance: str) -> str:
        """
        Format a Pokemon wild encounter as a markdown table row.

        Args:
            pokemon: Pokemon name (e.g., "Pidgey", "Rattata")
            level: Level range string (e.g., "5-7", "10", "15-20")
            chance: Encounter rate percentage (e.g., "30", "15")

        Returns:
            str: Formatted markdown table row with Pokemon name (linked), level, and chance
                 Example: "| [Pidgey](pokedex/pokemon/pidgey.md) | 5-7 | 30% |"
        """
        return f"| {format_pokemon(pokemon)} | {level} | {chance}% |"

    def parse_postgame_location_changes(self, line: str) -> None:
        """Parse the Postgame Locations Changes section."""
        self.parse_main_story_changes(line)

    def parse_hidden_grotto_guide(self, line: str) -> None:
        """Parse the Hidden Grotto Guide section."""
        # Match: "~ <location> ~"
        if match := re.match(r"^\~{1,} (.+) \~{1,}$", line):
            self._current_location = match.group(1)
            self._markdown += f"\n### {self._current_location}\n"
        # Match: "<encounter>:"
        elif line.endswith(":"):
            self._encounter_type = line[:-1]
            self._markdown += f'=== "{self._encounter_type}"\n'
            if self._encounter_type != "Guaranteed Encounters":
                self._markdown += '\n\t<div style="display: flex; justify-content: center; align-items: flex-end; flex-wrap: wrap; gap: 1rem;">'
        # Match: encounter Pokémon line
        elif line and self._encounter_type:
            if self._encounter_type == "Guaranteed Encounters":
                self._markdown += f"\t{line}\n"
                return
            self._markdown += f"\t\t{format_pokemon(line.strip(' -'))}\n"

            if self.peek_line(1) == "":
                self._markdown += "\t</div>\n"
                self._encounter_type = ""
        # Default: regular text line
        else:
            self.parse_default(line)
