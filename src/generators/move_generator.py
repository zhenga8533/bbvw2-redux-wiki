"""
Generator for move markdown pages.

This generator is specifically designed for Blaze Black 2 & Volt White 2 Redux,
with content prioritizing Black 2 & White 2 data.

This generator:
1. Reads move data from data/pokedb/parsed/move/
2. Generates individual markdown files for each move to docs/pokedex/moves/
3. Lists Pokemon that can learn each move (level-up, TM/HM, egg, tutor)
4. Prioritizes Black 2 & White 2 content (flavor text, stats, etc.)
"""

from collections import defaultdict
from pathlib import Path
from typing import Optional

from src.data.pokedb_loader import PokeDBLoader
from src.models.pokedb import Move, Pokemon
from src.utils.formatters.markdown_formatter import (
    format_pokemon_card_grid,
    format_type_badge,
)
from src.utils.data.constants import (
    DAMAGE_CLASS_ICONS,
    POKEMON_FORM_SUBFOLDERS_STANDARD,
    TYPE_COLORS,
    PRIMARY_VERSION,
    FALLBACK_VERSION,
)
from src.utils.data.pokemon_util import iterate_pokemon
from src.utils.formatters.table_formatter import create_move_index_table
from src.utils.text.text_util import format_display_name
from src.utils.formatters.yaml_formatter import (
    load_mkdocs_config,
    save_mkdocs_config,
    update_pokedex_subsection,
)

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
    """

    def __init__(
        self, output_dir: str = "docs/pokedex", project_root: Optional[Path] = None
    ):
        """
        Initialize the Move page generator.

        Args:
            output_dir: Directory where markdown files will be generated
            project_root: The root directory of the project. If None, it's inferred.
        """
        # Initialize base generator
        super().__init__(output_dir=output_dir, project_root=project_root)

        # Create moves subdirectory
        self.output_dir = self.output_dir / "moves"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _build_pokemon_move_cache(self) -> dict[str, dict[str, list[dict]]]:
        """
        Build a cache mapping move names to Pokemon that can learn them.

        Returns:
            Dict with move names as keys, values are dicts with learning methods as keys
            {'move-name': {'level_up': [{pokemon, level}, ...], 'machine': [...], ...}}
        """
        pokemon_base_dir = self.project_root / "data" / "pokedb" / "parsed" / "pokemon"

        # Map: move_name -> {method: [{pokemon, level}, ...]}
        move_cache = defaultdict(
            lambda: {"level_up": [], "machine": [], "egg": [], "tutor": []}
        )

        # Use shared Pokemon iteration utility (handles deduplication and filtering)
        for pokemon in iterate_pokemon(
            pokemon_base_dir,
            subfolders=POKEMON_FORM_SUBFOLDERS_STANDARD,
            include_non_default=False,
            deduplicate=True,
        ):
            # Add this Pokemon to each move it can learn
            if pokemon.moves:
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
                    move_cache[move.name]["machine"].append(
                        {
                            "pokemon": pokemon,
                        }
                    )

                # Egg moves
                for move in pokemon.moves.egg or []:
                    move_cache[move.name]["egg"].append(
                        {
                            "pokemon": pokemon,
                        }
                    )

                # Tutor moves
                for move in pokemon.moves.tutor or []:
                    move_cache[move.name]["tutor"].append(
                        {
                            "pokemon": pokemon,
                        }
                    )

        # Sort all lists by national dex number
        for move_data in move_cache.values():
            for method_list in move_data.values():
                method_list.sort(
                    key=lambda p: p["pokemon"].pokedex_numbers.get("national", 9999)
                )

        return dict(move_cache)

    def _generate_move_header(self, move: Move) -> str:
        """
        Generate a move header section with type and category.
        """
        md = ""

        display_name = format_display_name(move.name)
        move_type = getattr(move.type, PRIMARY_VERSION, None) or "???"
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

        # Get stats (prioritize Black 2 & White 2)
        move_type = getattr(move.type, PRIMARY_VERSION, None) or "???"
        category = move.damage_class.title() if move.damage_class else "Unknown"
        power = getattr(move.power, PRIMARY_VERSION, None)
        accuracy = getattr(move.accuracy, PRIMARY_VERSION, None)
        pp = getattr(move.pp, PRIMARY_VERSION, None)
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
        """Generate the effect description section."""
        md = "## :material-information: Effect\n\n"

        # Full effect
        if move.effect:
            # Try to get version-specific effect, fallback to first available
            effect_text = getattr(move.effect, PRIMARY_VERSION, None) or getattr(
                move.effect, FALLBACK_VERSION, None
            )

            if effect_text:
                md += f'!!! info "Description"\n\n'
                md += f"    {effect_text}\n\n"

        # Short effect (handle GameVersionStringMap object)
        if move.short_effect:
            short_effect_text = None
            if hasattr(move.short_effect, PRIMARY_VERSION):
                short_effect_text = (
                    getattr(move.short_effect, PRIMARY_VERSION, None) or
                    getattr(move.short_effect, FALLBACK_VERSION, None)
                )
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
        """Generate the flavor text section."""
        md = "## :material-book-open: In-Game Description\n\n"

        flavor_text = getattr(move.flavor_text, PRIMARY_VERSION, None)
        version = "Black 2 & White 2"

        if flavor_text:
            md += f'!!! quote "{version}"\n\n'
            md += f"    {flavor_text}\n\n"
        else:
            md += "*No in-game description available.*\n\n"

        return md

    def _generate_pokemon_section(
        self, move_name: str, cache: Optional[dict[str, dict[str, list[dict]]]] = None
    ) -> str:
        """Generate the section showing which Pokemon can learn this move."""
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

    def generate_move_page(
        self, move: Move, cache: Optional[dict[str, dict[str, list[dict]]]] = None
    ) -> Path:
        """
        Generate a markdown page for a single move.

        Args:
            move: The Move data to generate a page for
            cache: Optional pre-built cache of move->Pokemon mappings for performance

        Returns:
            Path to the generated markdown file
        """
        display_name = format_display_name(move.name)

        # Start building the markdown with title
        md = f"# {display_name}\n\n"

        # Add sections
        md += self._generate_stats_section(move)
        md += self._generate_effect_section(move)
        md += self._generate_flavor_text_section(move)

        # Get Pokemon that can learn this move (using cache if available)
        md += self._generate_pokemon_section(move.name, cache=cache)

        # Write to file
        output_file = self.output_dir / f"{move.name}.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated page for {display_name}: {output_file}")
        return output_file

    def generate_all_move_pages(self) -> list[Path]:
        """
        Generate markdown pages for all moves in the database.

        Returns:
            List of paths to generated markdown files
        """
        self.logger.info("Starting generation of all move pages")

        # Build Pokemon move cache once (massive performance improvement)
        self.logger.info("Building Pokemon move cache...")
        pokemon_cache = self._build_pokemon_move_cache()
        self.logger.info(f"Cached {len(pokemon_cache)} moves across all Pokemon")

        # Get move directory
        move_dir = self.project_root / "data" / "pokedb" / "parsed" / "move"

        if not move_dir.exists():
            self.logger.error(f"Move directory not found: {move_dir}")
            return []

        move_files = sorted(move_dir.glob("*.json"))
        self.logger.info(f"Found {len(move_files)} moves")

        generated_files = []

        for move_file in move_files:
            try:
                move_name = move_file.stem
                move = PokeDBLoader.load_move(move_name)

                if move:
                    output_path = self.generate_move_page(move, cache=pokemon_cache)
                    generated_files.append(output_path)
                else:
                    self.logger.warning(f"Could not load move: {move_name}")

            except Exception as e:
                self.logger.error(
                    f"Error generating page for {move_file.stem}: {e}",
                    exc_info=True,
                )

        self.logger.info(f"Generated {len(generated_files)} move pages")
        return generated_files

    def generate_moves_index(self) -> Path:
        """
        Generate the main moves index page with links to all moves.

        Returns:
            Path to the generated index file
        """
        self.logger.info("Generating moves index page")

        # Get all moves
        move_dir = self.project_root / "data" / "pokedb" / "parsed" / "move"
        move_files = sorted(move_dir.glob("*.json"))

        # Load move data for the index
        moves = []
        for move_file in move_files:
            try:
                move = PokeDBLoader.load_move(move_file.stem)
                if move:
                    moves.append(move)
            except Exception as e:
                self.logger.error(f"Error loading {move_file.stem}: {e}")

        # Sort alphabetically by name
        moves.sort(key=lambda m: m.name)

        # Generate markdown
        md = "# Moves\n\n"
        md += (
            "Complete list of all moves in **Blaze Black 2 & Volt White 2 Redux**.\n\n"
        )
        md += "> Click on any move to see its full description and which Pokémon can learn it.\n\n"

        # Group moves by damage class
        from collections import defaultdict

        moves_by_damage_class = defaultdict(list)

        for move in moves:
            damage_class = move.damage_class if move.damage_class else "unknown"
            moves_by_damage_class[damage_class].append(move)

        # Damage class order and display names
        damage_class_order = ["physical", "special", "status"]
        damage_class_display = {
            "physical": "Physical Moves",
            "special": "Special Moves",
            "status": "Status Moves",
        }

        # Generate sections for each damage class
        for class_key in damage_class_order:
            if class_key not in moves_by_damage_class:
                continue

            class_moves = moves_by_damage_class[class_key]
            display_name = damage_class_display.get(class_key, class_key.title())

            # Add damage class header
            md += f"## {display_name}\n\n"

            # Build table rows for this damage class
            rows = []
            for move in class_moves:
                name = format_display_name(move.name)
                link = f"[{name}](moves/{move.name}.md)"

                move_type = getattr(move.type, PRIMARY_VERSION, None) or "???"
                type_badge = format_type_badge(move_type)

                category_icon = DAMAGE_CLASS_ICONS.get(move.damage_class, "")

                power = getattr(move.power, PRIMARY_VERSION, None)
                power_str = str(power) if power is not None and power > 0 else "—"

                accuracy = getattr(move.accuracy, PRIMARY_VERSION, None)
                accuracy_str = (
                    str(accuracy) if accuracy is not None and accuracy > 0 else "—"
                )

                pp = getattr(move.pp, PRIMARY_VERSION, None)
                pp_str = str(pp) if pp is not None and pp > 0 else "—"

                rows.append(
                    [link, type_badge, category_icon, power_str, accuracy_str, pp_str]
                )

            # Use standardized table utility
            md += create_move_index_table(rows)
            md += "\n"

        # Add unknown damage class moves if any
        if "unknown" in moves_by_damage_class:
            md += "## Unknown Category\n\n"
            rows = []
            for move in moves_by_damage_class["unknown"]:
                name = format_display_name(move.name)
                link = f"[{name}](moves/{move.name}.md)"

                move_type = getattr(move.type, PRIMARY_VERSION, None) or "???"
                type_badge = format_type_badge(move_type)

                category_icon = DAMAGE_CLASS_ICONS.get(move.damage_class, "")

                power = getattr(move.power, PRIMARY_VERSION, None)
                power_str = str(power) if power is not None and power > 0 else "—"

                accuracy = getattr(move.accuracy, PRIMARY_VERSION, None)
                accuracy_str = (
                    str(accuracy) if accuracy is not None and accuracy > 0 else "—"
                )

                pp = getattr(move.pp, PRIMARY_VERSION, None)
                pp_str = str(pp) if pp is not None and pp > 0 else "—"

                rows.append(
                    [link, type_badge, category_icon, power_str, accuracy_str, pp_str]
                )

            md += create_move_index_table(rows)
            md += "\n"

        # Write to file
        output_file = self.output_dir.parent / "moves.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated moves index: {output_file}")
        return output_file

    def update_mkdocs_navigation(self) -> bool:
        """
        Update mkdocs.yml with navigation links to all move pages.
        Organizes moves alphabetically into subsections.

        Returns:
            bool: True if update succeeded, False if it failed
        """
        try:
            mkdocs_path = self.project_root / "mkdocs.yml"

            # Get all moves
            move_dir = self.project_root / "data" / "pokedb" / "parsed" / "move"
            move_files = sorted(move_dir.glob("*.json"))

            # Load moves
            moves = []
            for move_file in move_files:
                try:
                    move = PokeDBLoader.load_move(move_file.stem)
                    if move:
                        moves.append(move)
                except Exception as e:
                    self.logger.warning(f"Could not load {move_file.stem}: {e}")

            # Sort alphabetically within each group
            moves.sort(key=lambda m: m.name)

            # Group moves by damage class
            moves_by_damage_class = defaultdict(list)

            # Damage class display name mapping
            damage_class_display = {
                "physical": "Physical",
                "special": "Special",
                "status": "Status",
            }

            for move in moves:
                damage_class = move.damage_class if move.damage_class else "unknown"
                moves_by_damage_class[damage_class].append(move)

            # Create navigation structure with damage class subsections
            moves_nav_items = [{"Overview": "pokedex/moves.md"}]

            # Add subsections for each damage class in order (Physical, Special, Status)
            damage_class_order = ["physical", "special", "status"]
            for class_key in damage_class_order:
                if class_key in moves_by_damage_class:
                    class_moves = moves_by_damage_class[class_key]
                    display_name = damage_class_display.get(
                        class_key, class_key.title()
                    )
                    class_nav = [
                        {format_display_name(m.name): f"pokedex/moves/{m.name}.md"}
                        for m in class_moves
                    ]
                    # Using type: ignore because mkdocs nav allows mixed dict value types
                    moves_nav_items.append({display_name: class_nav})  # type: ignore

            # Add unknown damage class moves if any exist
            if "unknown" in moves_by_damage_class:
                unknown_moves = moves_by_damage_class["unknown"]
                unknown_nav = [
                    {format_display_name(m.name): f"pokedex/moves/{m.name}.md"}
                    for m in unknown_moves
                ]
                moves_nav_items.append({"Unknown": unknown_nav})  # type: ignore

            # Use shared utility to update mkdocs navigation
            success = update_pokedex_subsection(
                mkdocs_path, "Moves", moves_nav_items, self.logger
            )

            if success:
                self.logger.info(
                    f"Updated mkdocs.yml with {len(moves)} moves organized into {len(moves_by_damage_class)} damage class sections"
                )

            return success

        except Exception as e:
            self.logger.error(f"Failed to update mkdocs.yml: {e}", exc_info=True)
            return False

    def generate(self) -> bool:
        """
        Generate move pages and moves index.

        Returns:
            bool: True if generation succeeded, False if it failed
        """
        self.logger.info("Starting moves generation...")
        try:
            # Clean up old move markdown files
            self._cleanup_output_dir()

            # Generate all move pages
            self.logger.info("Generating individual move pages...")
            move_files = self.generate_all_move_pages()

            if not move_files:
                self.logger.error("No move pages were generated")
                return False

            # Generate the moves index
            self.logger.info("Generating moves index...")
            index_path = self.generate_moves_index()

            # Update mkdocs.yml navigation
            self.logger.info("Updating mkdocs.yml navigation...")
            nav_success = self.update_mkdocs_navigation()

            if not nav_success:
                self.logger.warning(
                    "Failed to update mkdocs.yml navigation, but pages were generated successfully"
                )

            self.logger.info(
                f"Successfully generated {len(move_files)} move pages and index"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate moves: {e}", exc_info=True)
            return False
