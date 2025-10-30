"""
Generator for individual Pokemon markdown pages.

This generator:
1. Reads Pokemon data from data/pokedb/parsed/pokemon/
2. Generates individual markdown files for each Pokemon to docs/pokedex/pokemon/
3. Handles Pokemon forms and variations
"""

from pathlib import Path
from typing import Optional, Dict, List
from src.data.pokedb_loader import PokeDBLoader
from src.models.pokedb import Pokemon, Move
from src.utils.logger_util import get_logger
from src.utils.text_util import extract_form_suffix
from src.utils.yaml_util import load_mkdocs_config, save_mkdocs_config
import html


class PokemonPageGenerator:
    """
    Generator for individual Pokemon markdown pages.

    Creates detailed pages for each Pokemon including:
    - Basic information (types, abilities, stats)
    - Evolution chain
    - Move learnset
    - Forms and variations
    - Sprites and images
    """

    def __init__(
        self, output_dir: str = "docs/pokedex", project_root: Optional[Path] = None
    ):
        """
        Initialize the Pokemon page generator.

        Args:
            output_dir: Directory where markdown files will be generated
            project_root: The root directory of the project. If None, it's inferred.
        """
        self.logger = get_logger(__name__)

        # Set up paths
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = project_root

        self.output_dir = self.project_root / output_dir / "pokemon"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.logger.debug(
            f"Pokemon page generator initialized. Output: {self.output_dir}"
        )

    def _format_name(self, name: str) -> str:
        """Format a Pokemon name for display (capitalize and handle special cases)."""
        # Handle special characters and formatting
        name = name.replace("-", " ")

        # Special cases for proper capitalization
        special_cases = {
            "nidoran f": "Nidoran♀",
            "nidoran m": "Nidoran♂",
            "mr mime": "Mr. Mime",
            "mime jr": "Mime Jr.",
            "type null": "Type: Null",
            "ho oh": "Ho-Oh",
        }

        lower_name = name.lower()
        if lower_name in special_cases:
            return special_cases[lower_name]

        # Default: title case
        return name.title()

    def _format_type(self, type_name: str) -> str:
        """Format a type name with color badge."""
        type_colors = {
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

        color = type_colors.get(type_name.lower(), "#777777")
        formatted_name = type_name.title()

        return f'<span style="display: inline-block; background-color: {color}; color: white; padding: 4px 12px; border-radius: 6px; font-weight: bold; margin: 2px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">{formatted_name}</span>'

    def _stat_bar(self, value: int, max_value: int = 255) -> str:
        """Create a visual progress bar for a stat."""
        percentage = min(100, (value / max_value) * 100)

        # Color based on value
        if value >= 150:
            color = "#4CAF50"  # Green for high stats
        elif value >= 100:
            color = "#2196F3"  # Blue for good stats
        elif value >= 70:
            color = "#FF9800"  # Orange for medium stats
        else:
            color = "#F44336"  # Red for low stats

        return f'<div style="width: 100%; background-color: #e0e0e0; border-radius: 4px; height: 20px; overflow: hidden;"><div style="width: {percentage}%; background-color: {color}; height: 100%; display: flex; align-items: center; justify-content: flex-end; padding-right: 5px; color: white; font-weight: bold; font-size: 12px;">{value}</div></div>'

    def _format_ability(self, ability_name: str, is_hidden: bool = False) -> str:
        """Format an ability name with link and hidden indicator."""
        formatted_name = self._format_name(ability_name)
        hidden_tag = " *(Hidden)*" if is_hidden else ""
        return f"{formatted_name}{hidden_tag}"

    def _format_form_name(self, pokemon_name: str, base_name: str) -> str:
        """
        Extract and format the form name from a Pokemon's full name.

        Args:
            pokemon_name: Full Pokemon name (e.g., "darmanitan-zen")
            base_name: Base species name (e.g., "darmanitan")

        Returns:
            Formatted form name (e.g., "Zen")
        """
        # Remove base name and leading hyphen
        if pokemon_name.startswith(base_name):
            form_suffix = pokemon_name[len(base_name) :].lstrip("-")
        else:
            form_suffix = pokemon_name

        # If no form suffix, it's the default form
        if not form_suffix:
            return "Standard"

        # Format the form name: replace hyphens with spaces and title case
        formatted_form = form_suffix.replace("-", " ").title()

        return formatted_form

    def _get_type_color(self, type_name: str) -> str:
        """Get the color for a Pokemon type."""
        type_colors = {
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
        return type_colors.get(type_name.lower(), "#777777")

    def _format_move_with_tooltip(self, move_name: str, move_data: Optional[Move]) -> str:
        """Format a move name with type color and tooltip."""
        if not move_data:
            return self._format_name(move_name)

        # Get move type and color
        move_type = move_data.type.black_2_white_2
        type_color = self._get_type_color(move_type) if move_type else "#777"

        # Get flavor text for tooltip
        flavor = move_data.flavor_text.black_2_white_2
        if flavor:
            escaped_flavor = html.escape(flavor)
            style = f"border-bottom: 1px dashed {type_color}; cursor: help; color: {type_color};"
            return f'<span style="{style}" title="{escaped_flavor}">{self._format_name(move_name)}</span>'
        else:
            return f'<span style="color: {type_color};">{self._format_name(move_name)}</span>'

    def _get_type_effectiveness(self, types: List[str]) -> Dict[str, List[str]]:
        """Calculate type effectiveness based on Pokemon's types."""
        # Type effectiveness chart (simplified for Gen 5)
        effectiveness = {
            "normal": {"weak_to": ["fighting"], "resistant_to": [], "immune_to": ["ghost"]},
            "fire": {"weak_to": ["water", "ground", "rock"], "resistant_to": ["fire", "grass", "ice", "bug", "steel", "fairy"], "immune_to": []},
            "water": {"weak_to": ["electric", "grass"], "resistant_to": ["fire", "water", "ice", "steel"], "immune_to": []},
            "electric": {"weak_to": ["ground"], "resistant_to": ["electric", "flying", "steel"], "immune_to": []},
            "grass": {"weak_to": ["fire", "ice", "poison", "flying", "bug"], "resistant_to": ["water", "electric", "grass", "ground"], "immune_to": []},
            "ice": {"weak_to": ["fire", "fighting", "rock", "steel"], "resistant_to": ["ice"], "immune_to": []},
            "fighting": {"weak_to": ["flying", "psychic", "fairy"], "resistant_to": ["bug", "rock", "dark"], "immune_to": []},
            "poison": {"weak_to": ["ground", "psychic"], "resistant_to": ["grass", "fighting", "poison", "bug", "fairy"], "immune_to": []},
            "ground": {"weak_to": ["water", "grass", "ice"], "resistant_to": ["poison", "rock"], "immune_to": ["electric"]},
            "flying": {"weak_to": ["electric", "ice", "rock"], "resistant_to": ["grass", "fighting", "bug"], "immune_to": ["ground"]},
            "psychic": {"weak_to": ["bug", "ghost", "dark"], "resistant_to": ["fighting", "psychic"], "immune_to": []},
            "bug": {"weak_to": ["fire", "flying", "rock"], "resistant_to": ["grass", "fighting", "ground"], "immune_to": []},
            "rock": {"weak_to": ["water", "grass", "fighting", "ground", "steel"], "resistant_to": ["normal", "fire", "poison", "flying"], "immune_to": []},
            "ghost": {"weak_to": ["ghost", "dark"], "resistant_to": ["poison", "bug"], "immune_to": ["normal", "fighting"]},
            "dragon": {"weak_to": ["ice", "dragon", "fairy"], "resistant_to": ["fire", "water", "electric", "grass"], "immune_to": []},
            "dark": {"weak_to": ["fighting", "bug", "fairy"], "resistant_to": ["ghost", "dark"], "immune_to": ["psychic"]},
            "steel": {"weak_to": ["fire", "fighting", "ground"], "resistant_to": ["normal", "grass", "ice", "flying", "psychic", "bug", "rock", "dragon", "steel", "fairy"], "immune_to": ["poison"]},
            "fairy": {"weak_to": ["poison", "steel"], "resistant_to": ["fighting", "bug", "dark"], "immune_to": ["dragon"]},
        }

        # Calculate combined effectiveness
        weak_multiplier = {}
        resist_multiplier = {}
        immune_types = set()

        for poke_type in types:
            type_data = effectiveness.get(poke_type.lower(), {})
            for weak_type in type_data.get("weak_to", []):
                weak_multiplier[weak_type] = weak_multiplier.get(weak_type, 1) * 2
            for resist_type in type_data.get("resistant_to", []):
                resist_multiplier[resist_type] = resist_multiplier.get(resist_type, 1) * 0.5
            for immune_type in type_data.get("immune_to", []):
                immune_types.add(immune_type)

        # Process resistances (some might be neutralized by weaknesses)
        for resist_type, mult in list(resist_multiplier.items()):
            if resist_type in weak_multiplier:
                # Combine multipliers
                combined = weak_multiplier[resist_type] * mult
                if combined > 1:
                    weak_multiplier[resist_type] = combined
                elif combined < 1:
                    resist_multiplier[resist_type] = combined
                else:
                    # Neutral - remove from both
                    weak_multiplier.pop(resist_type, None)
                    resist_multiplier.pop(resist_type, None)
                # Remove from weak since we've combined
                if resist_type in weak_multiplier and resist_type in resist_multiplier:
                    weak_multiplier.pop(resist_type, None)

        # Filter out immunities from weaknesses and resistances
        for immune in immune_types:
            weak_multiplier.pop(immune, None)
            resist_multiplier.pop(immune, None)

        return {
            "4x_weak": [t for t, m in weak_multiplier.items() if m >= 4],
            "2x_weak": [t for t, m in weak_multiplier.items() if m == 2],
            "0.5x_resist": [t for t, m in resist_multiplier.items() if m == 0.5],
            "0.25x_resist": [t for t, m in resist_multiplier.items() if m <= 0.25],
            "immune": list(immune_types),
        }

    def _generate_basic_info(self, pokemon: Pokemon) -> str:
        """Generate the basic information section."""
        md = ""

        # Types in a prominent display
        types_str = " ".join([self._format_type(t) for t in pokemon.types])
        md += f'<div style="text-align: center; margin: 20px 0;">\n{types_str}\n</div>\n\n'

        # Use grid layout for information cards
        md += '<div class="grid cards" markdown>\n\n'

        # Card 1: Abilities
        md += "- **:material-shield-star: Abilities**\n\n"
        md += "    ---\n\n"
        for ability in pokemon.abilities:
            hidden_emoji = " :material-eye-off:" if ability.is_hidden else ""
            # Load ability data for tooltip
            ability_data = PokeDBLoader.load_ability(ability.name)
            if ability_data and ability_data.flavor_text.black_2_white_2:
                flavor = ability_data.flavor_text.black_2_white_2
                escaped_flavor = html.escape(flavor)
                ability_display = f'<span style="border-bottom: 1px dashed #777; cursor: help;" title="{escaped_flavor}">{self._format_name(ability.name)}</span>{hidden_emoji}'
            else:
                ability_display = f"{self._format_name(ability.name)}{hidden_emoji}"
            md += f"    - {ability_display}\n"
        md += "\n"

        # Card 2: Physical Attributes
        height_m = pokemon.height / 10
        weight_kg = pokemon.weight / 10
        md += "- **:material-ruler: Physical Attributes**\n\n"
        md += "    ---\n\n"
        md += f"    **Height:** {height_m:.1f} m\n\n"
        md += f"    **Weight:** {weight_kg:.1f} kg\n\n"
        md += "\n"

        # Card 3: Training Info
        md += "- **:material-book-education: Training**\n\n"
        md += "    ---\n\n"
        md += f"    **Base Happiness:** {pokemon.base_happiness}\n\n"
        md += f"    **Capture Rate:** {pokemon.capture_rate}\n\n"
        md += f"    **Growth Rate:** {self._format_name(pokemon.growth_rate)}\n\n"
        if pokemon.habitat:
            md += f"    **Habitat:** {self._format_name(pokemon.habitat)}\n\n"
        md += "\n"

        # Card 4: Breeding Info
        md += "- **:material-egg: Breeding**\n\n"
        md += "    ---\n\n"
        if pokemon.gender_rate == -1:
            md += "    **Gender:** Genderless\n\n"
        else:
            female_pct = (pokemon.gender_rate / 8) * 100
            male_pct = 100 - female_pct
            md += f"    **Gender Ratio:** {male_pct:.1f}% ♂ / {female_pct:.1f}% ♀\n\n"
        md += f"    **Egg Groups:** {', '.join([self._format_name(eg) for eg in pokemon.egg_groups])}\n\n"
        md += f"    **Hatch Counter:** {pokemon.hatch_counter} cycles\n\n"

        md += "</div>\n\n"

        return md

    def _generate_type_effectiveness(self, pokemon: Pokemon) -> str:
        """Generate the type effectiveness section."""
        md = "## :material-shield-half-full: Type Effectiveness\n\n"

        effectiveness = self._get_type_effectiveness(pokemon.types)

        # Create a visual display of type effectiveness
        has_any = any(effectiveness.values())
        if not has_any:
            md += "*No notable type advantages or disadvantages.*\n\n"
            return md

        # Weaknesses
        if effectiveness["4x_weak"] or effectiveness["2x_weak"]:
            md += "### Weaknesses\n\n"
            if effectiveness["4x_weak"]:
                md += "**4× Damage:** "
                md += " ".join([self._format_type(t) for t in effectiveness["4x_weak"]])
                md += "\n\n"
            if effectiveness["2x_weak"]:
                md += "**2× Damage:** "
                md += " ".join([self._format_type(t) for t in effectiveness["2x_weak"]])
                md += "\n\n"

        # Resistances
        if effectiveness["0.25x_resist"] or effectiveness["0.5x_resist"]:
            md += "### Resistances\n\n"
            if effectiveness["0.25x_resist"]:
                md += "**¼× Damage:** "
                md += " ".join([self._format_type(t) for t in effectiveness["0.25x_resist"]])
                md += "\n\n"
            if effectiveness["0.5x_resist"]:
                md += "**½× Damage:** "
                md += " ".join([self._format_type(t) for t in effectiveness["0.5x_resist"]])
                md += "\n\n"

        # Immunities
        if effectiveness["immune"]:
            md += "### Immunities\n\n"
            md += "**No Damage:** "
            md += " ".join([self._format_type(t) for t in effectiveness["immune"]])
            md += "\n\n"

        return md

    def _generate_stats_table(self, pokemon: Pokemon) -> str:
        """Generate the stats table section with visual bars."""
        md = "## :material-chart-bar: Base Stats\n\n"

        stats_display = [
            ("HP", pokemon.stats.hp),
            ("Attack", pokemon.stats.attack),
            ("Defense", pokemon.stats.defense),
            ("Sp. Atk", pokemon.stats.special_attack),
            ("Sp. Def", pokemon.stats.special_defense),
            ("Speed", pokemon.stats.speed),
        ]

        total = sum([s[1] for s in stats_display])

        # Create a table with stat bars
        md += "| Stat | Value | Bar |\n"
        md += "|------|-------|-----|\n"

        for stat_name, value in stats_display:
            bar = self._stat_bar(value)
            md += f"| **{stat_name}** | {value} | {bar} |\n"

        md += f"| **Total** | **{total}** | |\n\n"

        # EV Yield in an admonition
        if pokemon.ev_yield:
            md += '!!! success "EV Yield"\n'
            for ev in pokemon.ev_yield:
                stat_name = self._format_name(ev.stat)
                md += f"    **+{ev.effort}** {stat_name}\n"
            md += "\n"

        return md

    def _generate_evolution_chain(self, pokemon: Pokemon) -> str:
        """Generate the evolution chain section."""
        md = "## :material-swap-horizontal: Evolution Chain\n\n"

        if pokemon.evolves_from_species:
            md += f'!!! info "Evolution"\n'
            md += f"    Evolves from **{self._format_name(pokemon.evolves_from_species)}**\n\n"

        def format_evolution_node(node, level=0) -> str:
            result = ""
            indent = "  " * level

            # Format the current Pokemon
            display_name = self._format_name(node.species_name)
            result += f"{indent}- **{display_name}**"

            # If this has evolutions, show them
            if node.evolves_to:
                result += "\n"
                for evo in node.evolves_to:
                    # Show evolution method
                    details = []
                    evo_details = evo.evolution_details

                    if evo_details:
                        if evo_details.min_level:
                            details.append(f"Level {evo_details.min_level}")
                        if evo_details.item:
                            details.append(f"Use {self._format_name(evo_details.item)}")
                        if evo_details.held_item:
                            details.append(
                                f"Hold {self._format_name(evo_details.held_item)}"
                            )
                        if evo_details.known_move:
                            details.append(
                                f"Know {self._format_name(evo_details.known_move)}"
                            )
                        if evo_details.min_happiness:
                            details.append(f"Happiness {evo_details.min_happiness}+")
                        if evo_details.time_of_day:
                            details.append(f"During {evo_details.time_of_day}")
                        if evo_details.location:
                            details.append(
                                f"At {self._format_name(evo_details.location)}"
                            )

                    detail_str = ", ".join(details) if details else "Unknown method"
                    result += f"{indent}  → *({detail_str})*\n"
                    result += format_evolution_node(evo, level + 1)
            else:
                result += "\n"

            return result

        md += format_evolution_node(pokemon.evolution_chain)
        md += "\n"

        return md

    def _generate_moves_section(self, pokemon: Pokemon) -> str:
        """Generate the moves learnset section with detailed move information."""
        md = "## :material-sword-cross: Moves\n\n"

        # Damage class icons
        damage_class_icons = {
            "physical": ":material-fist:",
            "special": ":material-star:",
            "status": ":material-shield:",
        }

        # Use tabs for different move categories
        md += '=== ":material-arrow-up-bold: Level-Up"\n\n'
        if pokemon.moves.level_up:
            md += "    | Level | Move | Type | Category | Power | Acc | PP |\n"
            md += "    |-------|------|------|----------|-------|-----|----|\n"

            # Sort by level
            sorted_moves = sorted(
                pokemon.moves.level_up, key=lambda m: m.level_learned_at
            )
            for move_learn in sorted_moves:
                # Load move data
                move_data = PokeDBLoader.load_move(move_learn.name)

                level = move_learn.level_learned_at
                move_name_formatted = self._format_move_with_tooltip(move_learn.name, move_data)

                if move_data:
                    # Get move details
                    move_type = move_data.type.black_2_white_2 or "???"
                    type_badge = self._format_type(move_type)

                    damage_class = move_data.damage_class
                    category_icon = damage_class_icons.get(damage_class, "")

                    power = move_data.power.black_2_white_2
                    power_str = str(power) if power is not None else "—"

                    accuracy = move_data.accuracy.black_2_white_2
                    accuracy_str = str(accuracy) if accuracy is not None else "—"

                    pp = move_data.pp.black_2_white_2
                    pp_str = str(pp) if pp is not None else "—"

                    md += f"    | {level} | {move_name_formatted} | {type_badge} | {category_icon} | {power_str} | {accuracy_str} | {pp_str} |\n"
                else:
                    # Fallback if move data not available
                    md += f"    | {level} | {self._format_name(move_learn.name)} | — | — | — | — | — |\n"
        else:
            md += "    *No level-up moves available*\n"
        md += "\n"

        # TM/HM moves
        md += '=== ":material-disc: TM/HM"\n\n'
        if pokemon.moves.machine:
            md += "    | Move | Type | Category | Power | Acc | PP |\n"
            md += "    |------|------|----------|-------|-----|----|\n"

            # Sort by move name
            sorted_moves = sorted(pokemon.moves.machine, key=lambda m: m.name)
            for move_learn in sorted_moves:
                move_data = PokeDBLoader.load_move(move_learn.name)
                move_name_formatted = self._format_move_with_tooltip(move_learn.name, move_data)

                if move_data:
                    move_type = move_data.type.black_2_white_2 or "???"
                    type_badge = self._format_type(move_type)

                    damage_class = move_data.damage_class
                    category_icon = damage_class_icons.get(damage_class, "")

                    power = move_data.power.black_2_white_2
                    power_str = str(power) if power is not None else "—"

                    accuracy = move_data.accuracy.black_2_white_2
                    accuracy_str = str(accuracy) if accuracy is not None else "—"

                    pp = move_data.pp.black_2_white_2
                    pp_str = str(pp) if pp is not None else "—"

                    md += f"    | {move_name_formatted} | {type_badge} | {category_icon} | {power_str} | {accuracy_str} | {pp_str} |\n"
                else:
                    md += f"    | {self._format_name(move_learn.name)} | — | — | — | — | — |\n"
        else:
            md += "    *No TM/HM moves available*\n"
        md += "\n"

        # Egg moves
        md += '=== ":material-egg-outline: Egg Moves"\n\n'
        if pokemon.moves.egg:
            md += "    | Move | Type | Category | Power | Acc | PP |\n"
            md += "    |------|------|----------|-------|-----|----|\n"

            sorted_moves = sorted(pokemon.moves.egg, key=lambda m: m.name)
            for move_learn in sorted_moves:
                move_data = PokeDBLoader.load_move(move_learn.name)
                move_name_formatted = self._format_move_with_tooltip(move_learn.name, move_data)

                if move_data:
                    move_type = move_data.type.black_2_white_2 or "???"
                    type_badge = self._format_type(move_type)

                    damage_class = move_data.damage_class
                    category_icon = damage_class_icons.get(damage_class, "")

                    power = move_data.power.black_2_white_2
                    power_str = str(power) if power is not None else "—"

                    accuracy = move_data.accuracy.black_2_white_2
                    accuracy_str = str(accuracy) if accuracy is not None else "—"

                    pp = move_data.pp.black_2_white_2
                    pp_str = str(pp) if pp is not None else "—"

                    md += f"    | {move_name_formatted} | {type_badge} | {category_icon} | {power_str} | {accuracy_str} | {pp_str} |\n"
                else:
                    md += f"    | {self._format_name(move_learn.name)} | — | — | — | — | — |\n"
        else:
            md += "    *No egg moves available*\n"
        md += "\n"

        # Tutor moves
        md += '=== ":material-school: Tutor"\n\n'
        if pokemon.moves.tutor:
            md += "    | Move | Type | Category | Power | Acc | PP |\n"
            md += "    |------|------|----------|-------|-----|----|\n"

            sorted_moves = sorted(pokemon.moves.tutor, key=lambda m: m.name)
            for move_learn in sorted_moves:
                move_data = PokeDBLoader.load_move(move_learn.name)
                move_name_formatted = self._format_move_with_tooltip(move_learn.name, move_data)

                if move_data:
                    move_type = move_data.type.black_2_white_2 or "???"
                    type_badge = self._format_type(move_type)

                    damage_class = move_data.damage_class
                    category_icon = damage_class_icons.get(damage_class, "")

                    power = move_data.power.black_2_white_2
                    power_str = str(power) if power is not None else "—"

                    accuracy = move_data.accuracy.black_2_white_2
                    accuracy_str = str(accuracy) if accuracy is not None else "—"

                    pp = move_data.pp.black_2_white_2
                    pp_str = str(pp) if pp is not None else "—"

                    md += f"    | {move_name_formatted} | {type_badge} | {category_icon} | {power_str} | {accuracy_str} | {pp_str} |\n"
                else:
                    md += f"    | {self._format_name(move_learn.name)} | — | — | — | — | — |\n"
        else:
            md += "    *No tutor moves available*\n"
        md += "\n"

        return md

    def _generate_flavor_text(self, pokemon: Pokemon) -> str:
        """Generate the Pokedex flavor text section."""
        md = "## :material-book-open: Pokédex Entries\n\n"

        # Create tabs for different versions
        md += '=== ":material-circle-outline: Black"\n\n'
        if pokemon.flavor_text.black:
            md += f'    !!! quote ""\n'
            md += f"        {pokemon.flavor_text.black}\n\n"

        md += '=== ":material-circle: White"\n\n'
        if pokemon.flavor_text.white:
            md += f'    !!! quote ""\n'
            md += f"        {pokemon.flavor_text.white}\n\n"

        md += '=== ":material-numeric-2-circle-outline: Black 2"\n\n'
        if pokemon.flavor_text.black_2:
            md += f'    !!! quote ""\n'
            md += f"        {pokemon.flavor_text.black_2}\n\n"

        md += '=== ":material-numeric-2-circle: White 2"\n\n'
        if pokemon.flavor_text.white_2:
            md += f'    !!! quote ""\n'
            md += f"        {pokemon.flavor_text.white_2}\n\n"

        return md

    def _generate_sprites_section(self, pokemon: Pokemon) -> str:
        """Generate the sprites section."""
        md = "## :material-image-multiple: Sprites\n\n"

        # Get the Gen 5 animated sprites
        sprites = pokemon.sprites

        md += "### Normal\n\n"
        md += '<div style="display: flex; gap: 20px; justify-content: center;">\n'

        if hasattr(sprites, "versions") and sprites.versions:
            bw = sprites.versions.black_white
            if bw.animated:
                if bw.animated.front_default:
                    md += f'  <img src="{bw.animated.front_default}" alt="Normal Front" />\n'
                if bw.animated.back_default:
                    md += f'  <img src="{bw.animated.back_default}" alt="Normal Back" />\n'

        md += "</div>\n\n"

        md += "### Shiny\n\n"
        md += '<div style="display: flex; gap: 20px; justify-content: center;">\n'

        if hasattr(sprites, "versions") and sprites.versions:
            bw = sprites.versions.black_white
            if bw.animated:
                if bw.animated.front_shiny:
                    md += (
                        f'  <img src="{bw.animated.front_shiny}" alt="Shiny Front" />\n'
                    )
                if bw.animated.back_shiny:
                    md += f'  <img src="{bw.animated.back_shiny}" alt="Shiny Back" />\n'

        md += "</div>\n\n"

        return md

    def generate_pokemon_page(self, pokemon: Pokemon) -> Path:
        """
        Generate a markdown page for a single Pokemon.

        Args:
            pokemon: The Pokemon data to generate a page for

        Returns:
            Path to the generated markdown file
        """
        display_name = self._format_name(pokemon.name)

        # Start building the markdown
        md = f"# {display_name}\n\n"

        # Genus (species classification)
        md += f"*{pokemon.genus}*\n\n"

        # Add Pokedex number
        if "national" in pokemon.pokedex_numbers:
            md += f"**National Dex**: #{pokemon.pokedex_numbers['national']:03d}\n\n"

        # Add sections
        md += self._generate_basic_info(pokemon)
        md += self._generate_type_effectiveness(pokemon)
        md += self._generate_stats_table(pokemon)
        md += self._generate_evolution_chain(pokemon)
        md += self._generate_flavor_text(pokemon)
        md += self._generate_moves_section(pokemon)
        md += self._generate_sprites_section(pokemon)

        # Write to file
        output_file = self.output_dir / f"{pokemon.name}.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated page for {display_name}: {output_file}")
        return output_file

    def generate_all_pokemon_pages(self, subfolder: str = "default") -> List[Path]:
        """
        Generate markdown pages for all Pokemon in the database, including all forms.

        Args:
            subfolder: Subfolder within pokemon directory to process (legacy parameter,
                      now scans all form subfolders)

        Returns:
            List of paths to generated markdown files
        """
        self.logger.info("Starting generation of all Pokemon pages including forms")

        # Get base Pokemon directory
        pokemon_base_dir = self.project_root / "data" / "pokedb" / "parsed" / "pokemon"

        # Subfolders to scan for forms (same as navigation)
        subfolders_to_scan = ["default", "transformation", "variant"]

        generated_files = []
        total_pokemon = 0

        for folder in subfolders_to_scan:
            pokemon_dir = pokemon_base_dir / folder

            if not pokemon_dir.exists():
                self.logger.debug(f"Subfolder not found, skipping: {folder}")
                continue

            pokemon_files = sorted(pokemon_dir.glob("*.json"))
            self.logger.info(
                f"Found {len(pokemon_files)} Pokemon in subfolder: {folder}"
            )
            total_pokemon += len(pokemon_files)

            for pokemon_file in pokemon_files:
                try:
                    pokemon_name = pokemon_file.stem
                    pokemon = PokeDBLoader.load_pokemon(pokemon_name, subfolder=folder)

                    if pokemon:
                        output_path = self.generate_pokemon_page(pokemon)
                        generated_files.append(output_path)
                    else:
                        self.logger.warning(
                            f"Could not load Pokemon: {pokemon_name} from {folder}"
                        )

                except Exception as e:
                    self.logger.error(
                        f"Error generating page for {pokemon_file.stem} in {folder}: {e}",
                        exc_info=True,
                    )

        self.logger.info(
            f"Generated {len(generated_files)} Pokemon pages from {total_pokemon} total Pokemon across all subfolders"
        )
        return generated_files

    def generate_pokedex_index(self, subfolder: str = "default") -> Path:
        """
        Generate the main Pokedex index page with links to all Pokemon.

        Args:
            subfolder: Subfolder within pokemon directory to process

        Returns:
            Path to the generated index file
        """
        self.logger.info("Generating Pokedex index page")

        # Get all Pokemon
        pokemon_dir = (
            self.project_root / "data" / "pokedb" / "parsed" / "pokemon" / subfolder
        )
        pokemon_files = sorted(pokemon_dir.glob("*.json"))

        # Load Pokemon data for the index (deduplicate by identity)
        pokemon_list = []
        seen_pokemon = set()  # Track (dex_number, name) to prevent duplicates

        for pokemon_file in pokemon_files:
            try:
                pokemon = PokeDBLoader.load_pokemon(
                    pokemon_file.stem, subfolder=subfolder
                )
                if (
                    pokemon and pokemon.is_default
                ):  # Only include default forms in main list
                    # Create unique key to prevent duplicates
                    pokemon_key = (
                        pokemon.pokedex_numbers.get("national"),
                        pokemon.name,
                    )

                    if pokemon_key not in seen_pokemon:
                        seen_pokemon.add(pokemon_key)
                        pokemon_list.append(pokemon)
            except Exception as e:
                self.logger.error(f"Error loading {pokemon_file.stem}: {e}")

        # Sort by national dex number
        pokemon_list.sort(key=lambda p: p.pokedex_numbers.get("national", 9999))

        # Generate markdown
        md = "# Pokédex\n\n"
        md += "Complete list of all Pokémon in Blaze Black 2 & Volt White 2 Redux.\n\n"

        # Generate table
        md += "| # | Pokémon | Types | Abilities |\n"
        md += "|---|---------|-------|----------|\n"

        for pokemon in pokemon_list:
            dex_num = pokemon.pokedex_numbers.get("national", "???")
            name = self._format_name(pokemon.name)
            link = f"[{name}](pokemon/{pokemon.name}.md)"
            types = " / ".join([self._format_type(t) for t in pokemon.types])

            # Get non-hidden abilities
            abilities = [a.name for a in pokemon.abilities if not a.is_hidden]
            abilities_str = ", ".join(
                [self._format_name(a) for a in abilities[:2]]
            )  # Show max 2

            md += f"| {dex_num:03d} | {link} | {types} | {abilities_str} |\n"

        md += "\n"

        # Write to file
        output_file = self.output_dir.parent / "pokedex.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated Pokedex index: {output_file}")
        return output_file

    def update_mkdocs_navigation(self, subfolder: str = "default") -> bool:
        """
        Update mkdocs.yml with navigation links to all Pokemon pages.

        Args:
            subfolder: Subfolder within pokemon directory to process

        Returns:
            bool: True if update succeeded, False if it failed
        """
        try:
            mkdocs_path = self.project_root / "mkdocs.yml"

            if not mkdocs_path.exists():
                self.logger.error(f"mkdocs.yml not found at {mkdocs_path}")
                return False

            # Load current mkdocs.yml using utility
            config = load_mkdocs_config(mkdocs_path)

            # Get all Pokemon for navigation from multiple subfolders
            pokemon_base_dir = (
                self.project_root / "data" / "pokedb" / "parsed" / "pokemon"
            )

            # Subfolders to scan for forms (in priority order)
            subfolders_to_scan = ["default", "transformation", "variant"]

            # Load all Pokemon and group by national dex number
            all_pokemon = []
            seen_pokemon = set()  # Track (dex_number, name) to prevent duplicates

            for folder in subfolders_to_scan:
                folder_path = pokemon_base_dir / folder
                if not folder_path.exists():
                    continue

                pokemon_files = sorted(folder_path.glob("*.json"))
                for pokemon_file in pokemon_files:
                    try:
                        pokemon = PokeDBLoader.load_pokemon(
                            pokemon_file.stem, subfolder=folder
                        )
                        if pokemon:
                            # Create unique key to prevent duplicates
                            pokemon_key = (
                                pokemon.pokedex_numbers.get("national"),
                                pokemon.name,
                            )

                            if pokemon_key not in seen_pokemon:
                                seen_pokemon.add(pokemon_key)
                                all_pokemon.append(pokemon)
                    except Exception as e:
                        self.logger.warning(
                            f"Could not load {pokemon_file.stem} from {folder}: {e}"
                        )

            # Group Pokemon by national dex number
            from collections import defaultdict

            pokemon_by_dex: Dict[int, List[Pokemon]] = defaultdict(list)

            for pokemon in all_pokemon:
                dex_num = pokemon.pokedex_numbers.get("national")
                if dex_num:
                    pokemon_by_dex[dex_num].append(pokemon)

            # Sort each group: default form first, then alternates
            for dex_num in pokemon_by_dex:
                pokemon_by_dex[dex_num].sort(key=lambda p: (not p.is_default, p.name))

            # Get sorted list of dex numbers
            sorted_dex_numbers = sorted(pokemon_by_dex.keys())

            # Group Pokemon by generation
            gen_names = [
                ("Gen 1", 1, 151),
                ("Gen 2", 152, 251),
                ("Gen 3", 252, 386),
                ("Gen 4", 387, 493),
                ("Gen 5", 494, 649),
            ]

            # Create navigation structure
            pokedex_nav: Dict[str, List[Dict[str, object]]] = {
                "Pokédex": [{"Overview": "pokedex/pokedex.md"}]
            }

            # Build navigation for each generation
            for gen_name, start, end in gen_names:
                gen_dex_numbers = [
                    dex for dex in sorted_dex_numbers if start <= dex <= end
                ]

                if gen_dex_numbers:
                    gen_nav = []
                    for dex_num in gen_dex_numbers:
                        pokemon_forms = pokemon_by_dex[dex_num]

                        # Get the default form (should be first after sorting)
                        default_form = pokemon_forms[0]
                        base_name = default_form.species

                        # Check if default form has a suffix
                        default_form_suffix = extract_form_suffix(
                            default_form.name, base_name
                        )

                        # Create main entry for default form
                        main_entry = {
                            f"#{dex_num:03d} {self._format_name(default_form.name)}": f"pokedex/pokemon/{default_form.name}.md"
                        }

                        # If there are alternate forms, add them as nested entries
                        if len(pokemon_forms) > 1:
                            # If default form has a suffix, use base species name for main entry
                            # and show all forms (including default) with their suffixes
                            if default_form_suffix:
                                all_forms = []
                                for form in pokemon_forms:
                                    form_display = self._format_form_name(
                                        form.name, base_name
                                    )
                                    all_forms.append(
                                        {
                                            form_display: f"pokedex/pokemon/{form.name}.md"
                                        }
                                    )

                                main_entry = {
                                    f"#{dex_num:03d} {self._format_name(base_name)}": all_forms
                                }
                            else:
                                # Default has no suffix, keep current behavior
                                alternate_forms = []
                                for alt_form in pokemon_forms[1:]:
                                    form_display = self._format_form_name(
                                        alt_form.name, base_name
                                    )
                                    alternate_forms.append(
                                        {
                                            form_display: f"pokedex/pokemon/{alt_form.name}.md"
                                        }
                                    )

                                main_entry = {
                                    f"#{dex_num:03d} {self._format_name(default_form.name)}": [
                                        {
                                            "Default": f"pokedex/pokemon/{default_form.name}.md"
                                        }
                                    ]
                                    + alternate_forms
                                }

                        gen_nav.append(main_entry)

                    pokedex_nav["Pokédex"].append({gen_name: gen_nav})

            # Find and replace Pokédex section in nav
            if "nav" in config:
                # Find the Pokédex entry and replace it
                nav_list = config["nav"]
                pokedex_index = None

                for i, item in enumerate(nav_list):
                    if isinstance(item, dict) and "Pokédex" in item:
                        pokedex_index = i
                        break

                if pokedex_index is not None:
                    nav_list[pokedex_index] = pokedex_nav
                else:
                    # Add Pokédex section if it doesn't exist
                    nav_list.append(pokedex_nav)

                config["nav"] = nav_list

            # Write updated mkdocs.yml using utility
            save_mkdocs_config(mkdocs_path, config)

            total_pokemon = len(sorted_dex_numbers)
            total_forms = len(all_pokemon)
            self.logger.info(
                f"Updated mkdocs.yml with {total_pokemon} Pokemon ({total_forms} total forms including alternates)"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to update mkdocs.yml: {e}", exc_info=True)
            return False
