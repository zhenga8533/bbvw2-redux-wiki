"""
Generator for move markdown pages.

This generator is specifically designed for Blaze Black 2 & Volt White 2 Redux,
with content prioritizing Black 2 & White 2 data.

This generator:
1. Reads move data from data/pokedb/parsed/move/
2. Generates individual markdown files for each move to docs/pokedex/moves/
3. Lists Pokemon that can learn each move (level-up, TM/HM, egg, tutor)
4. Prioritizes Black 2 & White 2 content (flavor text, stats, etc.)

CSS Styling:
This generator uses CSS classes defined in docs/stylesheets/move.css.
Keep the CSS file in sync when adding new HTML elements or classes.

Key CSS classes used:
- .move-header, .move-header-content - Move header section (see _generate_move_header)
- .move-header-name, .move-header-meta - Header text elements
- .move-header-type, .move-header-category - Type and category displays
- .move-stats-grid, .move-stat-card - Stats display grid
- .move-stat-label, .move-stat-value - Individual stat elements
- .move-learning-method - Learning method annotations
"""

from pathlib import Path
from typing import Optional, List, Dict
from collections import defaultdict
from src.data.pokedb_loader import PokeDBLoader
from src.models.pokedb import Move, Pokemon
from src.utils.yaml_util import load_mkdocs_config, save_mkdocs_config
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

    # Type colors (same as Pokemon generator)
    TYPE_COLORS = {
        "normal": "#A8A878",
        "fire": "#F08030",
        "water": "#6890F0",
        "electric": "#F8D030",
        "grass": "#78C850",
        "ice": "#98D8D8",
        "fighting": "#C03028",
        "poison": "#A040A0",
        "ground": "#E0C068",
        "flying": "#A890F0",
        "psychic": "#F85888",
        "bug": "#A8B820",
        "rock": "#B8A038",
        "ghost": "#705898",
        "dragon": "#7038F8",
        "dark": "#705848",
        "steel": "#B8B8D0",
        "fairy": "#EE99AC",
    }

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

    def _format_name(self, name: str) -> str:
        """Format a move name for display (capitalize and handle special cases)."""
        # Handle special characters and formatting
        name = name.replace("-", " ")

        # Special cases for proper capitalization
        special_cases = {
            "tm": "TM",
            "hm": "HM",
            "hp": "HP",
            "u turn": "U-turn",
            "v create": "V-create",
        }

        # Check if the whole name is a special case
        lower_name = name.lower()
        if lower_name in special_cases:
            return special_cases[lower_name]

        # Default: title case
        return name.title()

    def _format_type(self, type_name: str) -> str:
        """Format a type name with color badge (same as Pokemon generator)."""
        formatted_name = type_name.title()
        type_class = f"type-{type_name.lower()}"
        return f'<span class="pokemon-type-badge {type_class}">{formatted_name}</span>'

    def _build_pokemon_move_cache(self) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Build a cache mapping move names to Pokemon that can learn them.

        Returns:
            Dict with move names as keys, values are dicts with learning methods as keys
            {'move-name': {'level_up': [{pokemon, level}, ...], 'machine': [...], ...}}
        """
        pokemon_base_dir = self.project_root / "data" / "pokedb" / "parsed" / "pokemon"
        subfolders = ["default", "transformation", "variant"]

        # Map: move_name -> {method: [{pokemon, level}, ...]}
        move_cache = defaultdict(
            lambda: {"level_up": [], "machine": [], "egg": [], "tutor": []}
        )
        seen_pokemon = set()

        for subfolder in subfolders:
            pokemon_dir = pokemon_base_dir / subfolder
            if not pokemon_dir.exists():
                continue

            pokemon_files = sorted(pokemon_dir.glob("*.json"))

            for pokemon_file in pokemon_files:
                try:
                    pokemon = PokeDBLoader.load_pokemon(
                        pokemon_file.stem, subfolder=subfolder
                    )

                    if not pokemon or not pokemon.is_default:
                        continue

                    # Create unique key to prevent duplicates
                    pokemon_key = (
                        pokemon.name,
                        pokemon.pokedex_numbers.get("national"),
                    )

                    if pokemon_key in seen_pokemon:
                        continue

                    seen_pokemon.add(pokemon_key)

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

                except Exception as e:
                    self.logger.warning(
                        f"Error loading Pokemon {pokemon_file.stem}: {e}"
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

        CSS classes used:
        - .move-header: Main header container
        - .move-header-content: Text content container
        - .move-header-name: Move name display
        - .move-header-meta: Type and category container
        - .move-header-type: Type badge
        - .move-header-category: Category display
        """
        md = ""

        display_name = self._format_name(move.name)
        move_type = move.type.black_2_white_2 or "???"
        category = move.damage_class.title() if move.damage_class else "Unknown"

        md += '<div class="move-header">\n'
        md += '\t<div class="move-header-content">\n'
        md += f'\t\t<div class="move-header-name">{display_name}</div>\n'
        md += '\t\t<div class="move-header-meta">\n'
        md += f'\t\t\t<div class="move-header-type">{self._format_type(move_type)}</div>\n'
        md += f'\t\t\t<div class="move-header-category">{category}</div>\n'
        md += "\t\t</div>\n"
        md += "\t</div>\n"
        md += "</div>\n\n"

        return md

    def _generate_stats_section(self, move: Move) -> str:
        """Generate the move stats section with type, category, power, accuracy, PP, etc."""
        md = "## :material-chart-box: Stats\n\n"

        # Get stats (prioritize Black 2 & White 2)
        move_type = move.type.black_2_white_2 or "???"
        category = move.damage_class.title() if move.damage_class else "Unknown"
        power = move.power.black_2_white_2
        accuracy = move.accuracy.black_2_white_2
        pp = move.pp.black_2_white_2
        priority = move.priority

        # Use grid cards for a cleaner layout
        md += '<div class="grid cards" markdown>\n\n'

        # Card 1: Type
        md += "- **:material-tag: Type**\n\n"
        md += "\t---\n\n"
        md += f"\t{self._format_type(move_type)}\n\n"

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
            effect_text = getattr(move.effect, "black_2_white_2", None) or getattr(
                move.effect, "black_white", None
            )

            if effect_text:
                md += f'!!! info "Description"\n\n'
                md += f"    {effect_text}\n\n"

        # Short effect (handle GameVersionStringMap object)
        if move.short_effect:
            short_effect_text = None
            if hasattr(move.short_effect, "black_2_white_2"):
                short_effect_text = (
                    move.short_effect.black_2_white_2 or move.short_effect.black_white
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

        flavor_text = move.flavor_text.black_2_white_2
        version = "Black 2 & White 2"

        if flavor_text:
            md += f'!!! quote "{version}"\n\n'
            md += f"    {flavor_text}\n\n"
        else:
            md += "*No in-game description available.*\n\n"

        return md

    def _generate_pokemon_section(
        self, move_name: str, cache: Optional[Dict[str, Dict[str, List[Dict]]]] = None
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
            md += '<div class="grid cards ability-pokemon-cards" markdown>\n\n'

            for entry in move_data["level_up"]:
                pokemon = entry["pokemon"]
                level = entry.get("level", "—")
                dex_num = pokemon.pokedex_numbers.get("national", "???")
                name = self._format_name(pokemon.name)
                link = f"../pokemon/{pokemon.name}.md"

                # Get sprite URL
                sprite_url = None
                if hasattr(pokemon.sprites, "versions") and pokemon.sprites.versions:
                    bw = pokemon.sprites.versions.black_white
                    if bw.animated and bw.animated.front_default:
                        sprite_url = bw.animated.front_default

                # Card structure: sprite first, then separator, then info
                md += "- "
                if sprite_url:
                    md += f"[![{name}]({sprite_url}){{: .pokemon-sprite-img }}]({link})\n\n"
                else:
                    md += f"[{name}]({link})\n\n"

                md += "\t---\n\n"
                md += f"\t**#{dex_num:03d} [{name}]({link})**\n\n"
                md += f"\tLevel {level}\n\n"

            md += "</div>\n\n"

        # TM/HM
        if move_data.get("machine"):
            md += "### :material-disc: TM/HM\n\n"
            md += '<div class="grid cards ability-pokemon-cards" markdown>\n\n'

            for entry in move_data["machine"]:
                pokemon = entry["pokemon"]
                dex_num = pokemon.pokedex_numbers.get("national", "???")
                name = self._format_name(pokemon.name)
                link = f"../pokemon/{pokemon.name}.md"

                # Get sprite URL
                sprite_url = None
                if hasattr(pokemon.sprites, "versions") and pokemon.sprites.versions:
                    bw = pokemon.sprites.versions.black_white
                    if bw.animated and bw.animated.front_default:
                        sprite_url = bw.animated.front_default

                # Card structure: sprite first, then separator, then info
                md += "- "
                if sprite_url:
                    md += f"[![{name}]({sprite_url}){{: .pokemon-sprite-img }}]({link})\n\n"
                else:
                    md += f"[{name}]({link})\n\n"

                md += "\t---\n\n"
                md += f"\t**#{dex_num:03d} [{name}]({link})**\n\n"

            md += "</div>\n\n"

        # Egg moves
        if move_data.get("egg"):
            md += "### :material-egg-outline: Egg Moves\n\n"
            md += '<div class="grid cards ability-pokemon-cards" markdown>\n\n'

            for entry in move_data["egg"]:
                pokemon = entry["pokemon"]
                dex_num = pokemon.pokedex_numbers.get("national", "???")
                name = self._format_name(pokemon.name)
                link = f"../pokemon/{pokemon.name}.md"

                # Get sprite URL
                sprite_url = None
                if hasattr(pokemon.sprites, "versions") and pokemon.sprites.versions:
                    bw = pokemon.sprites.versions.black_white
                    if bw.animated and bw.animated.front_default:
                        sprite_url = bw.animated.front_default

                # Card structure: sprite first, then separator, then info
                md += "- "
                if sprite_url:
                    md += f"[![{name}]({sprite_url}){{: .pokemon-sprite-img }}]({link})\n\n"
                else:
                    md += f"[{name}]({link})\n\n"

                md += "\t---\n\n"
                md += f"\t**#{dex_num:03d} [{name}]({link})**\n\n"

            md += "</div>\n\n"

        # Tutor moves
        if move_data.get("tutor"):
            md += "### :material-school: Tutor\n\n"
            md += '<div class="grid cards ability-pokemon-cards" markdown>\n\n'

            for entry in move_data["tutor"]:
                pokemon = entry["pokemon"]
                dex_num = pokemon.pokedex_numbers.get("national", "???")
                name = self._format_name(pokemon.name)
                link = f"../pokemon/{pokemon.name}.md"

                # Get sprite URL
                sprite_url = None
                if hasattr(pokemon.sprites, "versions") and pokemon.sprites.versions:
                    bw = pokemon.sprites.versions.black_white
                    if bw.animated and bw.animated.front_default:
                        sprite_url = bw.animated.front_default

                # Card structure: sprite first, then separator, then info
                md += "- "
                if sprite_url:
                    md += f"[![{name}]({sprite_url}){{: .pokemon-sprite-img }}]({link})\n\n"
                else:
                    md += f"[{name}]({link})\n\n"

                md += "\t---\n\n"
                md += f"\t**#{dex_num:03d} [{name}]({link})**\n\n"

            md += "</div>\n\n"

        return md

    def generate_move_page(
        self, move: Move, cache: Optional[Dict[str, Dict[str, List[Dict]]]] = None
    ) -> Path:
        """
        Generate a markdown page for a single move.

        Args:
            move: The Move data to generate a page for
            cache: Optional pre-built cache of move->Pokemon mappings for performance

        Returns:
            Path to the generated markdown file
        """
        display_name = self._format_name(move.name)

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

    def generate_all_move_pages(self) -> List[Path]:
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

        # Generate table
        md += "| Move | Type | Category | Power | Acc | PP |\n"
        md += "|------|------|----------|-------|-----|----|\n"

        # Category icons
        category_icons = {
            "physical": ":material-sword:",
            "special": ":material-auto-fix:",
            "status": ":material-shield-outline:",
        }

        for move in moves:
            name = self._format_name(move.name)
            link = f"[{name}](moves/{move.name}.md)"

            move_type = move.type.black_2_white_2 or "???"
            type_badge = self._format_type(move_type)

            category_icon = category_icons.get(move.damage_class, "")

            power = move.power.black_2_white_2
            power_str = str(power) if power is not None and power > 0 else "—"

            accuracy = move.accuracy.black_2_white_2
            accuracy_str = (
                str(accuracy) if accuracy is not None and accuracy > 0 else "—"
            )

            pp = move.pp.black_2_white_2
            pp_str = str(pp) if pp is not None and pp > 0 else "—"

            md += f"| {link} | {type_badge} | {category_icon} | {power_str} | {accuracy_str} | {pp_str} |\n"

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

            if not mkdocs_path.exists():
                self.logger.error(f"mkdocs.yml not found at {mkdocs_path}")
                return False

            # Load current mkdocs.yml
            config = load_mkdocs_config(mkdocs_path)

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
                    display_name = damage_class_display.get(class_key, class_key.title())
                    class_nav = [
                        {self._format_name(m.name): f"pokedex/moves/{m.name}.md"}
                        for m in class_moves
                    ]
                    # Using type: ignore because mkdocs nav allows mixed dict value types
                    moves_nav_items.append({display_name: class_nav})  # type: ignore

            # Add unknown damage class moves if any exist
            if "unknown" in moves_by_damage_class:
                unknown_moves = moves_by_damage_class["unknown"]
                unknown_nav = [
                    {self._format_name(m.name): f"pokedex/moves/{m.name}.md"}
                    for m in unknown_moves
                ]
                moves_nav_items.append({"Unknown": unknown_nav})  # type: ignore

            # Find and update Pokédex section in nav
            if "nav" not in config:
                raise ValueError("mkdocs.yml does not contain a 'nav' section")

            nav_list = config["nav"]
            pokedex_index = None

            # Find the Pokédex section
            for i, item in enumerate(nav_list):
                if isinstance(item, dict) and "Pokédex" in item:
                    pokedex_index = i
                    break

            if pokedex_index is None:
                raise ValueError(
                    "mkdocs.yml nav section does not contain 'Pokédex'. "
                    "Please add a 'Pokédex' section to the navigation first."
                )

            # Get the Pokédex navigation items
            pokedex_nav = nav_list[pokedex_index]["Pokédex"]
            if not isinstance(pokedex_nav, list):
                pokedex_nav = []

            # Find or create Moves subsection within Pokédex
            moves_subsection_index = None
            for i, item in enumerate(pokedex_nav):
                if isinstance(item, dict) and "Moves" in item:
                    moves_subsection_index = i
                    break

            # Update or append Moves subsection
            moves_subsection = {"Moves": moves_nav_items}
            if moves_subsection_index is not None:
                pokedex_nav[moves_subsection_index] = moves_subsection
            else:
                pokedex_nav.append(moves_subsection)

            # Update the config
            nav_list[pokedex_index] = {"Pokédex": pokedex_nav}
            config["nav"] = nav_list

            # Write updated mkdocs.yml
            save_mkdocs_config(mkdocs_path, config)

            self.logger.info(
                f"Updated mkdocs.yml with {len(moves)} moves organized into {len(moves_by_damage_class)} damage class sections"
            )
            return True

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
