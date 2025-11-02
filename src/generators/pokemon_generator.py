"""
Generator for individual Pokemon markdown pages.

This generator is specifically designed for Blaze Black 2 & Volt White 2 Redux,
with content prioritizing Black 2 & White 2 data.

This generator:
1. Reads Pokemon data from data/pokedb/parsed/pokemon/
2. Generates individual markdown files for each Pokemon to docs/pokedex/pokemon/
3. Handles Pokemon forms and variations
4. Prioritizes Black 2 & White 2 content (flavor text, etc.)

CSS Styling:
This generator uses CSS classes defined in docs/stylesheets/pokemon.css.
Keep the CSS file in sync when adding new HTML elements or classes.

Key CSS classes used:
- .pokemon-type-badge, .type-{type} - Type badges (see _format_type)
- .pokemon-stat-bar-container, .pokemon-stat-bar-fill - Stat bars (see _stat_bar)
- .pokemon-hero, .pokemon-hero-* - Hero section components (see _generate_hero_section)
- .pokemon-status-badge-* - Legendary/Mythical/Baby badges (see _generate_status_badges)
- .pokemon-sprite-img - Sprite images (see _generate_sprites_section)

Note: Some styles are applied inline when they depend on dynamic data:
- Hero gradient colors (based on Pokemon types)
"""

from pathlib import Path
from typing import Optional, Dict, List, Any, cast
from src.data.pokedb_loader import PokeDBLoader
from src.models.pokedb import Pokemon, Move
from src.utils.markdown_util import format_item
from src.utils.text_util import extract_form_suffix
from src.utils.yaml_util import load_mkdocs_config, save_mkdocs_config
from .base_generator import BaseGenerator


class PokemonGenerator(BaseGenerator):
    """
    Generator for individual Pokemon markdown pages.

    Creates detailed pages for each Pokemon including:
    - Basic information (types, abilities, stats)
    - Evolution chain
    - Move learnset
    - Forms and variations
    - Sprites and images
    """

    # Type colors for badges and styling
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
        Initialize the Pokemon page generator.

        Args:
            output_dir: Directory where markdown files will be generated
            project_root: The root directory of the project. If None, it's inferred.
        """
        # Initialize base generator
        super().__init__(output_dir=output_dir, project_root=project_root)

        # Create pokemon subdirectory
        self.output_dir = self.output_dir / "pokemon"
        self.output_dir.mkdir(parents=True, exist_ok=True)

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
        """
        Format a type name with modern color badge.

        CSS classes used:
        - .pokemon-type-badge: Base badge styling
        - .type-{type}: Type-specific colors (e.g., .type-fire, .type-water)
        """
        formatted_name = type_name.title()
        type_class = f"type-{type_name.lower()}"

        # Use CSS classes for consistent styling
        return f'<span class="pokemon-type-badge {type_class}">{formatted_name}</span>'

    def _stat_bar(self, value: int, max_value: int = 255) -> str:
        """
        Create a modern visual progress bar for a stat.

        CSS classes used:
        - .pokemon-stat-bar-container: Outer container for the bar
        - .pokemon-stat-bar-fill: Inner fill element
        - .stat-bar-{quality}: Color based on value (high/good/medium/low)
        """
        percentage = min(100, (value / max_value) * 100)

        # Determine stat bar class based on value
        if value >= 150:
            bar_class = "stat-bar-high"
        elif value >= 100:
            bar_class = "stat-bar-good"
        elif value >= 70:
            bar_class = "stat-bar-medium"
        else:
            bar_class = "stat-bar-low"

        # Return just the bar without the number (number is shown in the Value column)
        return f'<div class="pokemon-stat-bar-container"><div class="pokemon-stat-bar-fill {bar_class}" style="width: {percentage}%;"></div></div>'

    def _format_ability(self, ability_name: str, is_hidden: bool = False) -> str:
        """Format an ability name with link and hidden indicator."""
        formatted_name = self._format_name(ability_name)
        hidden_tag = " *(Hidden)*" if is_hidden else ""
        return f"{formatted_name}{hidden_tag}"

    def _generate_status_badges(self, pokemon: Pokemon) -> str:
        """
        Generate modern status badges for legendary/mythical/baby Pokemon.

        CSS classes used:
        - .pokemon-status-badge-legendary: Gold gradient for legendary Pokemon
        - .pokemon-status-badge-mythical: Purple gradient for mythical Pokemon
        - .pokemon-status-badge-baby: Pink gradient for baby Pokemon
        """
        badges = []

        if pokemon.is_legendary:
            badges.append(
                '<span class="pokemon-status-badge-legendary">⭐ LEGENDARY</span>'
            )
        elif pokemon.is_mythical:
            badges.append(
                '<span class="pokemon-status-badge-mythical">✨ MYTHICAL</span>'
            )

        if pokemon.is_baby:
            badges.append('<span class="pokemon-status-badge-baby">🍼 BABY</span>')

        return " ".join(badges) if badges else ""

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
        return self.TYPE_COLORS.get(type_name.lower(), "#777777")

    def _format_move_link(self, move_name: str, move_data: Optional[Move]) -> str:
        """
        Format a move name as a link to its page.

        Args:
            move_name: The move identifier (e.g., "thunderbolt")
            move_data: Optional move data (if None, returns plain text)

        Returns:
            Markdown link to move page or plain text if move data unavailable
        """
        if not move_data:
            return self._format_name(move_name)

        # Format display name
        display_name = self._format_name(move_name)

        # Use normalized name from move data for the link
        normalized_name = move_data.name

        # Create link to move page using normalized name (relative from pokemon pages)
        return f"[{display_name}](../moves/{normalized_name}.md)"

    def _get_type_effectiveness(self, types: List[str]) -> Dict[str, List[str]]:
        """Calculate type effectiveness based on Pokemon's types."""
        # Type effectiveness chart (simplified for Gen 5)
        effectiveness = {
            "normal": {
                "weak_to": ["fighting"],
                "resistant_to": [],
                "immune_to": ["ghost"],
            },
            "fire": {
                "weak_to": ["water", "ground", "rock"],
                "resistant_to": ["fire", "grass", "ice", "bug", "steel", "fairy"],
                "immune_to": [],
            },
            "water": {
                "weak_to": ["electric", "grass"],
                "resistant_to": ["fire", "water", "ice", "steel"],
                "immune_to": [],
            },
            "electric": {
                "weak_to": ["ground"],
                "resistant_to": ["electric", "flying", "steel"],
                "immune_to": [],
            },
            "grass": {
                "weak_to": ["fire", "ice", "poison", "flying", "bug"],
                "resistant_to": ["water", "electric", "grass", "ground"],
                "immune_to": [],
            },
            "ice": {
                "weak_to": ["fire", "fighting", "rock", "steel"],
                "resistant_to": ["ice"],
                "immune_to": [],
            },
            "fighting": {
                "weak_to": ["flying", "psychic", "fairy"],
                "resistant_to": ["bug", "rock", "dark"],
                "immune_to": [],
            },
            "poison": {
                "weak_to": ["ground", "psychic"],
                "resistant_to": ["grass", "fighting", "poison", "bug", "fairy"],
                "immune_to": [],
            },
            "ground": {
                "weak_to": ["water", "grass", "ice"],
                "resistant_to": ["poison", "rock"],
                "immune_to": ["electric"],
            },
            "flying": {
                "weak_to": ["electric", "ice", "rock"],
                "resistant_to": ["grass", "fighting", "bug"],
                "immune_to": ["ground"],
            },
            "psychic": {
                "weak_to": ["bug", "ghost", "dark"],
                "resistant_to": ["fighting", "psychic"],
                "immune_to": [],
            },
            "bug": {
                "weak_to": ["fire", "flying", "rock"],
                "resistant_to": ["grass", "fighting", "ground"],
                "immune_to": [],
            },
            "rock": {
                "weak_to": ["water", "grass", "fighting", "ground", "steel"],
                "resistant_to": ["normal", "fire", "poison", "flying"],
                "immune_to": [],
            },
            "ghost": {
                "weak_to": ["ghost", "dark"],
                "resistant_to": ["poison", "bug"],
                "immune_to": ["normal", "fighting"],
            },
            "dragon": {
                "weak_to": ["ice", "dragon", "fairy"],
                "resistant_to": ["fire", "water", "electric", "grass"],
                "immune_to": [],
            },
            "dark": {
                "weak_to": ["fighting", "bug", "fairy"],
                "resistant_to": ["ghost", "dark"],
                "immune_to": ["psychic"],
            },
            "steel": {
                "weak_to": ["fire", "fighting", "ground"],
                "resistant_to": [
                    "normal",
                    "grass",
                    "ice",
                    "flying",
                    "psychic",
                    "bug",
                    "rock",
                    "dragon",
                    "steel",
                    "fairy",
                ],
                "immune_to": ["poison"],
            },
            "fairy": {
                "weak_to": ["poison", "steel"],
                "resistant_to": ["fighting", "bug", "dark"],
                "immune_to": ["dragon"],
            },
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
                resist_multiplier[resist_type] = (
                    resist_multiplier.get(resist_type, 1) * 0.5
                )
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

    def _generate_hero_section(self, pokemon: Pokemon) -> str:
        """
        Generate a modern hero section with sprite, types, and badges.

        CSS classes used:
        - .pokemon-hero: Main hero container with dynamic gradient (inline style)
        - .pokemon-hero-pattern: Decorative pattern overlay
        - .pokemon-hero-content: Content wrapper
        - .pokemon-hero-sprite: Sprite image container
        - .pokemon-dex-number: National dex number display
        - .pokemon-hero-regional-dex: Regional dex badges container (replaces inline style)
        - .pokemon-regional-badge: Individual regional dex badge
        - .pokemon-hero-types: Types container (replaces inline style)
        - .pokemon-hero-status-badges: Status badges container (replaces inline style)

        Note: Hero gradient is applied inline because it's based on the Pokemon's types.
        """
        md = ""

        # Get sprite URL
        sprite_url = None
        if hasattr(pokemon.sprites, "versions") and pokemon.sprites.versions:
            bw = pokemon.sprites.versions.black_white
            if bw.animated and bw.animated.front_default:
                sprite_url = bw.animated.front_default

        # Get type colors for dynamic gradient
        color_1 = "#667eea"  # Default
        color_2 = "#667eea"  # Default

        if pokemon.types:
            color_1 = self.TYPE_COLORS.get(pokemon.types[0].lower(), "#667eea")
            # Default color 2 to a faded version of color 1
            color_2 = f"{color_1}55"

            if len(pokemon.types) > 1:
                # Get the second type color, but fade it slightly
                color_2 = f"{self.TYPE_COLORS.get(pokemon.types[1].lower(), color_1)}99"

        # Modern hero container with dynamic gradient based on type(s)
        md += f'<div class="pokemon-hero" style="background: linear-gradient(135deg, {color_1}dd 0%, {color_2} 100%), linear-gradient(to bottom, rgba(255,255,255,0.1), rgba(0,0,0,0.1));">\n'

        # Subtle pattern overlay
        md += '\t<div class="pokemon-hero-pattern"></div>\n'
        md += '\t<div class="pokemon-hero-content">\n'

        # Sprite with glow effect (fixed scaling)
        if sprite_url:
            md += f'\t\t<div class="pokemon-hero-sprite">\n'
            md += f'\t\t\t<img src="{sprite_url}" alt="{pokemon.name}" />\n'
            md += "\t\t</div>\n"

        # Pokedex number with modern styling
        if "national" in pokemon.pokedex_numbers:
            dex_num = pokemon.pokedex_numbers["national"]
            md += f'\t\t<div class="pokemon-dex-number">#{dex_num:03d}</div>\n'

        # Regional dex numbers with modern badges
        regional_dex = {
            k: v
            for k, v in pokemon.pokedex_numbers.items()
            if k != "national" and v is not None
        }
        if regional_dex:
            dex_badges = []
            for region, number in sorted(regional_dex.items()):
                region_name = self._format_name(region).replace("_", " ")
                dex_badges.append(
                    f'<span class="pokemon-regional-badge">{region_name}: #{number:03d}</span>'
                )
            md += f'\t\t<div class="pokemon-hero-regional-dex">{" ".join(dex_badges)}</div>\n'

        # Types with better spacing
        types_str = " ".join([self._format_type(t) for t in pokemon.types])
        md += f'\t\t<div class="pokemon-hero-types">{types_str}</div>\n'

        # Status badges
        status_badges = self._generate_status_badges(pokemon)
        if status_badges:
            md += f'\t\t<div class="pokemon-hero-status-badges">{status_badges}</div>\n'

        md += "\t</div>\n"  # Close relative div
        md += "</div>\n\n"

        return md

    def _generate_basic_info(self, pokemon: Pokemon) -> str:
        """Generate the basic information section."""
        md = ""

        # Use grid layout for information cards
        md += '<div class="grid cards" markdown>\n\n'

        # Card 1: Abilities
        md += "- **:material-shield-star: Abilities**\n\n"
        md += "\t---\n\n"
        for ability in pokemon.abilities:
            hidden_emoji = " :material-eye-off:" if ability.is_hidden else ""
            # Load ability data to check if it exists and create link
            ability_data = PokeDBLoader.load_ability(ability.name)
            if ability_data:
                display_name = self._format_name(ability.name)
                # Use normalized name from ability_data for the link
                normalized_name = ability_data.name
                ability_display = f"[{display_name}](../abilities/{normalized_name}.md){hidden_emoji}"
            else:
                ability_display = f"{self._format_name(ability.name)}{hidden_emoji}"
            md += f"\t- {ability_display}\n"
        md += "\n"

        # Card 2: Physical Attributes
        height_m = pokemon.height / 10
        weight_kg = pokemon.weight / 10
        md += "- **:material-ruler: Physical Attributes**\n\n"
        md += "\t---\n\n"
        md += f"\t**Height:** {height_m:.1f} m\n\n"
        md += f"\t**Weight:** {weight_kg:.1f} kg\n\n"
        md += "\n"

        # Card 3: Training Info
        md += "- **:material-book-education: Training**\n\n"
        md += "\t---\n\n"
        md += f"\t**Base Experience:** {pokemon.base_experience}\n\n"
        md += f"\t**Base Happiness:** {pokemon.base_happiness}\n\n"
        md += f"\t**Capture Rate:** {pokemon.capture_rate}\n\n"
        md += f"\t**Growth Rate:** {self._format_name(pokemon.growth_rate)}\n\n"
        if pokemon.habitat:
            md += f"\t**Habitat:** {self._format_name(pokemon.habitat)}\n\n"
        # EV Yield
        if pokemon.ev_yield:
            md += "\t**EV Yield:** "
            ev_parts = []
            for ev in pokemon.ev_yield:
                stat_name = self._format_name(ev.stat)
                ev_parts.append(f"+{ev.effort} {stat_name}")
            md += ", ".join(ev_parts) + "\n\n"
        md += "\n"

        # Card 4: Breeding Info
        md += "- **:material-egg: Breeding**\n\n"
        md += "\t---\n\n"
        if pokemon.gender_rate == -1:
            md += "\t**Gender:** Genderless\n\n"
        else:
            female_pct = (pokemon.gender_rate / 8) * 100
            male_pct = 100 - female_pct
            md += f"\t**Gender Ratio:** {male_pct:.1f}% ♂ / {female_pct:.1f}% ♀\n\n"
            if pokemon.has_gender_differences:
                md += "\t**Gender Differences:** Yes\n\n"
        md += f"\t**Egg Groups:** {', '.join([self._format_name(eg) for eg in pokemon.egg_groups])}\n\n"
        md += f"\t**Hatch Counter:** {pokemon.hatch_counter} cycles\n\n"

        # Card 5: Classification
        md += "- **:material-star-four-points: Classification**\n\n"
        md += "\t---\n\n"
        md += f"\t**Generation:** {self._format_name(pokemon.generation)}\n\n"
        md += f"\t**Color:** {self._format_name(pokemon.color)}\n\n"
        md += f"\t**Shape:** {self._format_name(pokemon.shape)}\n\n"
        md += "\n"

        md += "</div>\n\n"

        return md

    def _generate_held_items_section(self, pokemon: Pokemon) -> str:
        """
        Generate the held items section showing what items this Pokemon can hold in the wild.

        Prioritizes Black 2 & White 2 data (the focus of this wiki).
        """
        if not pokemon.held_items:
            return ""

        md = "## :material-treasure-chest: Wild Held Items\n\n"
        md += "These items can be found when catching or defeating this Pokémon in the wild:\n\n"

        # Prioritize Black 2 & White 2 (main focus)
        md += "| Item | Black 2 | White 2 |\n"
        md += "|------|:-------:|:-------:|\n"

        for item_name, rates in pokemon.held_items.items():
            # Convert underscores to hyphens for item identifier
            item_id = item_name.replace("_", "-")
            item_display = format_item(item_id)

            # Get rates for Black 2 & White 2
            black_2_rate = (
                f"{rates.get('black_2', 0)}%" if rates.get("black_2") else "—"
            )
            white_2_rate = (
                f"{rates.get('white_2', 0)}%" if rates.get("white_2") else "—"
            )

            md += f"| {item_display} | {black_2_rate} | {white_2_rate} |\n"

        md += "\n"
        return md

    def _generate_type_effectiveness(self, pokemon: Pokemon) -> str:
        """Generate the type effectiveness section with enhanced visuals."""
        md = "## :material-shield-half-full: Type Effectiveness\n\n"

        effectiveness = self._get_type_effectiveness(pokemon.types)

        # Create a visual display of type effectiveness
        has_any = any(effectiveness.values())
        if not has_any:
            md += "*No notable type advantages or disadvantages.*\n\n"
            return md

        # Use grid layout for better organization
        md += '<div class="grid cards" markdown>\n\n'

        # Weaknesses card
        if effectiveness["4x_weak"] or effectiveness["2x_weak"]:
            md += "- **:material-alert: Weak To**\n\n"
            md += "\t---\n\n"
            if effectiveness["4x_weak"]:
                md += "\t**4× Damage**\n\n"
                md += "\t"
                md += " ".join(
                    [self._format_type(t) for t in sorted(effectiveness["4x_weak"])]
                )
                md += "\n\n"
            if effectiveness["2x_weak"]:
                md += "\t**2× Damage**\n\n"
                md += "\t"
                md += " ".join(
                    [self._format_type(t) for t in sorted(effectiveness["2x_weak"])]
                )
                md += "\n\n"

        # Resistances card
        if effectiveness["0.25x_resist"] or effectiveness["0.5x_resist"]:
            md += "- **:material-shield-check: Resists**\n\n"
            md += "\t---\n\n"
            if effectiveness["0.25x_resist"]:
                md += "\t**¼× Damage**\n\n"
                md += "\t"
                md += " ".join(
                    [
                        self._format_type(t)
                        for t in sorted(effectiveness["0.25x_resist"])
                    ]
                )
                md += "\n\n"
            if effectiveness["0.5x_resist"]:
                md += "\t**½× Damage**\n\n"
                md += "\t"
                md += " ".join(
                    [self._format_type(t) for t in sorted(effectiveness["0.5x_resist"])]
                )
                md += "\n\n"

        # Immunities card
        if effectiveness["immune"]:
            md += "- **:material-shield: Immune To**\n\n"
            md += "\t---\n\n"
            md += "\t**No Damage**\n\n"
            md += "\t"
            md += " ".join(
                [self._format_type(t) for t in sorted(effectiveness["immune"])]
            )
            md += "\n\n"

        md += "</div>\n\n"

        return md

    def _generate_stats_table(self, pokemon: Pokemon) -> str:
        """Generate the stats table section with modern visual bars."""
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
        md += "| Stat | Value | Distribution |\n"
        md += "|------|------:|:-------------|\n"

        for stat_name, value in stats_display:
            bar = self._stat_bar(value)
            md += f"| **{stat_name}** | **{value}** | {bar} |\n"

        # Total
        md += f"| **Base Stat Total** | **{total}** | |\n\n"

        return md

    def _get_sprite_url(self, pokemon_name: str) -> Optional[str]:
        """
        Get the sprite URL for a Pokemon by loading its data.

        Args:
            pokemon_name: The Pokemon's species name

        Returns:
            Sprite URL if found, None otherwise
        """
        try:
            # Try to load from different subfolders
            for subfolder in ["default", "transformation", "variant"]:
                try:
                    poke = PokeDBLoader.load_pokemon(pokemon_name, subfolder=subfolder)
                    if (
                        poke
                        and hasattr(poke.sprites, "versions")
                        and poke.sprites.versions
                    ):
                        bw = poke.sprites.versions.black_white
                        if bw.animated and bw.animated.front_default:
                            return bw.animated.front_default
                except:
                    continue
        except:
            pass
        return None

    def _create_evo_card(self, species_name: str, actual_name: str) -> str:
        """
        Create an evolution card with sprite and name.

        Args:
            species_name: The species name for display
            actual_name: The actual Pokemon name for linking (handles forms)

        Returns:
            HTML string for the evolution card
        """
        display_name = self._format_name(species_name)
        link_name = actual_name or species_name
        sprite_url = self._get_sprite_url(species_name)

        card_html = f'<a href="{link_name}.md" class="pokemon-evo-card">\n'
        if sprite_url:
            card_html += f'\t<img src="{sprite_url}" alt="{display_name}" class="pokemon-evo-sprite" />\n'
        card_html += f'\t<div class="pokemon-evo-name">{display_name}</div>\n'
        card_html += "</a>"

        return card_html

    def _format_evo_method(self, evo_details) -> str:
        """
        Format evolution method details into readable text.

        Args:
            evo_details: Evolution details object

        Returns:
            Formatted evolution method string
        """
        if not evo_details:
            return ""

        details = []
        if evo_details.min_level:
            details.append(f"Level {evo_details.min_level}")
        if evo_details.item:
            details.append(f"Use {self._format_name(evo_details.item)}")
        if evo_details.held_item:
            details.append(f"Hold {self._format_name(evo_details.held_item)}")
        if evo_details.known_move:
            details.append(f"Know {self._format_name(evo_details.known_move)}")
        if evo_details.min_happiness:
            details.append(f"Happiness {evo_details.min_happiness}+")
        if evo_details.time_of_day:
            details.append(f"During {evo_details.time_of_day}")
        if evo_details.location:
            details.append(f"At {self._format_name(evo_details.location)}")

        return "<br>".join(details) if details else "Unknown"

    def _generate_evolution_chain(self, pokemon: Pokemon) -> str:
        """
        Generate the evolution chain section with branching structure.

        Branches only split into separate paths when Pokemon differ.
        Evolution methods are shown under the target Pokemon (the one being evolved TO).
        Branches are organized into columns with max 3 branches per column.

        CSS classes used:
        - .pokemon-evo-chain: Main container
        - .pokemon-evo-path: Horizontal evolution path container
        - .pokemon-evo-branches: Container for all branch columns
        - .pokemon-evo-column: Column of branches (max 3 per column, stacked vertically)
        - .pokemon-evo-branch: A single branch within a column (flows horizontally)
        - .pokemon-evo-item: Container for Pokemon card + evolution method
        - .pokemon-evo-card: Individual Pokemon card with sprite
        - .pokemon-evo-method: Evolution method text (shown under sprite)
        - .pokemon-evo-arrow: Horizontal arrow connector (→)
        """
        md = "## :material-swap-horizontal: Evolution Chain\n\n"

        if pokemon.evolves_from_species:
            md += (
                f"*Evolves from {self._format_name(pokemon.evolves_from_species)}*\n\n"
            )

        def extract_all_paths(node, evolution_method=None) -> list:
            """
            Extract all evolution paths from root to leaves.
            evolution_method is the method used to get TO this node.
            """
            # Get actual Pokemon name
            actual_name = node.species_name
            try:
                for subfolder in ["default", "transformation", "variant"]:
                    try:
                        poke = PokeDBLoader.load_pokemon(
                            node.species_name, subfolder=subfolder
                        )
                        if poke:
                            actual_name = poke.name
                            break
                    except:
                        continue
            except:
                pass

            # Create current Pokemon entry with method to GET TO it
            current_entry = {
                "species_name": node.species_name,
                "actual_name": actual_name,
                "evolution_method": evolution_method,
            }

            # If this is a leaf node (no evolutions), return a path with just this Pokemon
            if not node.evolves_to:
                return [[current_entry]]

            # If has evolutions, recurse for each branch
            all_paths = []
            for evo in node.evolves_to:
                # Get evolution method for this evolution
                method = self._format_evo_method(evo.evolution_details)

                # Get paths from this evolution (with method to get TO that Pokemon)
                branch_paths = extract_all_paths(evo, method)

                # Prepend current Pokemon to each path
                for path in branch_paths:
                    all_paths.append([current_entry] + path)

            return all_paths

        # Extract all evolution paths
        paths = extract_all_paths(pokemon.evolution_chain)

        if not paths:
            return md

        # Find common prefix across all paths
        def find_common_prefix(paths):
            """Find the longest common prefix across all paths by species_name."""
            if not paths:
                return []

            prefix = []
            min_length = min(len(path) for path in paths)

            for i in range(min_length):
                # Check if all paths have the same Pokemon at position i
                first_species = paths[0][i]["species_name"]
                if all(path[i]["species_name"] == first_species for path in paths):
                    prefix.append(paths[0][i])
                else:
                    break

            return prefix

        # Split paths into common prefix and branches
        common_prefix = find_common_prefix(paths)
        prefix_length = len(common_prefix)

        # Get remaining parts after common prefix
        branches = []
        for path in paths:
            if len(path) > prefix_length:
                branches.append(path[prefix_length:])

        # Generate HTML
        md += '<div class="pokemon-evo-chain">\n'
        md += '\t<div class="pokemon-evo-path">\n'

        # Render common prefix horizontally
        for i, poke_data in enumerate(common_prefix):
            md += '\t\t<div class="pokemon-evo-item">\n'
            md += (
                "\t\t\t"
                + self._create_evo_card(
                    poke_data["species_name"], poke_data["actual_name"]
                )
                + "\n"
            )

            # Show evolution method (how to get TO this Pokemon)
            if poke_data["evolution_method"]:
                md += f'\t\t\t<div class="pokemon-evo-method">{poke_data["evolution_method"]}</div>\n'
            elif i == 0:
                # First Pokemon in chain - show "Base"
                md += '\t\t\t<div class="pokemon-evo-method">Base</div>\n'
            else:
                md += '\t\t\t<div class="pokemon-evo-method"></div>\n'

            md += "\t\t</div>\n"

            # Add arrow after if not last in prefix or if there are branches
            if i < len(common_prefix) - 1 or branches:
                md += '\t\t<div class="pokemon-evo-arrow">→</div>\n'

        # Render branches (if any)
        if branches:
            md += '\t\t<div class="pokemon-evo-branches">\n'

            # Organize branches into columns (max 3 per column)
            max_per_column = 3
            num_columns = (len(branches) + max_per_column - 1) // max_per_column

            for col_idx in range(num_columns):
                md += '\t\t\t<div class="pokemon-evo-column">\n'

                # Get branches for this column
                start_idx = col_idx * max_per_column
                end_idx = min(start_idx + max_per_column, len(branches))
                column_branches = branches[start_idx:end_idx]

                for branch in column_branches:
                    md += '\t\t\t\t<div class="pokemon-evo-branch">\n'

                    for i, poke_data in enumerate(branch):
                        md += '\t\t\t\t\t<div class="pokemon-evo-item">\n'
                        md += (
                            "\t\t\t\t\t\t"
                            + self._create_evo_card(
                                poke_data["species_name"], poke_data["actual_name"]
                            )
                            + "\n"
                        )

                        # Show evolution method
                        if poke_data["evolution_method"]:
                            md += f'\t\t\t\t\t\t<div class="pokemon-evo-method">{poke_data["evolution_method"]}</div>\n'
                        elif i == 0 and len(common_prefix) == 0:
                            # First Pokemon in branch and no common prefix - show "Base"
                            md += '\t\t\t\t\t\t<div class="pokemon-evo-method">Base</div>\n'
                        else:
                            md += '\t\t\t\t\t\t<div class="pokemon-evo-method"></div>\n'

                        md += "\t\t\t\t\t</div>\n"

                        # Add arrow if not last in branch
                        if i < len(branch) - 1:
                            md += '\t\t\t\t\t<div class="pokemon-evo-arrow">→</div>\n'

                    md += "\t\t\t\t</div>\n"

                md += "\t\t\t</div>\n"

            md += "\t\t</div>\n"

        md += "\t</div>\n"
        md += "</div>\n\n"

        return md

    def _generate_forms_section(self, pokemon: Pokemon) -> str:
        """
        Generate section showing available forms for this Pokemon.

        Only displays if the Pokemon has multiple forms or if forms are switchable.
        """
        # Don't show if only one form and not switchable
        if len(pokemon.forms) <= 1 and not pokemon.forms_switchable:
            return ""

        md = "## :material-shape: Available Forms\n\n"

        if len(pokemon.forms) > 1:
            md += "This Pokémon has the following forms:\n\n"

            for form in pokemon.forms:
                form_display = self._format_name(form.name)
                category_display = form.category.title()

                # Add icon based on category
                if form.category == "default":
                    icon = ":material-star:"
                elif form.category == "transformation":
                    icon = ":material-swap-horizontal:"
                elif form.category == "variant":
                    icon = ":material-palette:"
                else:  # cosmetic
                    icon = ":material-eye:"

                md += f"- {icon} **{form_display}** ({category_display})\n"
            md += "\n"

        if pokemon.forms_switchable:
            md += "> :material-information: Forms are switchable during gameplay.\n\n"

        return md

    def _generate_move_table(
        self,
        moves: List,
        damage_class_icons: Dict[str, str],
        include_level: bool = False,
        sort_by_level: bool = False,
    ) -> str:
        """
        Generate a move table with formatted move data.

        Args:
            moves: List of move learn objects
            damage_class_icons: Dictionary mapping damage classes to icons
            include_level: Whether to include the level column
            sort_by_level: Whether to sort by level learned (otherwise sort by name)

        Returns:
            Formatted markdown table string
        """
        md = ""

        # Generate header
        if include_level:
            md += "\t| Level | Move | Type | Category | Power | Acc | PP |\n"
            md += "\t|-------|------|------|----------|-------|-----|----|\n"
        else:
            md += "\t| Move | Type | Category | Power | Acc | PP |\n"
            md += "\t|------|------|----------|-------|-----|----|\n"

        # Sort moves
        if sort_by_level:
            sorted_moves = sorted(moves, key=lambda m: m.level_learned_at)
        else:
            sorted_moves = sorted(moves, key=lambda m: m.name)

        # Generate rows
        for move_learn in sorted_moves:
            move_data = PokeDBLoader.load_move(move_learn.name)
            move_name_formatted = self._format_move_link(move_learn.name, move_data)

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

                if include_level:
                    level = move_learn.level_learned_at
                    md += f"\t| {level} | {move_name_formatted} | {type_badge} | {category_icon} | {power_str} | {accuracy_str} | {pp_str} |\n"
                else:
                    md += f"\t| {move_name_formatted} | {type_badge} | {category_icon} | {power_str} | {accuracy_str} | {pp_str} |\n"
            else:
                # Fallback if move data not available
                if include_level:
                    level = move_learn.level_learned_at
                    md += f"\t| {level} | {self._format_name(move_learn.name)} | — | — | — | — | — |\n"
                else:
                    md += f"\t| {self._format_name(move_learn.name)} | — | — | — | — | — |\n"
        md += "\n"

        return md

    def _generate_moves_section(self, pokemon: Pokemon) -> str:
        """Generate the moves learnset section with detailed move information."""
        md = "## :material-sword-cross: Moves\n\n"

        # Damage class icons (using valid Material Design icons)
        damage_class_icons = {
            "physical": ":material-sword:",
            "special": ":material-auto-fix:",
            "status": ":material-shield-outline:",
        }

        # Use tabs for different move categories
        md += '=== ":material-arrow-up-bold: Level-Up"\n\n'
        if pokemon.moves.level_up:
            md += self._generate_move_table(
                pokemon.moves.level_up,
                damage_class_icons,
                include_level=True,
                sort_by_level=True,
            )
        else:
            md += "\t*No level-up moves available*\n\n"

        # TM/HM moves
        md += '=== ":material-disc: TM/HM"\n\n'
        if pokemon.moves.machine:
            md += self._generate_move_table(
                pokemon.moves.machine, damage_class_icons, include_level=False
            )
        else:
            md += "\t*No TM/HM moves available*\n\n"

        # Egg moves
        md += '=== ":material-egg-outline: Egg Moves"\n\n'
        if pokemon.moves.egg:
            md += self._generate_move_table(
                pokemon.moves.egg, damage_class_icons, include_level=False
            )
        else:
            md += "\t*No egg moves available*\n\n"

        # Tutor moves
        md += '=== ":material-school: Tutor"\n\n'
        if pokemon.moves.tutor:
            md += self._generate_move_table(
                pokemon.moves.tutor, damage_class_icons, include_level=False
            )
        else:
            md += "\t*No tutor moves available*\n\n"

        return md

    def _generate_flavor_text(self, pokemon: Pokemon) -> str:
        """
        Generate the Pokédex flavor text section.

        Focuses on Black 2 & White 2 (the main focus of this wiki).
        """
        md = "## :material-book-open: Pokédex Entries\n\n"

        # Pokemon flavor_text uses GameStringMap (individual game versions)
        # Prioritize Black 2 & White 2 since this is a B2W2 Redux wiki
        has_b2w2 = pokemon.flavor_text.black_2 or pokemon.flavor_text.white_2
        has_bw = pokemon.flavor_text.black or pokemon.flavor_text.white

        if has_b2w2:
            # Show Black 2 & White 2 (main focus)
            md += '=== ":material-numeric-2-circle-outline: Black 2"\n\n'
            if pokemon.flavor_text.black_2:
                md += f'\t!!! quote ""\n\n'
                md += f"\t\t{pokemon.flavor_text.black_2}\n\n"
            else:
                md += "\t*No entry available*\n\n"

            md += '=== ":material-numeric-2-circle: White 2"\n\n'
            if pokemon.flavor_text.white_2:
                md += f'\t!!! quote ""\n\n'
                md += f"\t\t{pokemon.flavor_text.white_2}\n\n"
            else:
                md += "\t*No entry available*\n\n"
        else:
            md += "*No Pokédex entries available.*\n\n"

        return md

    def _generate_sprites_section(self, pokemon: Pokemon) -> str:
        """Generate the sprites section with multiple sprite versions."""
        md = "## :material-image-multiple: Sprites\n\n"

        sprites = pokemon.sprites
        has_female_sprites = False

        # Check if this Pokemon has female sprite variants
        if hasattr(sprites, "versions") and sprites.versions:
            bw = sprites.versions.black_white
            if bw.animated and bw.animated.front_female:
                has_female_sprites = True

        # In-game Sprites Tab
        md += '=== "In-Game Sprites"\n\n'

        if hasattr(sprites, "versions") and sprites.versions:
            bw = sprites.versions.black_white
            if bw.animated:
                # Normal sprites
                md += "\t**Normal**\n\n"
                md += '\t<div class="grid cards" markdown>\n\n'

                if bw.animated.front_default:
                    md += f"\t- ![Front]({bw.animated.front_default}){{: .pokemon-sprite-img }}\n\n"
                    md += "\t\t---\n\n"
                    md += "\t\tFront\n\n"
                if bw.animated.back_default:
                    md += f"\t- ![Back]({bw.animated.back_default}){{: .pokemon-sprite-img }}\n\n"
                    md += "\t\t---\n\n"
                    md += "\t\tBack\n\n"

                # Female variants if available
                if has_female_sprites:
                    if bw.animated.front_female:
                        md += f"\t- ![Front ♀]({bw.animated.front_female}){{: .pokemon-sprite-img }}\n\n"
                        md += "\t\t---\n\n"
                        md += "\t\tFront ♀\n\n"
                    if bw.animated.back_female:
                        md += f"\t- ![Back ♀]({bw.animated.back_female}){{: .pokemon-sprite-img }}\n\n"
                        md += "\t\t---\n\n"
                        md += "\t\tBack ♀\n\n"

                md += "\t</div>\n\n"

                # Shiny sprites
                md += "\t**✨ Shiny**\n\n"
                md += '\t<div class="grid cards" markdown>\n\n'

                if bw.animated.front_shiny:
                    md += f"\t- ![Front Shiny]({bw.animated.front_shiny}){{: .pokemon-sprite-img }}\n\n"
                    md += "\t\t---\n\n"
                    md += "\t\tFront\n\n"
                if bw.animated.back_shiny:
                    md += f"\t- ![Back Shiny]({bw.animated.back_shiny}){{: .pokemon-sprite-img }}\n\n"
                    md += "\t\t---\n\n"
                    md += "\t\tBack\n\n"

                # Female shiny variants if available
                if has_female_sprites:
                    if bw.animated.front_shiny_female:
                        md += f"\t- ![Front Shiny ♀]({bw.animated.front_shiny_female}){{: .pokemon-sprite-img }}\n\n"
                        md += "\t\t---\n\n"
                        md += "\t\tFront ♀\n\n"
                    if bw.animated.back_shiny_female:
                        md += f"\t- ![Back Shiny ♀]({bw.animated.back_shiny_female}){{: .pokemon-sprite-img }}\n\n"
                        md += "\t\t---\n\n"
                        md += "\t\tBack ♀\n\n"

                md += "\t</div>\n\n"

        # Official Artwork Tab
        md += '=== "Official Artwork"\n\n'

        if (
            hasattr(sprites, "other")
            and sprites.other
            and hasattr(sprites.other, "official_artwork")
        ):
            artwork = sprites.other.official_artwork

            md += '\t<div class="grid cards" markdown>\n\n'

            # Normal artwork
            if artwork.front_default:
                md += f"\t- ![Official Artwork]({artwork.front_default})\n\n"
                md += "\t\t---\n\n"
                md += "\t\tNormal\n\n"

            # Shiny artwork
            if artwork.front_shiny:
                md += f"\t- ![Shiny Official Artwork]({artwork.front_shiny})\n\n"
                md += "\t\t---\n\n"
                md += "\t\t✨ Shiny\n\n"

            md += "\t</div>\n\n"

        # Pokemon cry audio player
        md += "---\n\n"
        md += "### :material-volume-high: Cry\n\n"

        if hasattr(pokemon, "cries") and pokemon.cries:
            # Prefer legacy cry, fallback to latest
            cry_url = getattr(pokemon.cries, "legacy", None) or getattr(
                pokemon.cries, "latest", None
            )

            if cry_url:
                md += f'<audio controls style="width: 100%; max-width: 500px;">\n'
                md += f'\t<source src="{cry_url}" type="audio/ogg">\n'
                md += "\tYour browser does not support the audio element.\n"
                md += "</audio>\n\n"
        else:
            md += "*Cry audio is not currently available for this Pokémon.*\n\n"

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

        # Hero section with sprite, types, and badges
        md += self._generate_hero_section(pokemon)

        # Add sections
        md += self._generate_basic_info(pokemon)
        md += self._generate_held_items_section(pokemon)
        md += self._generate_type_effectiveness(pokemon)
        md += self._generate_stats_table(pokemon)
        md += self._generate_evolution_chain(pokemon)
        md += self._generate_forms_section(pokemon)
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
        md += "Complete list of all Pokémon in **Blaze Black 2 & Volt White 2 Redux**.\n\n"
        md += "> Click on any Pokémon to see detailed stats, moves, evolutions, and more.\n\n"

        # Group Pokemon by generation
        gen_definitions = [
            ("Generation I", 1, 151, ":material-numeric-1-circle:"),
            ("Generation II", 152, 251, ":material-numeric-2-circle:"),
            ("Generation III", 252, 386, ":material-numeric-3-circle:"),
            ("Generation IV", 387, 493, ":material-numeric-4-circle:"),
            ("Generation V", 494, 649, ":material-numeric-5-circle:"),
        ]

        for gen_name, start, end, icon in gen_definitions:
            # Filter Pokemon for this generation
            gen_pokemon = [
                p
                for p in pokemon_list
                if start <= p.pokedex_numbers.get("national", 0) <= end
            ]

            if not gen_pokemon:
                continue

            # Add generation header
            md += f"## {icon} {gen_name}\n\n"
            md += f"*National Dex #{start:03d} - #{end:03d}*\n\n"

            # Generate table for this generation
            md += "| # | Sprite | Pokémon | Types | Abilities |\n"
            md += "|:---:|:---:|---------|-------|----------|\n"

            for pokemon in gen_pokemon:
                dex_num = pokemon.pokedex_numbers.get("national", "???")
                name = self._format_name(pokemon.name)
                link = f"[{name}](pokemon/{pokemon.name}.md)"
                # Stack types vertically if multiple types
                types = "<br>".join([self._format_type(t) for t in pokemon.types])

                # Get sprite URL
                sprite_url = None
                if hasattr(pokemon.sprites, "versions") and pokemon.sprites.versions:
                    bw = pokemon.sprites.versions.black_white
                    if bw.animated and bw.animated.front_default:
                        sprite_url = bw.animated.front_default

                # Create sprite cell
                if sprite_url:
                    sprite_cell = f'<img src="{sprite_url}" alt="{name}" class="pokemon-sprite-img" style="max-width: 80px; image-rendering: pixelated;" />'
                else:
                    sprite_cell = "—"

                # Get non-hidden abilities
                abilities = [a.name for a in pokemon.abilities if not a.is_hidden]
                abilities_str = ", ".join(
                    [self._format_name(a) for a in abilities[:2]]
                )  # Show max 2

                md += f"| **{dex_num:03d}** | {sprite_cell} | {link} | {types} | {abilities_str} |\n"

            md += "\n"

        # Write to file
        output_file = self.output_dir.parent / "pokemon.md"
        output_file.write_text(md, encoding="utf-8")

        self.logger.info(f"Generated Pokemon index: {output_file}")
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

            # Group Pokemon by national dex number first for form handling
            from collections import defaultdict

            pokemon_by_dex: Dict[int, List[Pokemon]] = defaultdict(list)

            for pokemon in all_pokemon:
                dex_num = pokemon.pokedex_numbers.get("national")
                if dex_num:
                    pokemon_by_dex[dex_num].append(pokemon)

            # Sort each group: default form first, then alternates
            for dex_num in pokemon_by_dex:
                pokemon_by_dex[dex_num].sort(key=lambda p: (not p.is_default, p.name))

            # Group Pokemon by generation attribute
            pokemon_by_generation: Dict[str, Dict[int, List[Pokemon]]] = defaultdict(lambda: defaultdict(list))

            for dex_num, pokemon_forms in pokemon_by_dex.items():
                # Use the generation from the default form
                default_form = pokemon_forms[0]
                gen = default_form.generation if default_form.generation else "unknown"
                pokemon_by_generation[gen][dex_num] = pokemon_forms

            # Generation display name mapping and order
            generation_display_names = {
                "generation-i": "Gen I",
                "generation-ii": "Gen II",
                "generation-iii": "Gen III",
                "generation-iv": "Gen IV",
                "generation-v": "Gen V",
            }
            generation_order = ["generation-i", "generation-ii", "generation-iii", "generation-iv", "generation-v"]

            # Create navigation structure for Pokémon subsection
            pokemon_nav_items = [{"Overview": "pokedex/pokemon.md"}]

            # Build navigation for each generation
            for gen_key in generation_order:
                if gen_key not in pokemon_by_generation:
                    continue

                display_name = generation_display_names.get(gen_key, gen_key)
                gen_pokemon_by_dex = pokemon_by_generation[gen_key]
                sorted_dex_numbers = sorted(gen_pokemon_by_dex.keys())

                gen_nav = []
                for dex_num in sorted_dex_numbers:
                    pokemon_forms = gen_pokemon_by_dex[dex_num]

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

                # Using type: ignore because mkdocs nav allows mixed dict value types
                pokemon_nav_items.append({display_name: gen_nav})  # type: ignore

            # Add unknown generation Pokemon if any exist
            if "unknown" in pokemon_by_generation:
                unknown_pokemon_by_dex = pokemon_by_generation["unknown"]
                sorted_unknown_dex = sorted(unknown_pokemon_by_dex.keys())
                unknown_nav = []
                for dex_num in sorted_unknown_dex:
                    pokemon_forms = unknown_pokemon_by_dex[dex_num]
                    default_form = pokemon_forms[0]
                    unknown_nav.append({
                        f"#{dex_num:03d} {self._format_name(default_form.name)}": f"pokedex/pokemon/{default_form.name}.md"
                    })
                pokemon_nav_items.append({"Unknown": unknown_nav})  # type: ignore

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

            # Ensure typing is flexible for mixed nav entry value types
            pokedex_nav = cast(List[Dict[str, Any]], pokedex_nav)

            # Find or create Pokémon subsection within Pokédex
            pokemon_subsection_index = None
            for i, item in enumerate(pokedex_nav):
                if isinstance(item, dict) and "Pokémon" in item:
                    pokemon_subsection_index = i
                    break

            # Update or append Pokémon subsection
            pokemon_subsection = {"Pokémon": pokemon_nav_items}
            if pokemon_subsection_index is not None:
                pokedex_nav[pokemon_subsection_index] = pokemon_subsection
            else:
                # Prepend Pokémon subsection as the first item
                pokedex_nav.insert(0, pokemon_subsection)

            # Update the config
            nav_list[pokedex_index] = {"Pokédex": pokedex_nav}
            config["nav"] = nav_list

            # Write updated mkdocs.yml using utility
            save_mkdocs_config(mkdocs_path, config)

            total_pokemon = len(pokemon_by_dex)
            total_forms = len(all_pokemon)
            total_generations = len([g for g in generation_order if g in pokemon_by_generation])
            self.logger.info(
                f"Updated mkdocs.yml with {total_pokemon} Pokemon ({total_forms} total forms including alternates) organized into {total_generations} generations"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to update mkdocs.yml: {e}", exc_info=True)
            return False

    def generate(self, subfolder: str = "default") -> bool:
        """
        Generate Pokemon pages and Pokedex index.

        Args:
            subfolder: Subfolder within pokemon directory to process

        Returns:
            bool: True if generation succeeded, False if it failed
        """
        self.logger.info("Starting Pokedex generation...")
        try:
            # Generate all Pokemon pages
            self.logger.info("Generating individual Pokemon pages...")
            pokemon_files = self.generate_all_pokemon_pages(subfolder=subfolder)

            if not pokemon_files:
                self.logger.error("No Pokemon pages were generated")
                return False

            # Generate the Pokedex index
            self.logger.info("Generating Pokedex index...")
            index_path = self.generate_pokedex_index(subfolder=subfolder)

            # Update mkdocs.yml navigation
            self.logger.info("Updating mkdocs.yml navigation...")
            nav_success = self.update_mkdocs_navigation(subfolder=subfolder)

            if not nav_success:
                self.logger.warning(
                    "Failed to update mkdocs.yml navigation, but pages were generated successfully"
                )

            self.logger.info(
                f"Successfully generated {len(pokemon_files)} Pokemon pages and index"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate Pokedex: {e}", exc_info=True)
            return False
