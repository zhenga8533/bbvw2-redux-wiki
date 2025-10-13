"""
Helper utilities for loading PokeDB JSON data into dataclass structures.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

from src.models.pokedb import (
    Pokemon,
    Move,
    Ability,
    Item,
    EvolutionChain,
    EvolutionNode,
    EvolutionDetails,
    Form,
    Sprites,
    Cries,
    Stats,
    PokemonAbility,
    EVYield,
    PokemonMoves,
    MoveLearn,
    OtherSprites,
    Versions,
    DreamWorld,
    Home,
    OfficialArtwork,
    Showdown,
    AnimatedSprites,
    GenerationSprites,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PokeDBLoader:
    """
    Utility class for loading PokeDB JSON files into structured dataclasses.

    Supports loading from both the original gen5 data and the parsed working copy.
    Implements caching to avoid redundant file I/O operations.

    IMPORTANT: This class uses a class-level cache that persists across all
    instances and throughout the lifetime of the process. This provides significant
    performance benefits but has important implications:

    - Cache invalidation: Call clear_cache() if files are modified externally
      or if you need fresh data from disk
    - Memory usage: In long-running processes, the cache can grow large.
      Call clear_cache() periodically if memory is a concern
    - Testing: Call clear_cache() between tests to ensure isolation

    The cache is automatically invalidated when saving Pokemon via save_pokemon().

    Configuration:
    - Use set_data_dir() to override the default data directory path
    - Use get_data_dir() to retrieve the current data directory path
    - The default path is: <project_root>/data/pokedb/parsed

    Thread Safety:
    ⚠️  WARNING: This class is NOT thread-safe!
    - Class-level state (_data_dir, _pokemon_cache) is shared across all instances
    - Concurrent access from multiple threads can lead to race conditions
    - DO NOT use this class concurrently from multiple threads without external
      synchronization (e.g., threading.Lock)
    - If thread safety is required, implement proper locking around:
      * Cache reads/writes (_pokemon_cache access)
      * Data directory changes (set_data_dir())
      * File operations (save_pokemon())
    """

    # Class-level data directory (configurable, defaults to None = use default path)
    _data_dir: Optional[Path] = None
    # Class-level cache: intentionally shared across all instances
    # Maps (name, subfolder) -> Pokemon object
    _pokemon_cache: dict[tuple[str, str], Pokemon] = {}

    @classmethod
    def get_data_dir(cls) -> Path:
        """
        Get the current data directory path.

        Returns:
            Path: The data directory path (either custom or default)

        Example:
            >>> data_dir = PokeDBLoader.get_data_dir()
            >>> print(data_dir)
            /path/to/project/data/pokedb/parsed
        """
        if cls._data_dir is None:
            # Default to <project_root>/data/pokedb/parsed
            cls._data_dir = (
                Path(__file__).parent.parent.parent / "data" / "pokedb" / "parsed"
            )
        return cls._data_dir

    @classmethod
    def set_data_dir(cls, path: Path) -> None:
        """
        Set a custom data directory path.

        This is useful for testing or when working with data in a non-standard location.
        When setting a new data directory, the cache is automatically cleared to prevent
        loading stale data from the previous directory.

        Args:
            path: The new data directory path

        Example:
            >>> # For testing with a temporary directory
            >>> PokeDBLoader.set_data_dir(Path("/tmp/test_pokedb"))
            >>> # Reset to default
            >>> PokeDBLoader.set_data_dir(Path(__file__).parent.parent.parent / "data" / "pokedb" / "parsed")
        """
        old_dir = cls._data_dir
        cls._data_dir = path
        logger.info(f"Data directory changed from {old_dir} to {path}")
        cls.clear_cache()  # Clear cache when changing directory

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

        This handles all nested structures in Pokemon data including sprites,
        cries, stats, abilities, moves, evolution_chain, and forms.

        Args:
            data: The raw Pokemon data dictionary

        Returns:
            dict: The data with nested objects converted to dataclasses
        """
        # Convert sprites dict to Sprites dataclass
        if "sprites" in data and isinstance(data["sprites"], dict):
            sprites_data = data["sprites"]

            # Convert nested other sprites
            if "other" in sprites_data and isinstance(sprites_data["other"], dict):
                other = sprites_data["other"]

                # Handle specific nested sprite structures
                if "dream_world" in other:
                    other["dream_world"] = DreamWorld(**other["dream_world"])

                if "home" in other:
                    other["home"] = Home(**other["home"])

                # Handle kebab-case key: official-artwork -> official_artwork
                if "official-artwork" in other:
                    other["official_artwork"] = OfficialArtwork(**other["official-artwork"])
                    del other["official-artwork"]
                elif "official_artwork" in other:
                    other["official_artwork"] = OfficialArtwork(**other["official_artwork"])

                if "showdown" in other:
                    other["showdown"] = Showdown(**other["showdown"])

                sprites_data["other"] = OtherSprites(**other)

            # Convert nested versions
            if "versions" in sprites_data and isinstance(sprites_data["versions"], dict):
                versions = sprites_data["versions"]

                # Handle kebab-case key: black-white -> black_white
                if "black-white" in versions:
                    bw_data = versions["black-white"]
                    if "animated" in bw_data:
                        bw_data["animated"] = AnimatedSprites(**bw_data["animated"])
                    versions["black_white"] = GenerationSprites(**bw_data)
                    del versions["black-white"]

                sprites_data["versions"] = Versions(**versions)

            data["sprites"] = Sprites(**sprites_data)

        # Convert cries dict to Cries dataclass
        if "cries" in data and isinstance(data["cries"], dict):
            data["cries"] = Cries(**data["cries"])

        # Convert stats dict to Stats dataclass
        # Handle kebab-case keys: special-attack and special-defense
        if "stats" in data and isinstance(data["stats"], dict):
            stats_data = data["stats"]
            if "special-attack" in stats_data:
                stats_data["special_attack"] = stats_data.pop("special-attack")
            if "special-defense" in stats_data:
                stats_data["special_defense"] = stats_data.pop("special-defense")
            data["stats"] = Stats(**stats_data)

        # Convert abilities list of dicts to list of PokemonAbility dataclasses
        if "abilities" in data and isinstance(data["abilities"], list):
            data["abilities"] = [
                PokemonAbility(**ability) if isinstance(ability, dict) else ability
                for ability in data["abilities"]
            ]

        # Convert ev_yield list of dicts to list of EVYield dataclasses
        if "ev_yield" in data and isinstance(data["ev_yield"], list):
            data["ev_yield"] = [
                EVYield(**ev) if isinstance(ev, dict) else ev for ev in data["ev_yield"]
            ]

        # Convert moves dict to PokemonMoves dataclass
        if "moves" in data and isinstance(data["moves"], dict):
            moves_data = data["moves"]

            # Convert each move list to MoveLearn objects
            for move_type in ["egg", "tutor", "machine", "level-up"]:
                if move_type in moves_data and isinstance(moves_data[move_type], list):
                    moves_data[move_type] = [
                        MoveLearn(**move) if isinstance(move, dict) else move
                        for move in moves_data[move_type]
                    ]

            # Rename level-up to level_up for dataclass
            if "level-up" in moves_data:
                moves_data["level_up"] = moves_data.pop("level-up")

            data["moves"] = PokemonMoves(**moves_data)

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

    @classmethod
    def _find_file(
        cls, category: str, name: str, subfolder: Optional[str] = None
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
        data_dir = cls.get_data_dir()
        if subfolder:
            dir_path = data_dir / category / subfolder
            file_path = dir_path / f"{name}.json"
        else:
            dir_path = data_dir / category
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

    @classmethod
    def _load_json(
        cls, category: str, name: str, subfolder: Optional[str] = None
    ) -> dict:
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
        file_path = cls._find_file(category, name, subfolder)

        if file_path is None:
            # Provide helpful error message
            data_dir = cls.get_data_dir()
            if subfolder:
                search_location = data_dir / category / subfolder
            else:
                search_location = data_dir / category
            logger.error(f"File not found: {name}.json in {search_location}")
            raise FileNotFoundError(
                f"File not found: {name}.json (searched in {search_location})"
            )

        logger.debug(f"Loading JSON file: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_path}: {e}", exc_info=True)
            raise
        except (OSError, IOError) as e:
            logger.error(f"Error reading file {file_path}: {e}", exc_info=True)
            raise

    @classmethod
    def _load_all_json(
        cls, category: str, subfolder: Optional[str] = None
    ) -> dict[str, dict]:
        """
        Load all JSON files from a category folder.

        Args:
            category: The category folder (pokemon, move, ability, item)
            subfolder: Optional subfolder within category (e.g., 'default' for pokemon)

        Returns:
            dict: Mapping of filename (without .json) to parsed JSON data
        """
        data_dir = cls.get_data_dir()
        if subfolder:
            dir_path = data_dir / category / subfolder
        else:
            dir_path = data_dir / category

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

        Examples:
            >>> pokemon = PokeDBLoader.load_pokemon("pikachu")
            >>> print(pokemon.name)
            pikachu
            >>> print(pokemon.types)
            ['electric']
            >>> # Load a specific form
            >>> darmanitan = PokeDBLoader.load_pokemon("darmanitan-zen", subfolder="variant")
        """
        cache_key = (name, subfolder)

        # Check cache first
        if cache_key in PokeDBLoader._pokemon_cache:
            logger.debug(
                f"Loading Pokemon '{name}' from cache (subfolder: {subfolder})"
            )
            return PokeDBLoader._pokemon_cache[cache_key]

        # Load from file
        logger.debug(f"Loading Pokemon '{name}' from disk (subfolder: {subfolder})")
        data = PokeDBLoader._load_json("pokemon", name, subfolder)
        data = PokeDBLoader._convert_nested_dataclasses(data)
        pokemon = Pokemon(**data)

        # Cache the result
        PokeDBLoader._pokemon_cache[cache_key] = pokemon
        logger.debug(
            f"Cached Pokemon '{name}' (cache size: {len(PokeDBLoader._pokemon_cache)})"
        )

        return pokemon

    @classmethod
    def _load_all_generic(
        cls,
        category: str,
        dataclass_type: type,
        subfolder: Optional[str] = None,
        convert_nested: bool = False,
    ) -> dict[str, Any]:
        """
        Generic method to load all items of a given category.

        Args:
            category: The category folder (pokemon, move, ability, item)
            dataclass_type: The dataclass type to instantiate
            subfolder: Optional subfolder within category
            convert_nested: Whether to convert nested dataclasses (for Pokemon)

        Returns:
            dict: Mapping of item name to dataclass objects
        """
        raw_data = cls._load_all_json(category, subfolder)
        result = {}
        for name, data in raw_data.items():
            if convert_nested:
                data = cls._convert_nested_dataclasses(data)
            result[name] = dataclass_type(**data)
        return result

    @staticmethod
    def load_all_pokemon(subfolder: str = "default") -> dict[str, Pokemon]:
        """
        Load all Pokemon from a specific subfolder.

        Args:
            subfolder: Pokemon subfolder (default, cosmetic, transformation, variant)

        Returns:
            dict: Mapping of pokemon name to data
        """
        return PokeDBLoader._load_all_generic(
            "pokemon", Pokemon, subfolder, convert_nested=True
        )

    @staticmethod
    def load_move(name: str) -> Move:
        """
        Load a Move JSON file and return as a Move dataclass.

        Args:
            name: Move name (e.g., 'thunderbolt')

        Returns:
            Move: Move dataclass object

        Examples:
            >>> move = PokeDBLoader.load_move("thunderbolt")
            >>> print(move.name)
            thunderbolt
            >>> print(move.type)
            {'gen5': 'electric'}
            >>> print(move.power)
            {'gen5': 90}
        """
        data = PokeDBLoader._load_json("move", name)
        return Move(**data)

    @staticmethod
    def load_all_moves() -> dict[str, Move]:
        """
        Load all moves and return as Move dataclasses.

        Returns:
            dict: Mapping of move name to Move dataclass objects
        """
        return PokeDBLoader._load_all_generic("move", Move)

    @staticmethod
    def load_ability(name: str) -> Ability:
        """
        Load an Ability JSON file and return as an Ability dataclass.

        Args:
            name: Ability name (e.g., 'intimidate')

        Returns:
            Ability: Ability dataclass object

        Examples:
            >>> ability = PokeDBLoader.load_ability("intimidate")
            >>> print(ability.name)
            intimidate
            >>> print(ability.is_main_series)
            True
        """
        data = PokeDBLoader._load_json("ability", name)
        return Ability(**data)

    @staticmethod
    def load_all_abilities() -> dict[str, Ability]:
        """
        Load all abilities and return as Ability dataclasses.

        Returns:
            dict: Mapping of ability name to Ability dataclass objects
        """
        return PokeDBLoader._load_all_generic("ability", Ability)

    @staticmethod
    def load_item(name: str) -> Item:
        """
        Load an Item JSON file and return as an Item dataclass.

        Args:
            name: Item name (e.g., 'potion')

        Returns:
            Item: Item dataclass object

        Examples:
            >>> item = PokeDBLoader.load_item("potion")
            >>> print(item.name)
            potion
            >>> print(item.category)
            healing
            >>> print(item.cost)
            300
        """
        data = PokeDBLoader._load_json("item", name)
        return Item(**data)

    @staticmethod
    def load_all_items() -> dict[str, Item]:
        """
        Load all items and return as Item dataclasses.

        Returns:
            dict: Mapping of item name to Item dataclass objects
        """
        return PokeDBLoader._load_all_generic("item", Item)

    @classmethod
    def get_pokemon_count(cls, subfolder: str = "default") -> int:
        """
        Get the count of Pokemon in a subfolder.

        Args:
            subfolder: Pokemon subfolder

        Returns:
            int: Number of Pokemon JSON files
        """
        dir_path = cls.get_data_dir() / "pokemon" / subfolder
        if not dir_path.exists():
            return 0
        return len(list(dir_path.glob("*.json")))

    @classmethod
    def get_category_path(cls, category: str, subfolder: Optional[str] = None) -> Path:
        """
        Get the path to a category folder.

        Args:
            category: The category (pokemon, move, ability, item)
            subfolder: Optional subfolder

        Returns:
            Path: Absolute path to the category folder
        """
        data_dir = cls.get_data_dir()
        if subfolder:
            return data_dir / category / subfolder
        return data_dir / category

    @classmethod
    def save_pokemon(cls, name: str, data: Pokemon, subfolder: str = "default") -> Path:
        """
        Save Pokemon data to a JSON file and invalidate cache.

        This method invalidates ALL cache entries for the given Pokemon name
        across all subfolders, not just the specific subfolder being saved to.
        This ensures cache consistency when a Pokemon might be loaded under
        different forms or categories.

        Args:
            name: Pokemon name (e.g., 'pikachu')
            data: Pokemon dataclass object
            subfolder: Pokemon subfolder (default, cosmetic, transformation, variant)

        Returns:
            Path: Path to the saved file
        """
        file_path = cls.get_data_dir() / "pokemon" / subfolder / f"{name}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Saving Pokemon '{name}' to {file_path}")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(asdict(data), f, indent=2, ensure_ascii=False)
        except (OSError, IOError) as e:
            logger.error(f"Error saving Pokemon '{name}': {e}", exc_info=True)
            raise

        # Invalidate ALL cache entries with this name (any subfolder)
        # This prevents stale cached data if the same Pokemon is cached under different forms
        keys_to_remove = [
            key for key in PokeDBLoader._pokemon_cache.keys() if key[0] == name
        ]
        if keys_to_remove:
            logger.debug(
                f"Invalidating {len(keys_to_remove)} cache entries for '{name}'"
            )
            for key in keys_to_remove:
                del PokeDBLoader._pokemon_cache[key]

        logger.info(f"Successfully saved Pokemon '{name}'")
        return file_path

    @staticmethod
    def clear_cache() -> None:
        """
        Clear the entire Pokemon cache.

        Useful when you need to reload data from disk or free up memory.

        Examples:
            >>> # Load and cache Pokemon
            >>> pokemon = PokeDBLoader.load_pokemon("pikachu")
            >>> print(PokeDBLoader.get_cache_size())
            1
            >>> # Clear the cache
            >>> PokeDBLoader.clear_cache()
            >>> print(PokeDBLoader.get_cache_size())
            0
        """
        cache_size = len(PokeDBLoader._pokemon_cache)
        PokeDBLoader._pokemon_cache.clear()
        logger.info(f"Cleared Pokemon cache ({cache_size} entries)")

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
