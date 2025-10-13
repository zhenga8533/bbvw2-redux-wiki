"""
Helper utilities for loading PokeDB JSON data into dataclass structures.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Optional

from src.models.pokedb import (
    Pokemon,
    EvolutionChain,
    EvolutionNode,
    EvolutionDetails,
    Form,
)


class PokeDBLoader:
    """
    Utility class for loading PokeDB JSON files into structured dataclasses.

    Supports loading from both the original gen5 data and the parsed working copy.
    Implements caching to avoid redundant file I/O operations.
    """

    _data_dir: Path = Path(__file__).parent.parent.parent / "data" / "pokedb" / "parsed"
    _pokemon_cache: Dict[tuple[str, str], Pokemon] = {}

    @staticmethod
    def _dict_to_evolution_node(data: dict) -> EvolutionNode:
        """Convert a dict to an EvolutionNode dataclass."""
        evolves_to = [
            PokeDBLoader._dict_to_evolution_node(node)
            for node in data.get("evolves_to", [])
        ]
        evolution_details = None
        if data.get("evolution_details") is not None:
            evolution_details = EvolutionDetails(**data["evolution_details"])
        return EvolutionNode(
            species_name=data["species_name"],
            evolves_to=evolves_to,
            evolution_details=evolution_details,
        )

    @staticmethod
    def _convert_nested_dataclasses(data: dict) -> dict:
        """
        Convert nested dictionaries to their corresponding dataclass objects.

        This handles evolution_chain and forms conversions.

        Args:
            data: The raw Pokemon data dictionary

        Returns:
            dict: The data with nested objects converted to dataclasses
        """
        # Convert evolution_chain dict to EvolutionChain dataclass
        if "evolution_chain" in data and isinstance(data["evolution_chain"], dict):
            data["evolution_chain"] = PokeDBLoader._dict_to_evolution_chain(
                data["evolution_chain"]
            )

        # Convert forms list of dicts to list of Form dataclasses
        if "forms" in data and isinstance(data["forms"], list):
            data["forms"] = [
                Form(**form) if isinstance(form, dict) else form
                for form in data["forms"]
            ]

        return data

    @staticmethod
    def _dict_to_evolution_chain(data: dict) -> EvolutionChain:
        """Convert a dict to an EvolutionChain dataclass."""
        evolves_to = [
            PokeDBLoader._dict_to_evolution_node(node)
            for node in data.get("evolves_to", [])
        ]
        return EvolutionChain(
            species_name=data["species_name"],
            evolves_to=evolves_to,
        )

    @staticmethod
    def _find_file(
        category: str, name: str, subfolder: Optional[str] = None
    ) -> Optional[Path]:
        """
        Find a file, with fallback to check for variants with form suffixes.

        For Pokemon that have forms (e.g., wormadam-plant, darmanitan-standard),
        this will try to find the base name first, then look for any files
        starting with the base name followed by a hyphen.

        Args:
            category: The category folder (pokemon, move, ability, item)
            name: The name of the JSON file (without .json extension)
            subfolder: Optional subfolder within category

        Returns:
            Path: The found file path, or None if not found
        """
        if subfolder:
            dir_path = PokeDBLoader._data_dir / category / subfolder
            file_path = dir_path / f"{name}.json"
        else:
            dir_path = PokeDBLoader._data_dir / category
            file_path = dir_path / f"{name}.json"

        # First try exact match
        if file_path.exists():
            return file_path

        # If not found, try to find a file starting with name followed by hyphen
        # This handles cases like "wormadam" -> "wormadam-plant.json"
        if dir_path.exists():
            pattern = f"{name}-*.json"
            matches = list(dir_path.glob(pattern))
            if matches:
                # Return the first match (alphabetically sorted for consistency)
                return sorted(matches)[0]

        return None

    @staticmethod
    def find_all_form_files(pokemon_id: str) -> list[tuple[str, str]]:
        """
        Find all form files for a given Pokemon by reading the forms field.

        This method loads the Pokemon data and returns all forms listed in
        the "forms" field, including their names and categories.

        Args:
            pokemon_id: The Pokemon species ID (e.g., 'wormadam')

        Returns:
            List of tuples (form_name, category) for all forms of this Pokemon.
            Returns empty list if Pokemon has no forms field or doesn't exist.

        Example:
            >>> PokeDBLoader.find_all_form_files('wormadam')
            [('wormadam-plant', 'default'), ('wormadam-sandy', 'variant'), ...]
        """
        try:
            # Load the base Pokemon data to get the forms list
            pokemon = PokeDBLoader.load_pokemon(pokemon_id)

            if not pokemon.forms:
                # If no forms field, return just the base Pokemon
                return [(pokemon_id, "default")]

            # Return all forms from the forms field
            return [(form.name, form.category) for form in pokemon.forms]
        except FileNotFoundError:
            # If file not found, return empty list
            return []

    @staticmethod
    def _load_json(category: str, name: str, subfolder: Optional[str] = None) -> dict:
        """
        Load a JSON file from the PokeDB directory.

        Args:
            category: The category folder (pokemon, move, ability, item)
            name: The name of the JSON file (without .json extension)
            subfolder: Optional subfolder within category

        Returns:
            dict: Parsed JSON data

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        file_path = PokeDBLoader._find_file(category, name, subfolder)

        if file_path is None:
            # Provide helpful error message
            if subfolder:
                search_location = PokeDBLoader._data_dir / category / subfolder
            else:
                search_location = PokeDBLoader._data_dir / category
            raise FileNotFoundError(
                f"File not found: {name}.json (searched in {search_location})"
            )

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _load_all_json(
        category: str, subfolder: Optional[str] = None
    ) -> Dict[str, dict]:
        """
        Load all JSON files from a category folder.

        Args:
            category: The category folder (pokemon, move, ability, item)
            subfolder: Optional subfolder within category (e.g., 'default' for pokemon)

        Returns:
            dict: Mapping of filename (without .json) to parsed JSON data
        """
        if subfolder:
            dir_path = PokeDBLoader._data_dir / category / subfolder
        else:
            dir_path = PokeDBLoader._data_dir / category

        if not dir_path.exists():
            return {}

        results = {}
        for json_file in dir_path.glob("*.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                results[json_file.stem] = json.load(f)

        return results

    @staticmethod
    def load_pokemon(name: str, subfolder: str = "default") -> Pokemon:
        """
        Load a Pokemon JSON file with caching.

        Args:
            name: Pokemon name (e.g., 'pikachu')
            subfolder: Pokemon subfolder (default, cosmetic, transformation, variant)

        Returns:
            Pokemon: Pokemon data
        """
        cache_key = (name, subfolder)

        # Check cache first
        if cache_key in PokeDBLoader._pokemon_cache:
            return PokeDBLoader._pokemon_cache[cache_key]

        # Load from file
        data = PokeDBLoader._load_json("pokemon", name, subfolder)
        data = PokeDBLoader._convert_nested_dataclasses(data)
        pokemon = Pokemon(**data)

        # Cache the result
        PokeDBLoader._pokemon_cache[cache_key] = pokemon

        return pokemon

    @staticmethod
    def load_all_pokemon(subfolder: str = "default") -> Dict[str, Pokemon]:
        """
        Load all Pokemon from a specific subfolder.

        Args:
            subfolder: Pokemon subfolder (default, cosmetic, transformation, variant)

        Returns:
            dict: Mapping of pokemon name to data
        """
        raw_data = PokeDBLoader._load_all_json("pokemon", subfolder)
        result = {}
        for name, data in raw_data.items():
            data = PokeDBLoader._convert_nested_dataclasses(data)
            result[name] = Pokemon(**data)
        return result

    @staticmethod
    def load_move(name: str) -> dict:
        """
        Load a Move JSON file.

        Args:
            name: Move name (e.g., 'thunderbolt')

        Returns:
            dict: Move data
        """
        return PokeDBLoader._load_json("move", name)

    @staticmethod
    def load_all_moves() -> Dict[str, dict]:
        """
        Load all moves.

        Returns:
            dict: Mapping of move name to data
        """
        return PokeDBLoader._load_all_json("move")

    @staticmethod
    def load_ability(name: str) -> dict:
        """
        Load an Ability JSON file.

        Args:
            name: Ability name (e.g., 'intimidate')

        Returns:
            dict: Ability data
        """
        return PokeDBLoader._load_json("ability", name)

    @staticmethod
    def load_all_abilities() -> Dict[str, dict]:
        """
        Load all abilities.

        Returns:
            dict: Mapping of ability name to data
        """
        return PokeDBLoader._load_all_json("ability")

    @staticmethod
    def load_item(name: str) -> dict:
        """
        Load an Item JSON file.

        Args:
            name: Item name (e.g., 'potion')

        Returns:
            dict: Item data
        """
        return PokeDBLoader._load_json("item", name)

    @staticmethod
    def load_all_items() -> Dict[str, dict]:
        """
        Load all items.

        Returns:
            dict: Mapping of item name to data
        """
        return PokeDBLoader._load_all_json("item")

    @staticmethod
    def get_pokemon_count(subfolder: str = "default") -> int:
        """
        Get the count of Pokemon in a subfolder.

        Args:
            subfolder: Pokemon subfolder

        Returns:
            int: Number of Pokemon JSON files
        """
        dir_path = PokeDBLoader._data_dir / "pokemon" / subfolder
        if not dir_path.exists():
            return 0
        return len(list(dir_path.glob("*.json")))

    @staticmethod
    def get_category_path(category: str, subfolder: Optional[str] = None) -> Path:
        """
        Get the path to a category folder.

        Args:
            category: The category (pokemon, move, ability, item)
            subfolder: Optional subfolder

        Returns:
            Path: Absolute path to the category folder
        """
        if subfolder:
            return PokeDBLoader._data_dir / category / subfolder
        return PokeDBLoader._data_dir / category

    @staticmethod
    def save_pokemon(name: str, data: Pokemon, subfolder: str = "default") -> Path:
        """
        Save Pokemon data to a JSON file and invalidate cache.

        Args:
            name: Pokemon name (e.g., 'pikachu')
            data: Pokemon dataclass object
            subfolder: Pokemon subfolder (default, cosmetic, transformation, variant)

        Returns:
            Path: Path to the saved file
        """
        file_path = PokeDBLoader._data_dir / "pokemon" / subfolder / f"{name}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(asdict(data), f, indent=2, ensure_ascii=False)

        # Invalidate cache for this Pokemon
        cache_key = (name, subfolder)
        if cache_key in PokeDBLoader._pokemon_cache:
            del PokeDBLoader._pokemon_cache[cache_key]

        return file_path

    @staticmethod
    def clear_cache() -> None:
        """
        Clear the entire Pokemon cache.

        Useful when you need to reload data from disk or free up memory.
        """
        PokeDBLoader._pokemon_cache.clear()

    @staticmethod
    def get_cache_size() -> int:
        """
        Get the number of cached Pokemon.

        Returns:
            int: Number of Pokemon currently in the cache
        """
        return len(PokeDBLoader._pokemon_cache)

    @staticmethod
    def get_cached_pokemon() -> list[tuple[str, str]]:
        """
        Get a list of all cached Pokemon identifiers.

        Returns:
            list: List of (name, subfolder) tuples for all cached Pokemon
        """
        return list(PokeDBLoader._pokemon_cache.keys())
