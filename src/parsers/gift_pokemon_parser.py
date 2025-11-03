"""
Parser for Gift Pokemon documentation file.

This parser:
1. Reads data/documentation/Gift Pokemon.txt
2. Generates a markdown file to docs/gift_pokemon.md
"""

import re

from src.utils.formatters.markdown_util import format_pokemon

from .base_parser import BaseParser


class GiftPokemonParser(BaseParser):
    """
    Parser for Gift Pokemon documentation.

    Extracts gift Pokemon information and generates markdown.
    """

    def __init__(self, input_file: str, output_dir: str = "docs"):
        """Initialize the Gift Pokemon parser."""
        super().__init__(input_file=input_file, output_dir=output_dir)
        self._sections = ["General Notes", "Gift Pokémon", "Special Encounters"]

    def get_title(self) -> str:
        """Return the title with proper unicode character."""
        return "Gift Pokémon"

    def parse_general_notes(self, line: str) -> None:
        """Parse lines under the General Notes section."""
        self.parse_default(line)

    def parse_gift_pokemon(self, line: str) -> None:
        """Parse lines under the Gift Pokémon section."""
        next_line = self.peek_line(1)

        # Match: header line followed by "---" separator
        if next_line == "---":
            self._format_gift_pokemon(line)
        # Match: separator line "---"
        elif line == "---":
            return
        # Match: "Key: Value"
        elif match := re.match(r"([a-zA-z]+): (.*)", line):
            key, value = match.groups()
            self._markdown += f"**{key}**: {value}\n\n"
        # Default: regular text line
        else:
            self.parse_default(line)

    def _format_gift_pokemon(self, header: str) -> None:
        """Format gift Pokemon section with grid cards."""
        from src.data.pokedb_loader import PokeDBLoader

        # Clean up header
        header = header.removesuffix(".")
        gift_pokemon_names = re.split(r", | or ", header.removesuffix(" Egg"))

        self._markdown += f"### {header}\n\n"
        self._markdown += '<div class="grid cards" markdown>\n\n'

        for pokemon_name in gift_pokemon_names:
            # Load Pokemon data to get sprite and dex number
            pokemon_data = PokeDBLoader.load_pokemon(
                pokemon_name.lower().replace(" ", "-")
            )

            if pokemon_data:
                dex_num = pokemon_data.pokedex_numbers.get("national", "???")

                # Get sprite URL
                sprite_url = None
                if (
                    hasattr(pokemon_data.sprites, "versions")
                    and pokemon_data.sprites.versions
                ):
                    bw = pokemon_data.sprites.versions.black_white
                    if bw.animated and bw.animated.front_default:
                        sprite_url = bw.animated.front_default

                # Format name for display
                display_name = pokemon_name.replace("-", " ").title()
                # Handle special cases
                if "nidoran" in pokemon_name.lower():
                    if "f" in pokemon_name.lower():
                        display_name = "Nidoran♀"
                    elif "m" in pokemon_name.lower():
                        display_name = "Nidoran♂"
                elif pokemon_name.lower() == "mr mime":
                    display_name = "Mr. Mime"
                elif pokemon_name.lower() == "mime jr":
                    display_name = "Mime Jr."

                # Create link
                link = f"../pokedex/pokemon/{pokemon_data.name}.md"

                # Card structure: sprite first, then separator, then info
                self._markdown += "- "
                if sprite_url:
                    self._markdown += f"[![{display_name}]({sprite_url}){{: .pokemon-sprite-img }}]({link})\n\n"
                else:
                    self._markdown += f"[{display_name}]({link})\n\n"

                self._markdown += "\t---\n\n"
                self._markdown += f"\t**#{dex_num:03d} [{display_name}]({link})**\n\n"
            else:
                # Fallback if Pokemon data not found
                self._markdown += f"- {pokemon_name}\n\n"

        self._markdown += "</div>\n\n"

    def parse_special_encounters(self, line: str) -> None:
        """Parse lines under the Special Encounters section."""
        self.parse_gift_pokemon(line)
