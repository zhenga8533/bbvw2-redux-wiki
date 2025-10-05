"""
Helper utilities for loading PokeDB JSON data into dataclass structures.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Type, TypeVar
from .pokedb_structure import Pokemon, Move, Ability, Item

T = TypeVar("T")


class PokeDBLoader:
    """
    Utility class for loading PokeDB JSON files into structured dataclasses.

    Supports loading from both the original gen5 data and the parsed working copy.
    """

    def __init__(self, use_parsed: bool = False):
        """
        Initialize the PokeDB loader.

        Args:
            use_parsed: If True, load from data/pokedb/parsed/
                       If False, load from data/pokedb/gen5/ (default)
        """
        self.project_root = Path(__file__).parent.parent.parent
        base_dir = "parsed" if use_parsed else "gen5"
        self.data_dir = self.project_root / "data" / "pokedb" / base_dir

        if not self.data_dir.exists():
            raise FileNotFoundError(
                f"PokeDB data directory not found: {self.data_dir}\n"
                "Run 'python -m src.main --init' to download the data."
            )

    def _load_json(self, category: str, name: str) -> dict:
        """
        Load a JSON file from the PokeDB directory.

        Args:
            category: The category folder (pokemon, move, ability, item)
            name: The name of the JSON file (without .json extension)

        Returns:
            dict: Parsed JSON data

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        file_path = self.data_dir / category / f"{name}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_all_json(self, category: str, subfolder: Optional[str] = None) -> Dict[str, dict]:
        """
        Load all JSON files from a category folder.

        Args:
            category: The category folder (pokemon, move, ability, item)
            subfolder: Optional subfolder within category (e.g., 'default' for pokemon)

        Returns:
            dict: Mapping of filename (without .json) to parsed JSON data
        """
        if subfolder:
            dir_path = self.data_dir / category / subfolder
        else:
            dir_path = self.data_dir / category

        if not dir_path.exists():
            return {}

        results = {}
        for json_file in dir_path.glob("*.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                results[json_file.stem] = json.load(f)

        return results

    def load_pokemon(self, name: str, subfolder: str = "default") -> dict:
        """
        Load a Pokemon JSON file.

        Args:
            name: Pokemon name (e.g., 'pikachu')
            subfolder: Pokemon subfolder (default, cosmetic, transformation, variant)

        Returns:
            dict: Pokemon data
        """
        file_path = self.data_dir / "pokemon" / subfolder / f"{name}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Pokemon not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_all_pokemon(self, subfolder: str = "default") -> Dict[str, dict]:
        """
        Load all Pokemon from a specific subfolder.

        Args:
            subfolder: Pokemon subfolder (default, cosmetic, transformation, variant)

        Returns:
            dict: Mapping of pokemon name to data
        """
        return self._load_all_json("pokemon", subfolder)

    def load_move(self, name: str) -> dict:
        """
        Load a Move JSON file.

        Args:
            name: Move name (e.g., 'thunderbolt')

        Returns:
            dict: Move data
        """
        return self._load_json("move", name)

    def load_all_moves(self) -> Dict[str, dict]:
        """
        Load all moves.

        Returns:
            dict: Mapping of move name to data
        """
        return self._load_all_json("move")

    def load_ability(self, name: str) -> dict:
        """
        Load an Ability JSON file.

        Args:
            name: Ability name (e.g., 'intimidate')

        Returns:
            dict: Ability data
        """
        return self._load_json("ability", name)

    def load_all_abilities(self) -> Dict[str, dict]:
        """
        Load all abilities.

        Returns:
            dict: Mapping of ability name to data
        """
        return self._load_all_json("ability")

    def load_item(self, name: str) -> dict:
        """
        Load an Item JSON file.

        Args:
            name: Item name (e.g., 'potion')

        Returns:
            dict: Item data
        """
        return self._load_json("item", name)

    def load_all_items(self) -> Dict[str, dict]:
        """
        Load all items.

        Returns:
            dict: Mapping of item name to data
        """
        return self._load_all_json("item")

    def get_pokemon_count(self, subfolder: str = "default") -> int:
        """
        Get the count of Pokemon in a subfolder.

        Args:
            subfolder: Pokemon subfolder

        Returns:
            int: Number of Pokemon JSON files
        """
        dir_path = self.data_dir / "pokemon" / subfolder
        if not dir_path.exists():
            return 0
        return len(list(dir_path.glob("*.json")))

    def get_category_path(self, category: str, subfolder: Optional[str] = None) -> Path:
        """
        Get the path to a category folder.

        Args:
            category: The category (pokemon, move, ability, item)
            subfolder: Optional subfolder

        Returns:
            Path: Absolute path to the category folder
        """
        if subfolder:
            return self.data_dir / category / subfolder
        return self.data_dir / category
