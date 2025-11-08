"""
Generator for location markdown pages.

This generator creates comprehensive location documentation pages with data
from trainer battles and wild encounters.

This generator:
1. Reads location data from data/locations/
2. Generates individual markdown files for each location to docs/locations/
3. Includes trainer battles, wild encounters, and hidden grottos
4. Supports nested sublocations
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.core.config import GENERATOR_DEX_RELATIVE_PATH
from src.utils.core.logger import get_logger
from src.utils.formatters.markdown_formatter import (
    format_ability,
    format_item,
    format_move,
    format_pokemon,
    format_pokemon_card_grid,
    format_type_badge,
)
from src.utils.formatters.yaml_formatter import update_mkdocs_nav


class LocationGenerator:
    """
    Generator for location markdown pages.

    Creates detailed pages for each location including:
    - Trainer battles with full team details
    - Wild encounters by method (grass, surf, fishing, etc.)
    - Hidden Grotto encounters
    - Nested sublocations

    This generator does not inherit from BaseGenerator as it works with
    location data rather than pokedex data.
    """

    def __init__(
        self,
        output_dir: str = "docs/locations",
        input_dir: str = "data/locations",
        project_root: Optional[Path] = None,
    ):
        """Initialize the Location page generator.

        Args:
            output_dir (str, optional): Directory where markdown files will be generated. Defaults to "docs/locations".
            input_dir (str, optional): Directory where location JSON files are stored. Defaults to "data/locations".
            project_root (Optional[Path], optional): The root directory of the project. If None, it's inferred.
        """
        # Set up logger
        self.logger = get_logger(self.__class__.__module__)

        # Set up paths
        if project_root is None:
            project_root = Path.cwd()
        self.project_root = Path(project_root)
        self.input_dir = self.project_root / input_dir
        self.output_dir = self.project_root / output_dir

        # Individual location pages go in data/ subdirectory
        self.data_dir = self.output_dir / "data"

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.logger.debug(f"Initializing generator: {self.__class__.__name__}")
        self.logger.debug(f"Input directory: {self.input_dir}")
        self.logger.debug(f"Output directory: {self.output_dir}")
        self.logger.debug(f"Data directory: {self.data_dir}")

    def _clear_old_files(self) -> None:
        """Clear old location markdown files from the data directory."""
        self.logger.info("Clearing old location files...")
        count = 0
        for old_file in self.data_dir.glob("*.md"):
            old_file.unlink()
            count += 1
        self.logger.debug(f"Removed {count} old location files")

    def generate_all(self) -> bool:
        """Generate markdown pages for all locations.

        Returns:
            bool: True if the generation was successful.
        """
        self.logger.info("Generating all location pages...")

        # Clear old files first
        self._clear_old_files()

        generated_files = []
        location_data_list = []

        # Load all location JSON files
        location_files = sorted(self.input_dir.glob("*.json"))
        self.logger.info(f"Found {len(location_files)} location files")

        for location_file in location_files:
            try:
                # Load location data for overview page
                with open(location_file, "r", encoding="utf-8") as f:
                    location_data = json.load(f)
                    location_data_list.append((location_file.stem, location_data))

                # Generate individual location page
                output_path = self._generate_location_page(location_file, location_data)
                if output_path:
                    generated_files.append(output_path)
            except Exception as e:
                self.logger.error(
                    f"Failed to generate page for {location_file.name}: {e}"
                )
                return False

        # Generate overview page
        overview_path = self._generate_overview_page(location_data_list)
        generated_files.append(overview_path)

        # Update mkdocs.yml navigation
        self._update_mkdocs_nav(location_data_list)

        self.logger.info(f"Generated {len(generated_files)} location pages")
        return True

    def _generate_location_page(
        self, location_file: Path, location_data: Dict[str, Any]
    ) -> Optional[Path]:
        """Generate a markdown page for a single location.

        Args:
            location_file (Path): Path to the location JSON file.
            location_data (Dict[str, Any]): The location data dictionary.

        Returns:
            Optional[Path]: Path to the generated markdown file, or None if generation failed.
        """
        location_name = location_data.get("name", location_file.stem)
        self.logger.debug(f"Generating page for: {location_name}")

        # Build markdown content
        markdown = self._build_location_markdown(location_data)

        # Write to file in data/ subdirectory
        output_filename = f"{location_file.stem}.md"
        output_path = self.data_dir / output_filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        self.logger.debug(f"Saved markdown to: {output_path}")
        return output_path

    def _build_location_markdown(self, location_data: Dict[str, Any]) -> str:
        """Build markdown content for a location.

        Args:
            location_data (Dict[str, Any]): The location data dictionary.

        Returns:
            str: The complete markdown content.
        """
        markdown = f"# {location_data['name']}\n\n"

        # Check if there are sublocations
        has_sublocations = bool(location_data.get("sublocations"))

        # Check if main area has any content
        has_main_content = (
            location_data.get("trainers")
            or location_data.get("wild_encounters")
            or location_data.get("hidden_grotto")
        )

        # If there are sublocations and main content, add "Main Area" header
        if has_sublocations and has_main_content:
            markdown += "## Main Area\n\n"
            # Add location description after "Main Area" heading
            if location_data.get("description"):
                markdown += f"{location_data['description']}\n\n"
            trainer_header = "###"
            encounter_header = "###"
            grotto_header = "###"
        else:
            # Add location description after location title if no sublocations
            if location_data.get("description"):
                markdown += f"{location_data['description']}\n\n"
            trainer_header = "##"
            encounter_header = "##"
            grotto_header = "##"

        # Add trainers section
        if location_data.get("trainers"):
            markdown += f"{trainer_header} Trainers\n\n"
            # Add trainer notes (level adjustments, etc.) after Trainers heading
            if location_data.get("trainer_notes"):
                markdown += f"{location_data['trainer_notes']}\n\n"
            markdown += self._build_trainers_section(location_data["trainers"])

        # Add wild encounters section
        if location_data.get("wild_encounters"):
            markdown += f"{encounter_header} Wild Encounters\n\n"
            markdown += self._build_wild_encounters_section(
                location_data["wild_encounters"]
            )

        # Add hidden grotto section
        if location_data.get("hidden_grotto"):
            markdown += f"{grotto_header} Hidden Grotto\n\n"
            markdown += self._build_hidden_grotto_section(
                location_data["hidden_grotto"]
            )

        # Add sublocations
        if location_data.get("sublocations"):
            markdown += self._build_sublocations_section(location_data["sublocations"])

        return markdown

    def _build_sublocations_section(
        self, sublocations: Dict[str, Any], depth: int = 2
    ) -> str:
        """Build markdown content for sublocations.

        Args:
            sublocations (Dict[str, Any]): Dictionary of sublocations.
            depth (int, optional): Current nesting depth for headers. Defaults to 2.

        Returns:
            str: Markdown content for sublocations.
        """
        markdown = ""
        heading = "#" * depth

        for sublocation_name, sublocation_data in sublocations.items():
            markdown += f"{heading} {sublocation_name}\n\n"

            # Add sublocation description if it exists
            if sublocation_data.get("description"):
                markdown += f"{sublocation_data['description']}\n\n"

            # Add trainers for this sublocation
            if sublocation_data.get("trainers"):
                markdown += f"{'#' * (depth + 1)} Trainers\n\n"
                # Add trainer notes (level adjustments, etc.) after Trainers heading
                if sublocation_data.get("trainer_notes"):
                    markdown += f"{sublocation_data['trainer_notes']}\n\n"
                markdown += self._build_trainers_section(sublocation_data["trainers"])

            # Add wild encounters for this sublocation
            if sublocation_data.get("wild_encounters"):
                markdown += f"{'#' * (depth + 1)} Wild Encounters\n\n"
                markdown += self._build_wild_encounters_section(
                    sublocation_data["wild_encounters"]
                )

            # Add hidden grotto for this sublocation
            if sublocation_data.get("hidden_grotto"):
                markdown += f"{'#' * (depth + 1)} Hidden Grotto\n\n"
                markdown += self._build_hidden_grotto_section(
                    sublocation_data["hidden_grotto"]
                )

            # Recursively handle nested sublocations
            if sublocation_data.get("sublocations"):
                markdown += self._build_sublocations_section(
                    sublocation_data["sublocations"], depth + 1
                )

        return markdown

    def _build_trainers_section(self, trainers: List[Dict[str, Any]]) -> str:
        """Build markdown content for trainers.

        Args:
            trainers (List[Dict[str, Any]]): List of trainer data.

        Returns:
            str: Markdown content for trainers.
        """
        markdown = ""

        for trainer in trainers:
            # Trainer header
            markdown += f"{trainer['name']}\n\n"

            # Trainer metadata
            if trainer.get("reward"):
                markdown += "**Reward:** "
                markdown += ", ".join(
                    format_item(item, relative_path=GENERATOR_DEX_RELATIVE_PATH)
                    for item in trainer["reward"]
                )
                markdown += "\n\n"

            if trainer.get("mode"):
                markdown += f"**Mode:** {trainer['mode']}\n\n"

            if trainer.get("battle_type"):
                markdown += f"**Battle Type:** {trainer['battle_type']}\n\n"

            # Handle starter variations
            if trainer.get("starter_variations"):
                for starter, variation in trainer["starter_variations"].items():
                    markdown += f'=== "{starter}"\n\n'
                    markdown += self._build_team_table(variation["team"], indent=1)
            else:
                # Regular team
                markdown += self._build_team_table(trainer["team"])

        return markdown

    def _build_team_table(self, team: List[Dict[str, Any]], indent: int = 0) -> str:
        """Build a markdown table for a trainer's team.

        Args:
            team (List[Dict[str, Any]]): List of Pokemon in the team.
            indent (int, optional): Indentation level (tabs). Defaults to 0.

        Returns:
            str: Markdown table for the team.
        """
        if not team:
            return ""

        tab = "\t" * indent
        markdown = f"{tab}| Pokémon | Type(s) | Attributes | Moves |\n"
        markdown += f"{tab}|:-------:|:-------:|:-----------|:------|\n"

        for pokemon in team:
            # Pokemon column
            row = f"{tab}| {format_pokemon(pokemon['pokemon'], relative_path=GENERATOR_DEX_RELATIVE_PATH)} | "

            # Type(s) column
            badges = " ".join(format_type_badge(t) for t in pokemon["types"])
            row += f"<div class='badges-vstack'>{badges}</div> | "

            # Attributes column
            row += f"**Level:** {pokemon['level']}"
            row += f"<br>**Ability:** {format_ability(pokemon['ability'], relative_path=GENERATOR_DEX_RELATIVE_PATH)}"
            if pokemon.get("item"):
                row += f"<br>**Item:** {format_item(pokemon['item'], relative_path=GENERATOR_DEX_RELATIVE_PATH)}"
            row += " | "

            # Moves column
            for i, move in enumerate(pokemon["moves"]):
                if i > 0:
                    row += "<br>"
                row += f"{i + 1}. {format_move(move, relative_path=GENERATOR_DEX_RELATIVE_PATH)}"

            markdown += row + " |\n"

        markdown += "\n"
        return markdown

    def _build_wild_encounters_section(
        self, wild_encounters: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """Build markdown content for wild encounters.

        Args:
            wild_encounters (Dict[str, List[Dict[str, Any]]]): Wild encounters by method.

        Returns:
            str: Markdown content for wild encounters.
        """
        markdown = ""

        for method, encounters in wild_encounters.items():
            markdown += f"{method}\n\n"
            markdown += "| Pokémon | Type(s) | Level(s) | Chance |\n"
            markdown += "|:-------:|:-------:|:---------|:-------|\n"

            for encounter in encounters:
                pokemon_md = format_pokemon(
                    encounter["pokemon"], relative_path=GENERATOR_DEX_RELATIVE_PATH
                )

                # Types
                if encounter.get("types"):
                    types_md = "<div class='badges-vstack'>"
                    types_md += " ".join(
                        format_type_badge(t) for t in encounter["types"]
                    )
                    types_md += "</div>"
                else:
                    types_md = "—"

                # Chance
                if encounter.get("chance") is not None:
                    chance_md = f"{encounter['chance']}%"
                else:
                    chance_md = "—"

                markdown += f"| {pokemon_md} | {types_md} | {encounter['level']} | {chance_md} |\n"

            markdown += "\n"

        return markdown

    def _build_hidden_grotto_section(
        self, hidden_grotto: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """Build markdown content for hidden grotto encounters.

        Args:
            hidden_grotto (Dict[str, List[Dict[str, Any]]]): Hidden grotto encounters by type.

        Returns:
            str: Markdown content for hidden grotto encounters.
        """
        markdown = ""

        for encounter_type, encounters in hidden_grotto.items():
            markdown += f'=== "{encounter_type}"\n\n'

            pokemon_encounters = [e["pokemon"] for e in encounters]
            pokemon_cards = format_pokemon_card_grid(
                pokemon_encounters,
                relative_path="../../pokedex/pokemon",
                extra_info=[f"*{encounter_type.split(' ')[0]}*"]
                * len(pokemon_encounters),
            )
            markdown += f"{'\n'.join(f'\t{l}'.rstrip() for l in pokemon_cards.splitlines())}\n\n"

        return markdown

    def _generate_overview_page(
        self, location_data_list: List[tuple[str, Dict[str, Any]]]
    ) -> Path:
        """Generate the overview/index page for all locations.

        Args:
            location_data_list (List[tuple[str, Dict[str, Any]]]): List of (filename_stem, location_data) tuples.

        Returns:
            Path: Path to the generated overview markdown file.
        """
        self.logger.info("Generating locations overview page...")

        # Start markdown
        markdown = "# Locations\n\n"
        markdown += "Browse all locations in the game.\n\n"

        # Group locations by type (you could categorize them if needed)
        # For now, just create an alphabetical list
        markdown += "## All Locations\n\n"
        markdown += "| Location | Trainers | Wild Encounters | Hidden Grotto |\n"
        markdown += "|:---------|:--------:|:---------------:|:-------------:|\n"

        # Sort by display name
        sorted_locations = sorted(
            location_data_list, key=lambda x: x[1].get("name", x[0])
        )

        for filename_stem, location_data in sorted_locations:
            location_name = location_data.get("name", filename_stem)
            link = f"[{location_name}](data/{filename_stem}.md)"

            # Count trainers (including sublocations)
            trainer_count = self._count_trainers(location_data)
            trainer_str = str(trainer_count) if trainer_count > 0 else "—"

            # Check for wild encounters
            has_wild = bool(location_data.get("wild_encounters"))
            # Also check sublocations for wild encounters
            if not has_wild and location_data.get("sublocations"):
                has_wild = self._has_wild_encounters_in_sublocations(
                    location_data["sublocations"]
                )
            wild_str = "✓" if has_wild else "—"

            # Check for hidden grotto
            has_grotto = bool(location_data.get("hidden_grotto"))
            # Also check sublocations
            if not has_grotto and location_data.get("sublocations"):
                has_grotto = self._has_hidden_grotto_in_sublocations(
                    location_data["sublocations"]
                )
            grotto_str = "✓" if has_grotto else "—"

            markdown += f"| {link} | {trainer_str} | {wild_str} | {grotto_str} |\n"

        markdown += "\n"

        # Write to file
        output_path = self.output_dir / "locations.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        self.logger.info(f"Generated overview page: {output_path}")
        return output_path

    def _count_trainers(self, location_data: Dict[str, Any]) -> int:
        """Count total trainers in a location including sublocations.

        Args:
            location_data (Dict[str, Any]): The location data dictionary.

        Returns:
            int: Total number of trainers.
        """
        count = len(location_data.get("trainers", []))

        # Recursively count trainers in sublocations
        if location_data.get("sublocations"):
            for sublocation in location_data["sublocations"].values():
                count += self._count_trainers(sublocation)

        return count

    def _has_wild_encounters_in_sublocations(
        self, sublocations: Dict[str, Any]
    ) -> bool:
        """Check if any sublocation has wild encounters.

        Args:
            sublocations (Dict[str, Any]): Dictionary of sublocations.

        Returns:
            bool: True if any sublocation has wild encounters.
        """
        for sublocation in sublocations.values():
            if sublocation.get("wild_encounters"):
                return True
            if sublocation.get("sublocations"):
                if self._has_wild_encounters_in_sublocations(
                    sublocation["sublocations"]
                ):
                    return True
        return False

    def _has_hidden_grotto_in_sublocations(self, sublocations: Dict[str, Any]) -> bool:
        """Check if any sublocation has hidden grotto.

        Args:
            sublocations (Dict[str, Any]): Dictionary of sublocations.

        Returns:
            bool: True if any sublocation has hidden grotto.
        """
        for sublocation in sublocations.values():
            if sublocation.get("hidden_grotto"):
                return True
            if sublocation.get("sublocations"):
                if self._has_hidden_grotto_in_sublocations(sublocation["sublocations"]):
                    return True
        return False

    def _update_mkdocs_nav(
        self, location_data_list: List[tuple[str, Dict[str, Any]]]
    ) -> bool:
        """Update mkdocs.yml navigation with locations.

        Args:
            location_data_list (List[tuple[str, Dict[str, Any]]]): List of (filename_stem, location_data) tuples.

        Returns:
            bool: True if update succeeded, False otherwise.
        """
        try:
            self.logger.info("Updating mkdocs.yml navigation for locations...")
            mkdocs_path = self.project_root / "mkdocs.yml"

            # Sort by display name
            sorted_locations = sorted(
                location_data_list, key=lambda x: x[1].get("name", x[0])
            )

            # Create navigation structure
            nav_items = [{"Overview": "locations/locations.md"}]

            # Add all locations
            for filename_stem, location_data in sorted_locations:
                location_name = location_data.get("name", filename_stem)
                nav_items.append({location_name: f"locations/data/{filename_stem}.md"})

            # Use shared utility to update mkdocs navigation
            success = update_mkdocs_nav(mkdocs_path, {"Locations": nav_items})

            if success:
                self.logger.info(
                    f"Updated mkdocs.yml with {len(location_data_list)} locations"
                )
            else:
                self.logger.warning("Failed to update mkdocs.yml")

            return success

        except Exception as e:
            self.logger.error(f"Error updating mkdocs.yml: {e}", exc_info=True)
            return False

    def run(self) -> bool:
        """Run the generator.

        Returns:
            bool: True if the generation was successful.
        """
        return self.generate_all()
