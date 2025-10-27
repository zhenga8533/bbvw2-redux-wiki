"""
Parser for Wild Area Changes documentation file.

This parser:
1. Reads data/documentation/Wild Area Changes.txt
2. Generates a markdown file to docs/wild_area_changes.md
"""

from src.utils.markdown_util import format_pokemon
from src.utils.text_util import strip_common_prefix, strip_common_suffix
from .base_parser import BaseParser
import re


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
            "Postgame Locations Changes",
            "Hidden Grotto Guide",
        ]

        # Main Story Changes States
        self._current_location = ""
        self._tab_markdown = ""

    def parse_general_changes(self, line: str) -> None:
        """Parse the General Changes section."""
        self.parse_default(line)

    def parse_main_story_changes(self, line: str) -> None:
        """Parse the Main Story Changes section."""
        pokemon_row_pattern = r"(.+?) Lv. (.+?) (\d+)%"
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
            self._markdown += "| Pokémon | Level(s) | Chance |\n"
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
                self._tab_markdown += f"\t{extra}\n"
        elif match := re.match(r"^(.+?) Lv\. (.+?) (.+?)%$", line):
            pkmn, level, chance = match.groups()
            self._markdown += f"\t{self._format_pokemon_row(pkmn, level, chance)}\n"
        # Match: empty line
        elif line == "":
            self._markdown += f"\n{self._tab_markdown}"
            self._tab_markdown = ""
            self.parse_default(line)
        # Default: regular text line
        else:
            self.parse_default(line)

    def _format_pokemon_row(self, pokemon: str, level: str, chance: str) -> str:
        """Format a Pokémon row for the markdown table."""
        return f"| {format_pokemon(pokemon)} | {level} | {chance}% |"

    def parse_postgame_locations_changes(self, line: str) -> None:
        """Parse the Postgame Locations Changes section."""
        self.parse_main_story_changes(line)

    def parse_hidden_grotto_guide(self, line: str) -> None:
        """Parse the Hidden Grotto Guide section."""
        self.parse_default(line)
