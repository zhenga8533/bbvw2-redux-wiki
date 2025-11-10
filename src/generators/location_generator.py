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

from src.generators.base_generator import BaseGenerator
from src.utils.core.config import GENERATOR_DEX_RELATIVE_PATH
from src.utils.formatters.markdown_formatter import (
    format_ability,
    format_item,
    format_move,
    format_pokemon,
    format_pokemon_card_grid,
    format_type_badge,
)
from src.utils.formatters.yaml_formatter import update_mkdocs_nav


class LocationGenerator(BaseGenerator):
    """
    Generator for location markdown pages.

    Creates detailed pages for each location including:
    - Trainer battles with full team details
    - Wild encounters by method (grass, surf, fishing, etc.)
    - Hidden Grotto encounters
    - Nested sublocations
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
        # Initialize base generator
        super().__init__(output_dir=output_dir, project_root=project_root)

        # Set category for BaseGenerator
        self.category = "locations"

        # Configure index table
        self.index_table_headers = [
            "Location",
            "Trainers",
            "Wild Encounters",
            "Hidden Grotto",
        ]
        self.index_table_alignments = ["left", "center", "center", "center"]

        # Set up input directory
        self.input_dir = self.project_root / input_dir

        # Individual location pages go in data/ subdirectory
        self.data_dir = self.output_dir / "data"

        # Create directories
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.logger.debug(f"Input directory: {self.input_dir}")
        self.logger.debug(f"Data directory: {self.data_dir}")

    def load_all_data(self) -> List[tuple[str, Dict[str, Any]]]:
        """Load all location data from JSON files.

        Returns:
            List[tuple[str, Dict[str, Any]]]: List of (filename_stem, location_data) tuples.
        """
        location_data_list = []
        location_files = sorted(self.input_dir.glob("*.json"))
        self.logger.info(f"Found {len(location_files)} location files")

        for location_file in location_files:
            try:
                with open(location_file, "r", encoding="utf-8") as f:
                    location_data = json.load(f)
                    location_data_list.append((location_file.stem, location_data))
            except Exception as e:
                self.logger.error(f"Failed to load {location_file.name}: {e}")
                raise

        return location_data_list

    def categorize_data(
        self, data: List[tuple[str, Dict[str, Any]]]
    ) -> Dict[str, List[tuple[str, Dict[str, Any]]]]:
        """Categorize location data (locations don't have subcategories, so all go in 'all').

        Args:
            data (List[tuple[str, Dict[str, Any]]]): List of location data tuples.

        Returns:
            Dict[str, List[tuple[str, Dict[str, Any]]]]: Categorized data (single 'all' category).
        """
        # Locations don't have subcategories, so we return all in a single category
        return {"all": data}

    def cleanup_output_dir(self, pattern: str = "*.md") -> int:
        """Clean up old files in both output_dir and data_dir.

        Args:
            pattern (str, optional): Glob pattern for files to delete. Defaults to "*.md".

        Returns:
            int: Number of files deleted.
        """
        deleted_count = super().cleanup_output_dir(pattern)

        # Also clean up the data subdirectory
        if self.data_dir.exists():
            for old_file in self.data_dir.glob(pattern):
                old_file.unlink()
                self.logger.debug(f"Deleted old file: {old_file}")
                deleted_count += 1

        return deleted_count

    def generate_page(
        self, entry: tuple[str, Dict[str, Any]], cache: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Generate a markdown page for a single location.

        Args:
            entry (tuple[str, Dict[str, Any]]): Tuple of (filename_stem, location_data).
            cache (Optional[Dict[str, Any]], optional): Cache (not used for locations). Defaults to None.

        Returns:
            Path: Path to the generated markdown file.
        """
        filename_stem, location_data = entry
        location_name = location_data.get("name", filename_stem)
        self.logger.debug(f"Generating page for: {location_name}")

        # Build markdown content
        markdown = self._build_location_markdown(location_data)

        # Write to file in data/ subdirectory
        output_filename = f"{filename_stem}.md"
        output_path = self.data_dir / output_filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        self.logger.debug(f"Saved markdown to: {output_path}")
        return output_path

    def format_index_row(self, entry: tuple[str, Dict[str, Any]]) -> List[str]:
        """Format a single row for the index table.

        Args:
            entry (tuple[str, Dict[str, Any]]): Tuple of (filename_stem, location_data).

        Returns:
            List[str]: List of formatted row values.
        """
        filename_stem, location_data = entry
        location_name = location_data.get("name", filename_stem)
        link = f"[{location_name}](data/{filename_stem}.md)"

        # Count trainers (including sublocations)
        trainer_count = self._count_trainers(location_data)
        trainer_str = str(trainer_count) if trainer_count > 0 else "—"

        # Check for wild encounters
        has_wild = bool(location_data.get("wild_encounters"))
        if not has_wild and location_data.get("sublocations"):
            has_wild = self._has_wild_encounters_in_sublocations(
                location_data["sublocations"]
            )
        wild_str = "✓" if has_wild else "—"

        # Check for hidden grotto
        has_grotto = bool(location_data.get("hidden_grotto"))
        if not has_grotto and location_data.get("sublocations"):
            has_grotto = self._has_hidden_grotto_in_sublocations(
                location_data["sublocations"]
            )
        grotto_str = "✓" if has_grotto else "—"

        return [link, trainer_str, wild_str, grotto_str]

    def generate_index(
        self,
        data: List[tuple[str, Dict[str, Any]]],
        categorized_entries: Dict[str, List[tuple[str, Dict[str, Any]]]],
    ) -> Path:
        """Generate the overview/index page for all locations.

        Args:
            data (List[tuple[str, Dict[str, Any]]]): List of all location data tuples.
            categorized_entries (Dict[str, List[tuple[str, Dict[str, Any]]]]): Categorized data.

        Returns:
            Path: Path to the generated overview markdown file.
        """
        from src.utils.core.config import GAME_TITLE
        from src.utils.formatters.table_formatter import create_table

        self.logger.info("Generating locations overview page...")

        # Start markdown
        markdown = "# Locations\n\n"
        markdown += f"Complete list of all locations in **{GAME_TITLE}**.\n\n"
        markdown += "> Click on any of the Locations to see its full description.\n\n"

        # Get all locations from the 'all' category
        all_locations = categorized_entries.get("all", [])

        # Sort by display name
        sorted_locations = sorted(all_locations, key=lambda x: x[1].get("name", x[0]))

        # Generate table
        markdown += "## All Locations\n\n"

        # Build table rows
        rows = []
        for entry in sorted_locations:
            rows.append(self.format_index_row(entry))

        # Use table formatter
        markdown += create_table(
            self.index_table_headers,
            rows,
            self.index_table_alignments,
        )
        markdown += "\n"

        # Write to file (in the locations directory, not parent)
        output_path = self.output_dir / "locations.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        self.logger.info(f"Generated overview page: {output_path}")
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
            # Main area uses depth 3 for content sections
            content_depth = 3
        else:
            # Add location description after location title if no sublocations
            if location_data.get("description"):
                markdown += f"{location_data['description']}\n\n"
            # No sublocations, use depth 2 for content sections
            content_depth = 2

        # Add content sections with dynamic depth
        markdown += self._build_content_sections(
            location_data, content_depth
        )

        # Add sublocations
        if location_data.get("sublocations"):
            markdown += self._build_sublocations_section(location_data["sublocations"])

        return markdown

    def _build_content_sections(
        self, data: Dict[str, Any], depth: int
    ) -> str:
        """Build trainers, wild encounters, and hidden grotto sections with dynamic headers.

        Args:
            data (Dict[str, Any]): Location or sublocation data.
            depth (int): Current header depth level.

        Returns:
            str: Markdown content for all content sections.
        """
        markdown = ""
        header = "#" * depth

        # Add trainers section
        if data.get("trainers"):
            markdown += f"{header} Trainers\n\n"
            # Add trainer notes (level adjustments, etc.) after Trainers heading
            if data.get("trainer_notes"):
                markdown += f"{data['trainer_notes']}\n\n"
            markdown += self._build_trainers_section(data["trainers"])

        # Add wild encounters section
        if data.get("wild_encounters"):
            markdown += f"{header} Wild Encounters\n\n"
            markdown += self._build_wild_encounters_section(
                data["wild_encounters"]
            )

        # Add hidden grotto section
        if data.get("hidden_grotto"):
            markdown += f"{header} Hidden Grotto\n\n"
            markdown += self._build_hidden_grotto_section(
                data["hidden_grotto"]
            )

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

            # Check if this sublocation has nested sublocations
            has_nested_sublocations = bool(sublocation_data.get("sublocations"))

            # Check if this sublocation has any content
            has_content = (
                sublocation_data.get("trainers")
                or sublocation_data.get("wild_encounters")
                or sublocation_data.get("hidden_grotto")
            )

            # If there are nested sublocations and content, add "Main Section" header
            if has_nested_sublocations and has_content:
                markdown += f"{'#' * (depth + 1)} Main Section\n\n"
                # Content sections go one level deeper
                content_depth = depth + 2
            else:
                # No nested sublocations, content sections are one level deeper than sublocation
                content_depth = depth + 1

            # Add content sections with dynamic depth
            markdown += self._build_content_sections(sublocation_data, content_depth)

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

            if trainer.get("notes"):
                markdown += f"{trainer['notes']}\n\n"

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

    def update_mkdocs_nav(
        self, categorized_entries: Dict[str, List[tuple[str, Dict[str, Any]]]]
    ) -> bool:
        """Update mkdocs.yml navigation with locations.

        Args:
            categorized_entries (Dict[str, List[tuple[str, Dict[str, Any]]]]): Categorized location data.

        Returns:
            bool: True if update succeeded, False otherwise.
        """
        try:
            self.logger.info("Updating mkdocs.yml navigation for locations...")
            mkdocs_path = self.project_root / "mkdocs.yml"

            # Get all locations from the 'all' category
            all_locations = categorized_entries.get("all", [])

            # Sort by display name
            sorted_locations = sorted(
                all_locations, key=lambda x: x[1].get("name", x[0])
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
                    f"Updated mkdocs.yml with {len(all_locations)} locations"
                )
            else:
                self.logger.warning("Failed to update mkdocs.yml")

            return success

        except Exception as e:
            self.logger.error(f"Error updating mkdocs.yml: {e}", exc_info=True)
            return False
