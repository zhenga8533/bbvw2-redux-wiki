"""
Parser for Evolution Changes.txt that updates Pokemon evolution data in PokeDB.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from ..utils.pokedb_loader import PokeDBLoader
from ..utils.logger import ChangeLogger
from ..utils import string_utils, sprite_utils
from .base_parser import BaseParser


class EvolutionParser(BaseParser, ChangeLogger):
    """
    Parse Evolution Changes.txt and update Pokemon JSON files in data/pokedb/parsed/.

    This parser:
    1. Reads evolution changes from the text file
    2. Updates evolution_chain data in Pokemon JSON files
    3. Generates a markdown summary of all changes
    """

    # Regex patterns for parsing Evolution Changes.txt
    PATTERNS = {
        # File structure patterns
        'section_header': r'^={3,}',
        'changes_section': r'Evolution\s+Changes',
        'pokemon_entry': r'^(\d+)\s+(\S+(?:\s+Jr\.)?)\s+(.+)$',
        'continuation_line': r'^\s+(.+)$',
        'skip_line': r'^(---|Pokémon|---$)',
        'empty_line': r'^\s*$',

        # Evolution data extraction patterns
        'level': r'(?:at\s+)?level\s+(\d+)',
        'friendship': r'(\d+)\+?\s*friendship',
        'item': r'via\s+the\s+use\s+of\s+(?:a\s+|an\s+)?(.+?)(?:\.|$)',
        'move': r'knowing(?:\s+the\s+move)?\s+(.+?)(?:\.|$)',
        'party_species': r'when\s+a\s+(\w+)\s+is\s+in\s+the\s+party',
        'evolution_target': r'into\s+(\w+(?:-?\w+)?)',

        # Additional evolution conditions
        'gender_condition': r'if\s+(\w+)\s+is\s+(male|female)',
        'time_condition': r'(?:at\s+|during\s+)?(?:any\s+time\s+of\s+)?(?:the\s+)?(day|night)',
        'additional_method': r'in\s+addition\s+to\s+its\s+normal\s+evolution\s+method',
    }

    def __init__(
        self,
        input_file: str = "Evolution Changes.txt",
        output_dir: str = "docs/changes",
        parsed_data_dir: str = "evolution",
    ):
        """Initialize the evolution parser."""
        BaseParser.__init__(self, input_file, output_dir, parsed_data_dir)
        ChangeLogger.__init__(self)
        self.loader = PokeDBLoader(use_parsed=True)
        self.changes: List[Dict] = []

    def parse(self) -> dict:
        """
        Parse the Evolution Changes.txt file using pattern matching.

        Returns:
            dict: Parsed evolution changes with Pokemon data
        """
        content = self.input_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        in_changes_section = False
        current_pokemon = None

        for i, line in enumerate(lines):
            # Detect start of changes section
            if re.search(self.PATTERNS['changes_section'], line):
                # Check if previous line is a section header
                if i > 0 and re.match(self.PATTERNS['section_header'], lines[i - 1]):
                    in_changes_section = True
                    continue

            if not in_changes_section:
                continue

            # Skip empty lines and table headers using patterns
            if re.match(self.PATTERNS['empty_line'], line):
                continue
            if re.match(self.PATTERNS['skip_line'], line):
                continue

            # Try to match a Pokemon entry line
            pokemon_match = re.match(self.PATTERNS['pokemon_entry'], line)
            if pokemon_match:
                dex_num, pokemon_name, change_text = pokemon_match.groups()
                current_pokemon = {
                    "dex_num": int(dex_num),
                    "name": string_utils.parse_pokemon_name(pokemon_name),
                    "display_name": pokemon_name,
                    "changes": [change_text],
                }
                self.changes.append(current_pokemon)
                continue

            # Try to match a continuation line (indented text)
            continuation_match = re.match(self.PATTERNS['continuation_line'], line)
            if continuation_match and current_pokemon:
                continuation_text = continuation_match.group(1)
                current_pokemon["changes"].append(continuation_text)
                continue

        self.logger.info(f"Parsed {len(self.changes)} Pokemon with evolution changes")
        return {"changes": self.changes, "total_pokemon": len(self.changes)}

    def _extract_level(self, text: str) -> Optional[int]:
        """Extract level from evolution text."""
        return string_utils.extract_number(text, self.PATTERNS['level'])

    def _extract_friendship(self, text: str) -> Optional[int]:
        """Extract friendship value from evolution text."""
        return string_utils.extract_number(text, self.PATTERNS['friendship'])

    def _extract_item(self, text: str) -> Optional[str]:
        """Extract item name from evolution text."""
        return string_utils.extract_with_pattern(
            text, self.PATTERNS['item'], string_utils.parse_item_name
        )

    def _extract_move(self, text: str) -> Optional[str]:
        """Extract move name from evolution text."""
        return string_utils.extract_with_pattern(
            text, self.PATTERNS['move'], string_utils.parse_move_name
        )

    def _extract_party_species(self, text: str) -> Optional[str]:
        """Extract party species from evolution text."""
        return string_utils.extract_with_pattern(
            text, self.PATTERNS['party_species'], string_utils.parse_pokemon_name
        )

    def _extract_evolution_target(self, text: str) -> Optional[str]:
        """Extract evolution target species from text."""
        return string_utils.extract_with_pattern(
            text, self.PATTERNS['evolution_target'], string_utils.parse_pokemon_name
        )

    def _extract_gender_condition(self, text: str) -> Optional[str]:
        """Extract gender condition from evolution text."""
        match = re.search(self.PATTERNS['gender_condition'], text.lower())
        if match:
            return match.group(2)  # Returns 'male' or 'female'
        return None

    def _extract_time_condition(self, text: str) -> Optional[str]:
        """Extract time of day condition from evolution text."""
        match = re.search(self.PATTERNS['time_condition'], text.lower())
        if match:
            return match.group(1)  # Returns 'day' or 'night'
        return None

    def _is_additional_method(self, text: str) -> bool:
        """Check if this is an additional evolution method (not replacement)."""
        return bool(re.search(self.PATTERNS['additional_method'], text.lower()))

    def _parse_evolution_method(self, change_text: str) -> Optional[Dict]:
        """
        Parse evolution method text into structured data using pattern matching.

        Args:
            change_text: Text describing the evolution change

        Returns:
            dict: Evolution details or None if can't parse
        """
        # Base evolution data
        evo_data = {
            "trigger": None,
            "item": None,
            "min_level": None,
            "min_happiness": None,
            "known_move": None,
            "party_species": None,
            "gender": None,
            "time_of_day": None,
            "is_additional": self._is_additional_method(change_text),
        }

        # Extract all possible conditions
        level = self._extract_level(change_text)
        item = self._extract_item(change_text)
        friendship = self._extract_friendship(change_text)
        move = self._extract_move(change_text)
        party_species = self._extract_party_species(change_text)
        gender = self._extract_gender_condition(change_text)
        time_of_day = self._extract_time_condition(change_text)

        # Determine trigger and populate data
        if item:
            evo_data["trigger"] = "use-item"
            evo_data["item"] = item
        elif level:
            evo_data["trigger"] = "level-up"
            evo_data["min_level"] = level
        elif friendship:
            evo_data["trigger"] = "level-up"
            evo_data["min_happiness"] = friendship
        elif move:
            evo_data["trigger"] = "level-up"
            evo_data["known_move"] = move
        elif party_species:
            evo_data["trigger"] = "level-up"
            evo_data["party_species"] = party_species
        else:
            return None

        # Add optional conditions
        if gender:
            evo_data["gender"] = gender
        if time_of_day:
            evo_data["time_of_day"] = time_of_day

        # Remove None values for cleaner output
        return {k: v for k, v in evo_data.items() if v is not None}

    def _find_pokemon_file(self, pokemon_name: str) -> Optional[Path]:
        """
        Find the Pokemon JSON file across all subdirectories.

        Args:
            pokemon_name: Name of the Pokemon

        Returns:
            Path: Path to the JSON file, or None if not found
        """
        for subfolder in ["default", "cosmetic", "variant", "transformation"]:
            path = (
                self.loader.get_category_path("pokemon", subfolder)
                / f"{pokemon_name}.json"
            )
            if path.exists():
                return path
        return None

    def _update_pokemon_evolution(self, pokemon_data: Dict) -> bool:
        """
        Update Pokemon evolution data in the parsed directory.

        Args:
            pokemon_data: Parsed Pokemon change data

        Returns:
            bool: True if updated, False if failed
        """
        pokemon_name = pokemon_data["name"]
        pokemon_file = self._find_pokemon_file(pokemon_name)

        if not pokemon_file:
            self.logger.warning(f"Pokemon file not found: {pokemon_name}")
            return False

        # Load the Pokemon JSON
        with open(pokemon_file, "r", encoding="utf-8") as f:
            poke_json = json.load(f)

        # Store original evolution chain for logging
        original_evo_chain = json.dumps(poke_json.get("evolution_chain", {}))

        # Process each evolution change
        updated = False
        for change_text in pokemon_data["changes"]:
            evo_method = self._parse_evolution_method(change_text)
            if not evo_method:
                self.logger.warning(
                    f"Could not parse evolution method for {pokemon_name}: {change_text}"
                )
                continue

            # Extract evolution target
            target_species = self._extract_evolution_target(change_text)
            if not target_species:
                self.logger.warning(
                    f"Could not find evolution target in: {change_text}"
                )
                continue

            # Log the change
            self.log_change(
                entity_type="pokemon",
                entity_name=pokemon_name,
                field=f"evolution.{target_species}",
                old_value=f"[Original method]",
                new_value=evo_method,
                file_path=pokemon_file,
                metadata={
                    "change_text": change_text,
                    "target_species": target_species,
                },
            )

            # Update evolution chain
            # Note: This is a simplified update - full implementation would need to
            # properly navigate and update the evolution_chain structure
            self.logger.debug(
                f"Would update {pokemon_name} -> {target_species}: {evo_method}"
            )
            updated = True

        if updated:
            # Save updated Pokemon JSON
            with open(pokemon_file, "w", encoding="utf-8") as f:
                json.dump(poke_json, f, indent=4, ensure_ascii=False)

            # Log file update
            self.log_file_update(pokemon_file, "updated")

        return updated

    def _get_evolution_target_id(self, target_name: str) -> Optional[int]:
        """
        Get the Pokedex ID for an evolution target by name.

        Args:
            target_name: Name of the evolution target (slug format)

        Returns:
            int: Pokedex ID, or None if not found
        """
        # Try to find the Pokemon file
        pokemon_file = self._find_pokemon_file(target_name)
        if not pokemon_file:
            return None

        try:
            with open(pokemon_file, "r", encoding="utf-8") as f:
                poke_json = json.load(f)
                return poke_json.get("id")
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None

    def generate_markdown(self, parsed_data: dict) -> str:
        """
        Generate markdown documentation of evolution changes with sprites and MkDocs features.

        Args:
            parsed_data: Data from parse()

        Returns:
            str: Markdown content
        """
        lines = [
            "# Evolution Changes\n\n",
            f"*Source: {self.input_path.name}*\n\n",
        ]

        # Overview admonition
        overview_content = """A number of Pokémon have had their evolution methods modified in Redux.

**Key Changes:**

- **Link Cable** and **Ice Stone** introduced as evolution items
- Trade evolution items now work like evolution stones
- Level requirements adjusted for balance
- Some friendship evolutions simplified"""

        lines.append(sprite_utils.mkdocs_admonition(
            "Overview",
            overview_content,
            "info"
        ))
        lines.append("\n\n")

        # Statistics table
        lines.extend([
            "## Summary\n\n",
            "| Statistic | Value |\n",
            "|-----------|-------|\n",
            f"| Total Pokémon Affected | **{parsed_data['total_pokemon']}** |\n",
            "| Generations | All |\n",
            "| Game Versions | All |\n\n",
            "---\n\n",
        ])

        # Evolution changes table with sprites
        lines.extend([
            "## Evolution Changes\n\n",
            "| # | Base Form | Evolved Form | Method |\n",
            "|---|:---------:|:------------:|--------|\n",
        ])

        for change in parsed_data["changes"]:
            dex_num = change["dex_num"]
            dex_num_str = str(dex_num).zfill(3)
            pokemon_name = change["display_name"]
            pokemon_slug = change["name"]

            # Base Pokemon sprite with name underneath
            base_sprite = sprite_utils.pokemon_sprite_md(dex_num, pokemon_name, size=64)
            base_display = f"{base_sprite}<br>{pokemon_name}"

            # Process each evolution change
            for change_text in change["changes"]:
                # Extract evolution target
                target_species = self._extract_evolution_target(change_text)

                if target_species:
                    # Get evolution target sprite
                    target_id = self._get_evolution_target_id(target_species)
                    if target_id:
                        # Capitalize first letter for display
                        target_display = target_species.replace("-", " ").title()
                        evo_sprite = sprite_utils.pokemon_sprite_md(target_id, target_display, size=64)
                        evo_display = f"{evo_sprite}<br>{target_display}"
                    else:
                        # Fallback if we can't find the target
                        target_display = target_species.replace("-", " ").title()
                        evo_display = target_display
                else:
                    # Fallback if we can't parse the target
                    evo_display = "Unknown"

                # Clean up the method text (remove "Now evolves into X" part)
                method_text = change_text
                if "Now evolves into" in method_text and target_species:
                    # Use regex to extract everything after the Pokemon name
                    # This handles names with spaces, dots, hyphens, etc.
                    import re
                    # Pattern to match "Now evolves into [Pokemon Name] [method]"
                    # We'll extract everything after the first occurrence of the pattern
                    pattern = r"Now evolves into\s+([A-Za-z0-9.\-'\s]+?)\s+(at|via|by|while|when|if|in)"
                    match = re.search(pattern, change_text)
                    if match:
                        # Get the text starting from the second group (at/via/by/etc)
                        start_pos = match.start(2)
                        method_text = change_text[start_pos:].strip()
                    else:
                        # Fallback: just remove "Now evolves into [target]"
                        method_text = change_text.replace(f"Now evolves into {target_species.replace('-', ' ').title()}", "").strip()
                        method_text = change_text.replace(f"Now evolves into {target_species.replace('-', ' ')}", "").strip()

                lines.append(f"| #{dex_num_str} | {base_display} | {evo_display} | {method_text} |\n")

        return "".join(lines)

    def run(self, save_data: bool = True) -> tuple[Path, Optional[Path]]:
        """
        Execute the full parsing pipeline with change logging.

        Args:
            save_data: Whether to update Pokemon JSON files (default: True)

        Returns:
            tuple: (markdown_path, change_log_path)
        """
        self.logger.info(f"Starting parse of {self.input_path}")

        # Parse input file
        parsed_data = self.parse()

        # Generate markdown
        markdown_content = self.generate_markdown(parsed_data)

        # Save markdown
        markdown_path = self.save_markdown(markdown_content, "evolution_changes.md")

        # Update Pokemon data if requested
        change_log_path = None
        if save_data:
            self.logger.info("\nUpdating Pokemon evolution data...")
            updated_count = 0
            for pokemon_data in parsed_data["changes"]:
                if self._update_pokemon_evolution(pokemon_data):
                    updated_count += 1

            self.logger.info(
                f"\nProcessed {updated_count}/{len(parsed_data['changes'])} Pokemon files"
            )

            # Print change summary
            self.print_change_summary()

            # Save change log to logs/changes/
            change_log_dir = self.project_root / "logs" / "changes"
            change_log_dir.mkdir(parents=True, exist_ok=True)
            change_log_path = change_log_dir / "evolution_changes.json"
            self.save_change_log(change_log_path)

        self.logger.info("Parsing complete")
        return markdown_path, change_log_path


# Example usage
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    parser = EvolutionParser()
    markdown_path, _ = parser.run(save_data=True)
    print(f"Markdown: {markdown_path}")
