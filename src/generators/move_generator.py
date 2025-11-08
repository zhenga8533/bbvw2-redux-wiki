"""
Generator for move markdown pages.

This generator creates comprehensive move documentation pages with data
from the configured version group (see config.VERSION_GROUP).

This generator:
1. Reads move data from data/pokedb/parsed/move/
2. Generates individual markdown files for each move to docs/pokedex/moves/
3. Lists Pokemon that can learn each move (level-up, TM/HM, egg, tutor)
4. Uses version group data configured in config.py
"""

from collections import defaultdict
from pathlib import Path
from typing import Optional

from src.utils.core.config import VERSION_GROUP, VERSION_GROUP_FRIENDLY
from src.utils.core.loader import PokeDBLoader
from src.utils.data.models import Move
from src.utils.formatters.markdown_formatter import (
    format_category_badge,
    format_pokemon_card_grid,
    format_type_badge,
)
from src.utils.text.text_util import format_display_name

from .base_generator import BaseGenerator


class MoveGenerator(BaseGenerator):
    """
    Generator for move markdown pages.

    Creates detailed pages for each move including:
    - Type and category information
    - Power, accuracy, PP, and other stats
    - Effect descriptions
    - Flavor text
    - Learning Pokemon (level-up, TM/HM, egg, tutor)

    Args:
        BaseGenerator (_type_): Abstract base generator class
    """

    def __init__(
        self, output_dir: str = "docs/pokedex", project_root: Optional[Path] = None
    ):
        """Initialize the Move page generator.

        Args:
            output_dir (str, optional): Directory where markdown files will be generated. Defaults to "docs/pokedex".
            project_root (Optional[Path], optional): The root directory of the project. If None, it's inferred.
        """
        # Initialize base generator
        super().__init__(output_dir=output_dir, project_root=project_root)

        self.category = "moves"
        self.subcategory_order = ["physical", "special", "status"]
        self.subcategory_names = {
            "physical": "Physical Moves",
            "special": "Special Moves",
            "status": "Status Moves",
        }
        self.index_table_headers = ["Move", "Type", "Category", "Power", "Acc", "PP"]
        self.index_table_alignments = [
            "left",
            "center",
            "center",
            "left",
            "left",
            "left",
        ]

        # Create moves subdirectory
        self.output_dir = self.output_dir / "moves"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _build_pokemon_move_cache(self) -> dict[str, dict[str, list[dict]]]:
        """Build a cache mapping move names to Pokemon that can learn them.

        Returns:
            dict[str, dict[str, list[dict]]]: A mapping of move names to Pokemon by learn method.
        """
        from src.utils.core.loader import PokeDBLoader

        move_cache = defaultdict(
            lambda: {"level_up": [], "machine": [], "egg": [], "tutor": []}
        )

        # Moves have complex structure with multiple learn methods, handle manually
        for pokemon in PokeDBLoader.iterate_pokemon(
            include_non_default=False,
            deduplicate=True,
        ):
            if not pokemon.moves:
                continue

            # Level-up moves
            for move in pokemon.moves.level_up or []:
                move_cache[move.name]["level_up"].append(
                    {
                        "pokemon": pokemon,
                        "level": move.level_learned_at,
                    }
                )

            # TM/HM moves
            for move in pokemon.moves.machine or []:
                move_cache[move.name]["machine"].append({"pokemon": pokemon})

            # Egg moves
            for move in pokemon.moves.egg or []:
                move_cache[move.name]["egg"].append({"pokemon": pokemon})

            # Tutor moves
            for move in pokemon.moves.tutor or []:
                move_cache[move.name]["tutor"].append({"pokemon": pokemon})

        # Sort all lists by national dex number
        for move_data in move_cache.values():
            for method_list in move_data.values():
                method_list.sort(
                    key=lambda p: p["pokemon"].pokedex_numbers.get("national", 9999)
                )

        return dict(move_cache)

    def load_all_data(self) -> list[Move]:
        """Load all moves from the database once.

        Returns:
            list[Move]: A list of all Move objects
        """
        move_dir = self.project_root / "data" / "pokedb" / "parsed" / "move"

        if not move_dir.exists():
            self.logger.error(f"Move directory not found: {move_dir}")
            return []

        move_files = sorted(move_dir.glob("*.json"))
        self.logger.info(f"Found {len(move_files)} move files")

        moves = []
        for move_file in move_files:
            try:
                move = PokeDBLoader.load_move(move_file.stem)
                if move:
                    moves.append(move)
                else:
                    self.logger.warning(f"Could not load move: {move_file.stem}")
            except Exception as e:
                self.logger.error(f"Error loading {move_file.stem}: {e}", exc_info=True)

        # Sort alphabetically by name
        moves.sort(key=lambda m: m.name)
        self.logger.info(f"Loaded {len(moves)} moves")

        return moves

    def categorize_data(self, data: list[Move]) -> dict[str, list[Move]]:
        """Categorize moves by damage class for index and navigation.

        Args:
            data (list[Move]): List of Move objects to categorize

        Returns:
            dict[str, list[Move]]: Mapping of damage class identifiers to lists of Move objects
        """
        moves_by_damage_class = defaultdict(list)

        for move in data:
            damage_class = move.damage_class if move.damage_class else "unknown"
            moves_by_damage_class[damage_class].append(move)

        return moves_by_damage_class

    def format_index_row(self, entry: Move) -> list[str]:
        """Format a single row for the index table.

        Args:
            entry (Move): The entry to format

        Returns:
            list[str]: A list of strings for table columns: [link, type_badge, category_icon, power, accuracy, pp]
        """
        name = format_display_name(entry.name)
        link = f"[{name}](moves/{entry.name}.md)"

        move_type = getattr(entry.type, VERSION_GROUP, None) or "???"
        type_badge = format_type_badge(move_type)

        category = format_category_badge(entry.damage_class)

        power = getattr(entry.power, VERSION_GROUP, None)
        power_str = str(power) if power is not None and power > 0 else "—"

        accuracy = getattr(entry.accuracy, VERSION_GROUP, None)
        accuracy_str = str(accuracy) if accuracy is not None and accuracy > 0 else "—"

        pp = getattr(entry.pp, VERSION_GROUP, None)
        pp_str = str(pp) if pp is not None and pp > 0 else "—"

        return [link, type_badge, category, power_str, accuracy_str, pp_str]

    def _generate_move_header(self, move: Move) -> str:
        """Generate a move header section with type and category.

        Args:
            move (Move): The move object to generate the header for.

        Returns:
            str: The generated markdown for the move header.
        """
        md = ""

        display_name = format_display_name(move.name)
        move_type = getattr(move.type, VERSION_GROUP, None) or "???"
        category = move.damage_class.title() if move.damage_class else "Unknown"

        md += "<div>\n"
        md += "\t<div>\n"
        md += f"\t\t<div>{display_name}</div>\n"
        md += "\t\t<div>\n"
        md += f"\t\t\t<div>{format_type_badge(move_type)}</div>\n"
        md += f"\t\t\t<div>{category}</div>\n"
        md += "\t\t</div>\n"
        md += "\t</div>\n"
        md += "</div>\n\n"

        return md

    def _generate_stats_section(self, move: Move) -> str:
        """Generate the move stats section with type, category, power, accuracy, PP, etc."""
        md = "## :material-chart-box: Stats\n\n"

        # Get stats
        move_type = getattr(move.type, VERSION_GROUP, None) or "???"
        category = move.damage_class.title() if move.damage_class else "Unknown"
        power = getattr(move.power, VERSION_GROUP, None)
        accuracy = getattr(move.accuracy, VERSION_GROUP, None)
        pp = getattr(move.pp, VERSION_GROUP, None)
        priority = move.priority

        # Use grid cards for a cleaner layout
        md += '<div class="grid cards" markdown>\n\n'

        # Card 1: Type
        md += "- **:material-tag: Type**\n\n"
        md += "\t---\n\n"
        md += f"\t{format_type_badge(move_type)}\n\n"

        # Card 2: Category
        md += "- **:material-shape: Category**\n\n"
        md += "\t---\n\n"
        md += f"\t{category}\n\n"

        # Card 3: Power
        md += "- **:material-fire: Power**\n\n"
        md += "\t---\n\n"
        if power is not None and power > 0:
            md += f"\t{power}\n\n"
        else:
            md += "\t—\n\n"

        # Card 4: Accuracy
        md += "- **:material-target: Accuracy**\n\n"
        md += "\t---\n\n"
        if accuracy is not None and accuracy > 0:
            md += f"\t{accuracy}%\n\n"
        else:
            md += "\t—\n\n"

        # Card 5: PP
        md += "- **:material-counter: PP**\n\n"
        md += "\t---\n\n"
        if pp is not None and pp > 0:
            md += f"\t{pp}\n\n"
        else:
            md += "\t—\n\n"

        # Card 6: Priority
        md += "- **:material-priority-high: Priority**\n\n"
        md += "\t---\n\n"
        if priority is not None:
            priority_str = f"+{priority}" if priority > 0 else str(priority)
            md += f"\t{priority_str}\n\n"
        else:
            md += "\t0\n\n"

        md += "</div>\n\n"

        return md

    def _generate_effect_section(self, move: Move) -> str:
        """Generate the effect description section.

        Args:
            move (Move): The move object to generate the effect section for.

        Returns:
            str: The generated markdown for the effect section.
        """
        md = "## :material-information: Effect\n\n"

        # Full effect
        if move.effect:
            # Try to get version-specific effect, fallback to first available
            effect_text = getattr(move.effect, VERSION_GROUP, None)

            if effect_text:
                md += f'!!! info "Description"\n\n'
                md += f"    {effect_text}\n\n"

        # Short effect (handle GameVersionStringMap object)
        if move.short_effect:
            short_effect_text = None
            if hasattr(move.short_effect, VERSION_GROUP):
                short_effect_text = getattr(move.short_effect, VERSION_GROUP, None)
            else:
                short_effect_text = str(move.short_effect)

            if short_effect_text:
                md += f'!!! tip "Quick Summary"\n\n'
                md += f"    {short_effect_text}\n\n"

        # If no effect information available
        if not move.effect and not move.short_effect:
            md += "*Effect description not available.*\n\n"

        return md

    def _generate_flavor_text_section(self, move: Move) -> str:
        """Generate the flavor text section.

        Args:
            move (Move): The move object to generate the flavor text section for.

        Returns:
            str: The generated markdown for the flavor text section.
        """
        md = "## :material-book-open: In-Game Description\n\n"

        flavor_text = getattr(move.flavor_text, VERSION_GROUP, None)

        if flavor_text:
            md += f'!!! quote "{VERSION_GROUP_FRIENDLY}"\n\n'
            md += f"    {flavor_text}\n\n"
        else:
            md += "*No in-game description available.*\n\n"

        return md

    def _generate_pokemon_section(
        self, move_name: str, cache: Optional[dict[str, dict[str, list[dict]]]] = None
    ) -> str:
        """Generate the section showing which Pokemon can learn this move.

        Args:
            move_name (str): The name of the move to generate the section for.
            cache (Optional[dict[str, dict[str, list[dict]]]], optional): A cache of move data to use. Defaults to None.

        Returns:
            str: The generated markdown for the Pokémon section.
        """
        md = "## :material-pokeball: Learning Pokémon\n\n"

        # Get Pokemon that can learn this move
        move_data = {}
        if cache is not None:
            move_data = cache.get(move_name, {})

        # Check if any Pokemon can learn this move
        has_pokemon = any(len(pokemon_list) > 0 for pokemon_list in move_data.values())

        if not has_pokemon:
            md += "*No Pokémon can learn this move.*\n\n"
            return md

        # Level-up
        if move_data.get("level_up"):
            md += "### :material-arrow-up-bold: Level-Up\n\n"
            pokemon = [entry["pokemon"] for entry in move_data["level_up"]]
            level = [
                f"Level {entry.get('level', '—')}" for entry in move_data["level_up"]
            ]
            md += format_pokemon_card_grid(pokemon, extra_info=level)
            md += "\n\n"

        # TM/HM
        if move_data.get("machine"):
            md += "### :material-disc: TM/HM\n\n"
            pokemon = [entry["pokemon"] for entry in move_data["machine"]]
            md += format_pokemon_card_grid(pokemon)
            md += "\n\n"

        # Egg moves
        if move_data.get("egg"):
            md += "### :material-egg-outline: Egg Moves\n\n"
            pokemon = [entry["pokemon"] for entry in move_data["egg"]]
            md += format_pokemon_card_grid(pokemon)
            md += "\n\n"

        # Tutor moves
        if move_data.get("tutor"):
            md += "### :material-school: Tutor\n\n"
            pokemon = [entry["pokemon"] for entry in move_data["tutor"]]
            md += format_pokemon_card_grid(pokemon)
            md += "\n\n"

        return md

    def generate_page(
        self, entry: Move, cache: Optional[dict[str, dict[str, list[dict]]]] = None
    ) -> Path:
        """Generate a markdown page for a single move.

        Args:
            entry (Move): The move entry to generate the page for.
            cache (Optional[dict[str, dict[str, list[dict]]]], optional): A cache of move data to use. Defaults to None.

        Returns:
            Path: The path to the generated markdown file.
        """
        display_name = format_display_name(entry.name)

        # Start building the markdown with title
        md = f"# {display_name}\n\n"

        # Add sections
        md += self._generate_stats_section(entry)
        md += self._generate_effect_section(entry)
        md += self._generate_flavor_text_section(entry)

        # Get Pokemon that can learn this move (using cache if available)
        md += self._generate_pokemon_section(entry.name, cache=cache)

        # Write to file
        output_file = self.output_dir / f"{entry.name}.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated page for {display_name}: {output_file}")
        return output_file

    def generate_all_pages(
        self,
        data: list[Move],
        cache: Optional[dict[str, dict[str, list[dict]]]] = None,
    ) -> list[Path]:
        """Generate markdown pages for all moves.

        Args:
            data (list[Move]): List of Move objects to generate pages for.
            cache (Optional[dict[str, dict[str, list[dict]]]], optional): A cache of move data to use. Defaults to None.

        Returns:
            list[Path]: List of paths to the generated markdown files.
        """
        cache = cache or self._build_pokemon_move_cache()
        return super().generate_all_pages(data, cache=cache)
