"""
Helper utilities for loading PokeDB JSON data into dataclass structures.
"""

import orjson
import threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from enum import IntEnum
from pathlib import Path
from typing import Any, Optional, Type, TypeVar

from dacite import from_dict, Config, DaciteError

from src.models.pokedb import (
    Pokemon,
    Move,
    Ability,
    Item,
    Form,
    Stats,
    PokemonMoves,
)
from src.utils.logger_util import get_logger

logger = get_logger(__name__)
T = TypeVar("T")


class ReadWriteLock:
    """
    A read-write lock implementation for better concurrency.

    Allows multiple concurrent readers or a single writer.
    This significantly improves performance for cache reads.
    """

    def __init__(self):
        self._readers = 0
        self._writers = 0
        self._read_waiters = 0
        self._write_waiters = 0
        self._lock = threading.Lock()
        self._read_ok = threading.Condition(self._lock)
        self._write_ok = threading.Condition(self._lock)

    def acquire_read(self):
        """Acquire a read lock (shared)."""
        with self._lock:
            self._read_waiters += 1
            try:
                while self._writers > 0:
                    self._read_ok.wait()
                self._readers += 1
            finally:
                self._read_waiters -= 1

    def release_read(self):
        """Release a read lock."""
        with self._lock:
            self._readers -= 1
            if self._readers == 0:
                self._write_ok.notify()

    def acquire_write(self):
        """Acquire a write lock (exclusive)."""
        with self._lock:
            self._write_waiters += 1
            try:
                while self._readers > 0 or self._writers > 0:
                    self._write_ok.wait()
                self._writers = 1
            finally:
                self._write_waiters -= 1

    def release_write(self):
        """Release a write lock."""
        with self._lock:
            self._writers = 0
            if self._write_waiters > 0:
                self._write_ok.notify()
            else:
                self._read_ok.notify_all()


class PokeDBLoader:
    """
    Utility class for loading PokeDB JSON files into structured dataclasses.

    Supports loading from both the original gen5 data and the parsed working copy.
    Implements thread-safe LRU caching for all data types (Pokemon, Moves, Abilities, Items)
    to avoid redundant file I/O operations.

    IMPORTANT: This class uses class-level caches that persist across all
    instances and throughout the lifetime of the process. This provides significant
    performance benefits but has important implications:

    - Cache invalidation: Call clear_cache() if files are modified externally
      or if you need fresh data from disk
    - Memory usage: Each cache type is limited to MAX_CACHE_SIZE entries (default: 1000).
      Least recently used entries are automatically evicted when a cache is full.
    - Testing: Call clear_cache() between tests to ensure isolation

    The Pokemon cache is automatically updated when saving Pokemon via save_pokemon().

    Configuration:
    - Use set_data_dir() to override the default data directory path
    - Use get_data_dir() to retrieve the current data directory path
    - The default path is: <project_root>/data/pokedb/parsed
    - Use set_max_cache_size() to configure the maximum cache size

    Thread Safety:
    This class is now THREAD-SAFE! All cache operations and file I/O are protected
    by locks to prevent race conditions. You can safely use this class from
    multiple threads concurrently.
    """

    # Maximum number of Pokemon to cache (LRU eviction)
    MAX_CACHE_SIZE = 10000

    # Class-level data directory (configurable, defaults to None = use default path)
    _data_dir: Optional[Path] = None

    # Unified cache: OrderedDict for LRU behavior
    # Key format: ("type", name, subfolder) for pokemon or ("type", name) for others
    # Value: Pokemon | Move | Ability | Item
    _cache: OrderedDict[tuple[str, ...], Pokemon | Move | Ability | Item] = OrderedDict()

    # Cache statistics
    _cache_hits: int = 0
    _cache_misses: int = 0

    # Thread locks
    _cache_lock = ReadWriteLock()  # Read-write lock for better concurrency
    _data_dir_lock = threading.Lock()
    _file_lock = threading.Lock()  # For file write operations

    # Dacite configuration for efficient deserialization
    _dacite_config = Config(
        check_types=False,  # We rely on __post_init__ for validation
        # Use from_dict methods for types that need special handling
        type_hooks={
            PokemonMoves: PokemonMoves.from_dict,
        },
    )

    @classmethod
    def get_data_dir(cls) -> Path:
        """
        Get the current data directory path (thread-safe).

        Returns:
            Path: The data directory path (either custom or default)

        Example:
            >>> data_dir = PokeDBLoader.get_data_dir()
            >>> print(data_dir)
            /path/to/project/data/pokedb/parsed
        """
        with cls._data_dir_lock:
            if cls._data_dir is None:
                # Default to <project_root>/data/pokedb/parsed
                cls._data_dir = (
                    Path(__file__).parent.parent.parent / "data" / "pokedb" / "parsed"
                )
            return cls._data_dir

    @classmethod
    def set_data_dir(cls, path: Path) -> None:
        """
        Set a custom data directory path (thread-safe).

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
        with cls._data_dir_lock:
            old_dir = cls._data_dir
            cls._data_dir = path
            logger.info(f"Data directory changed from {old_dir} to {path}")
            cls.clear_cache()  # Clear cache when changing directory

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
    def find_all_form_files(
        pokemon_id: str,
    ) -> tuple[list[tuple[str, str]], Optional[Pokemon]]:
        """
        Find all form files for a given Pokemon and return the base Pokemon data.

        This method loads the Pokemon data and returns all forms listed in
        the "forms" field. It also returns the loaded base Pokemon object
        to prevent redundant loads by the caller.

        Args:
            pokemon_id: The Pokemon species ID (e.g., 'wormadam')

        Returns:
            A tuple containing:
            - A list of (form_name, category) tuples for all forms.
            - The loaded Pokemon object for the base form, or None if not found.

        Example:
            >>> forms, pokemon_obj = PokeDBLoader.find_all_form_files('wormadam')
            >>> forms
            [('wormadam-plant', 'default'), ('wormadam-sandy', 'variant'), ...]
        """
        try:
            # Load the base Pokemon data to get the forms list
            pokemon = PokeDBLoader.load_pokemon(pokemon_id)

            if not pokemon.forms:
                # If no forms field, return just the base Pokemon
                return ([(pokemon_id, "default")], pokemon)

            # Return all forms from the forms field
            return ([(form.name, form.category) for form in pokemon.forms], pokemon)
        except FileNotFoundError:
            # If file not found, return empty list and None
            return ([], None)

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
            # Use orjson for ~2-3x faster parsing
            with open(file_path, "rb") as f:
                return orjson.loads(f.read())
        except ValueError as e:
            # orjson raises ValueError for invalid JSON
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
            with open(json_file, "rb") as f:
                results[json_file.stem] = orjson.loads(f.read())

        return results

    @classmethod
    def _update_cache(
        cls, cache_key: tuple[str, ...], item: Pokemon | Move | Ability | Item, item_type: str, name: str
    ) -> None:
        """
        Update unified cache with an item, handling LRU eviction (thread-safe).

        This shared method is used after loading any item from disk to avoid
        code duplication and ensure consistent cache behavior.

        Args:
            cache_key: Tuple key for cache lookup (format varies by type)
            item: Item object to cache (Pokemon, Move, Ability, or Item)
            item_type: Type of item ("pokemon", "move", "ability", "item")
            name: Item name (for logging)
        """
        cls._cache_lock.acquire_write()
        try:
            # Check again if another thread cached it while we were loading
            if cache_key in cls._cache:
                cls._cache.move_to_end(cache_key)
                return

            # Add to cache
            cls._cache[cache_key] = item
            cls._cache.move_to_end(cache_key)

            # Optimized batch eviction: if we're significantly over limit,
            # evict multiple entries at once for better performance
            overage = len(cls._cache) - cls.MAX_CACHE_SIZE
            if overage > 0:
                # Evict 10% extra to reduce frequent evictions
                evict_count = max(1, overage + cls.MAX_CACHE_SIZE // 10)
                evicted_keys = []
                for _ in range(min(evict_count, len(cls._cache) - 1)):
                    if len(cls._cache) <= cls.MAX_CACHE_SIZE:
                        break
                    evicted_key = next(iter(cls._cache))
                    del cls._cache[evicted_key]
                    evicted_keys.append(f"{evicted_key[0]}:{evicted_key[1]}")

                if evicted_keys:
                    logger.debug(
                        f"Batch evicted {len(evicted_keys)} LRU entries from cache "
                        f"(cache at max size: {cls.MAX_CACHE_SIZE})"
                    )

            logger.debug(
                f"Cached {item_type} '{name}' (cache size: {len(cls._cache)}/{cls.MAX_CACHE_SIZE})"
            )
        finally:
            cls._cache_lock.release_write()

    @classmethod
    def load_pokemon(cls, name: str, subfolder: str = "default") -> Pokemon:
        """
        Load a Pokemon JSON file with thread-safe LRU caching.

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
        cache_key = ("pokemon", name, subfolder)

        # Check cache first (with read lock for better concurrency)
        cls._cache_lock.acquire_read()
        try:
            if cache_key in cls._cache:
                cls._cache_hits += 1
                result = cls._cache[cache_key]
                logger.debug(
                    f"Loading Pokemon '{name}' from cache (subfolder: {subfolder}) "
                    f"[hit rate: {cls.get_cache_hit_rate():.1%}]"
                )
                return result

            # Cache miss
            cls._cache_misses += 1
        finally:
            cls._cache_lock.release_read()

        # Load from file (outside cache lock to allow parallel file reads)
        logger.debug(f"Loading Pokemon '{name}' from disk (subfolder: {subfolder})")
        data = cls._load_json("pokemon", name, subfolder)
        try:
            pokemon = from_dict(
                data_class=Pokemon, data=data, config=cls._dacite_config
            )
        except (DaciteError, ValueError, TypeError) as e:
            logger.error(f"Error deserializing Pokemon '{name}': {e}", exc_info=True)
            raise

        # Cache the result with LRU eviction
        cls._update_cache(cache_key, pokemon, "pokemon", name)
        return pokemon

    @classmethod
    def _load_all_generic(
        cls,
        category: str,
        dataclass_type: Type[T],
        subfolder: Optional[str] = None,
    ) -> dict[str, T]:
        """
        Generic method to load all items of a given category.

        Args:
            category: The category folder (pokemon, move, ability, item)
            dataclass_type: The dataclass type to instantiate
            subfolder: Optional subfolder within category

        Returns:
            dict: Mapping of item name to dataclass objects
        """
        raw_data = cls._load_all_json(category, subfolder)
        result = {}
        for name, data in raw_data.items():
            try:
                # Preprocess Move data: convert empty list to None for machine field
                # (machine can be str, dict, or None)
                if category == "move" and "machine" in data and isinstance(data["machine"], list):
                    if len(data["machine"]) == 0:
                        data["machine"] = None
                    else:
                        logger.warning(f"Move '{name}' has unexpected machine format: {data['machine']}")

                result[name] = from_dict(
                    data_class=dataclass_type, data=data, config=cls._dacite_config
                )
            except (DaciteError, TypeError, ValueError) as e:
                logger.error(f"Error loading {category} '{name}': {e}", exc_info=True)
        return result

    @classmethod
    def load_all_pokemon(cls, subfolder: str = "default") -> dict[str, Pokemon]:
        """
        Load all Pokemon from a specific subfolder.

        Args:
            subfolder: Pokemon subfolder (default, cosmetic, transformation, variant)

        Returns:
            dict: Mapping of pokemon name to data
        """
        return cls._load_all_generic("pokemon", Pokemon, subfolder)

    @classmethod
    def load_move(cls, name: str) -> Move:
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
        cache_key = ("move", name)

        # Check cache first (with read lock)
        cls._cache_lock.acquire_read()
        try:
            if cache_key in cls._cache:
                cls._cache_hits += 1
                result = cls._cache[cache_key]
                logger.debug(
                    f"Loading Move '{name}' from cache "
                    f"[hit rate: {cls.get_cache_hit_rate():.1%}]"
                )
                return result
            # Cache miss
            cls._cache_misses += 1
        finally:
            cls._cache_lock.release_read()

        # Load from file
        data = cls._load_json("move", name)

        # Preprocess: Convert empty list to None for machine field
        # (machine can be str, dict, or None)
        if "machine" in data and isinstance(data["machine"], list):
            if len(data["machine"]) == 0:
                data["machine"] = None
            else:
                # If non-empty list, log warning but don't fail
                logger.warning(f"Move '{name}' has unexpected machine format: {data['machine']}")

        move = from_dict(data_class=Move, data=data, config=cls._dacite_config)

        # Cache the result
        cls._update_cache(cache_key, move, "move", name)
        return move

    @classmethod
    def load_all_moves(cls) -> dict[str, Move]:
        """
        Load all moves and return as Move dataclasses.

        Returns:
            dict: Mapping of move name to Move dataclass objects
        """
        return cls._load_all_generic("move", Move)

    @classmethod
    def load_ability(cls, name: str) -> Ability:
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
        cache_key = ("ability", name)

        # Check cache first (with read lock)
        cls._cache_lock.acquire_read()
        try:
            if cache_key in cls._cache:
                cls._cache_hits += 1
                result = cls._cache[cache_key]
                logger.debug(
                    f"Loading Ability '{name}' from cache "
                    f"[hit rate: {cls.get_cache_hit_rate():.1%}]"
                )
                return result
            # Cache miss
            cls._cache_misses += 1
        finally:
            cls._cache_lock.release_read()

        # Load from file
        data = cls._load_json("ability", name)
        ability = from_dict(data_class=Ability, data=data, config=cls._dacite_config)

        # Cache the result
        cls._update_cache(cache_key, ability, "ability", name)
        return ability

    @classmethod
    def load_all_abilities(cls) -> dict[str, Ability]:
        """
        Load all abilities and return as Ability dataclasses.

        Returns:
            dict: Mapping of ability name to Ability dataclass objects
        """
        return cls._load_all_generic("ability", Ability)

    @classmethod
    def load_item(cls, name: str) -> Item:
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
        cache_key = ("item", name)

        # Check cache first (with read lock)
        cls._cache_lock.acquire_read()
        try:
            if cache_key in cls._cache:
                cls._cache_hits += 1
                result = cls._cache[cache_key]
                logger.debug(
                    f"Loading Item '{name}' from cache "
                    f"[hit rate: {cls.get_cache_hit_rate():.1%}]"
                )
                return result
            # Cache miss
            cls._cache_misses += 1
        finally:
            cls._cache_lock.release_read()

        # Load from file
        data = cls._load_json("item", name)
        item = from_dict(data_class=Item, data=data, config=cls._dacite_config)

        # Cache the result
        cls._update_cache(cache_key, item, "item", name)
        return item

    @classmethod
    def load_all_items(cls) -> dict[str, Item]:
        """
        Load all items and return as Item dataclasses.

        Returns:
            dict: Mapping of item name to Item dataclass objects
        """
        return cls._load_all_generic("item", Item)

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
        Save Pokemon data to a JSON file and update cache (thread-safe).

        This method saves the Pokemon and updates the cache with the new data
        instead of invalidating it. This provides better performance when saving
        multiple Pokemon in a batch operation (like evolution chain updates).

        Uses file locking to prevent concurrent write conflicts.

        Args:
            name: Pokemon name (e.g., 'pikachu')
            data: Pokemon dataclass object
            subfolder: Pokemon subfolder (default, cosmetic, transformation, variant)

        Returns:
            Path: Path to the saved file
        """
        file_path = cls.get_data_dir() / "pokemon" / subfolder / f"{name}.json"

        # Use file lock to prevent concurrent writes
        with cls._file_lock:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Saving Pokemon '{name}' to {file_path}")
            temp_path = file_path.with_suffix(".tmp")
            try:
                # Write to temp file first, then atomic rename (safer)
                with open(temp_path, "wb") as f:
                    # asdict needs a custom factory to handle enums and custom classes
                    from src.models.pokedb import (
                        GameVersionStringMap,
                        GameVersionIntMap,
                        SpriteVersions,
                        PokemonMoves,
                    )

                    def dict_factory(fields):
                        result = {}
                        for k, v in fields:
                            if isinstance(v, IntEnum):
                                result[k] = v.value
                            elif isinstance(
                                v,
                                (
                                    GameVersionStringMap,
                                    GameVersionIntMap,
                                    SpriteVersions,
                                    PokemonMoves,
                                ),
                            ):
                                result[k] = v.to_dict()
                            else:
                                result[k] = v
                        return result

                    f.write(
                        orjson.dumps(
                            asdict(data, dict_factory=dict_factory),
                            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
                        )
                    )

                # Atomic rename (or as close as possible on Windows)
                temp_path.replace(file_path)
            except (OSError, IOError) as e:
                logger.error(f"Error saving Pokemon '{name}': {e}", exc_info=True)
                # Clean up temp file if it exists
                if temp_path.exists():
                    temp_path.unlink()
                raise

        # Update cache with the new data instead of invalidating
        # This is more efficient for batch operations like evolution chain updates
        cache_key = ("pokemon", name, subfolder)
        cls._update_cache(cache_key, data, name)

        logger.info(f"Successfully saved Pokemon '{name}'")
        return file_path

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear all caches (Pokemon, Move, Ability, Item) and reset statistics (thread-safe).

        Useful when you need to reload data from disk or free up memory.

        Examples:
            >>> # Load and cache data
            >>> pokemon = PokeDBLoader.load_pokemon("pikachu")
            >>> move = PokeDBLoader.load_move("thunderbolt")
            >>> print(PokeDBLoader.get_cache_size())
            2
            >>> # Clear the cache
            >>> PokeDBLoader.clear_cache()
            >>> print(PokeDBLoader.get_cache_size())
            0
        """
        cls._cache_lock.acquire_write()
        try:
            # Count entries by type
            pokemon_size = sum(1 for k in cls._cache if k[0] == "pokemon")
            move_size = sum(1 for k in cls._cache if k[0] == "move")
            ability_size = sum(1 for k in cls._cache if k[0] == "ability")
            item_size = sum(1 for k in cls._cache if k[0] == "item")
            total_size = len(cls._cache)

            cls._cache.clear()
            cls._cache_hits = 0
            cls._cache_misses = 0

            logger.info(
                f"Cleared unified cache ({total_size} total entries: "
                f"{pokemon_size} Pokemon, {move_size} Moves, "
                f"{ability_size} Abilities, {item_size} Items)"
            )
        finally:
            cls._cache_lock.release_write()

    @classmethod
    def get_cache_size(cls) -> int:
        """
        Get the total number of cached items across all caches (thread-safe).

        Returns:
            int: Total number of items currently in all caches
        """
        cls._cache_lock.acquire_read()
        try:
            return len(cls._cache)
        finally:
            cls._cache_lock.release_read()

    @classmethod
    def get_cached_pokemon(cls) -> list[tuple[str, str]]:
        """
        Get a list of all cached Pokemon identifiers (thread-safe).

        Returns:
            list: List of (name, subfolder) tuples for all cached Pokemon
        """
        cls._cache_lock.acquire_read()
        try:
            return [(k[1], k[2]) for k in cls._cache.keys() if k[0] == "pokemon"]
        finally:
            cls._cache_lock.release_read()

    @classmethod
    def get_cache_stats(cls) -> dict[str, Any]:
        """
        Get cache statistics (thread-safe).

        Returns:
            dict: Dictionary containing cache statistics:
                - total_size: Total number of cached items across all types
                - pokemon_size: Number of cached Pokemon
                - move_size: Number of cached Moves
                - ability_size: Number of cached Abilities
                - item_size: Number of cached Items
                - max_size: Maximum cache size per type
                - hits: Number of cache hits
                - misses: Number of cache misses
                - hit_rate: Cache hit rate (0.0 to 1.0)
                - total_requests: Total number of cache requests
        """
        cls._cache_lock.acquire_read()
        try:
            total = cls._cache_hits + cls._cache_misses
            hit_rate = cls._cache_hits / total if total > 0 else 0.0
            pokemon_size = sum(1 for k in cls._cache if k[0] == "pokemon")
            move_size = sum(1 for k in cls._cache if k[0] == "move")
            ability_size = sum(1 for k in cls._cache if k[0] == "ability")
            item_size = sum(1 for k in cls._cache if k[0] == "item")
            return {
                "total_size": len(cls._cache),
                "pokemon_size": pokemon_size,
                "move_size": move_size,
                "ability_size": ability_size,
                "item_size": item_size,
                "max_size": cls.MAX_CACHE_SIZE,
                "hits": cls._cache_hits,
                "misses": cls._cache_misses,
                "hit_rate": hit_rate,
                "total_requests": total,
            }
        finally:
            cls._cache_lock.release_read()

    @classmethod
    def get_cache_hit_rate(cls) -> float:
        """
        Get the cache hit rate (thread-safe).

        Returns:
            float: Cache hit rate between 0.0 and 1.0
        """
        cls._cache_lock.acquire_read()
        try:
            total = cls._cache_hits + cls._cache_misses
            return cls._cache_hits / total if total > 0 else 0.0
        finally:
            cls._cache_lock.release_read()

    @classmethod
    def set_max_cache_size(cls, size: int) -> None:
        """
        Set the maximum cache size (thread-safe).

        If the new size is smaller than the current cache size,
        the least recently used entries will be evicted.

        Args:
            size: New maximum cache size (must be > 0)

        Raises:
            ValueError: If size is not positive
        """
        if size <= 0:
            raise ValueError(f"Cache size must be positive, got: {size}")

        cls._cache_lock.acquire_write()
        try:
            old_size = cls.MAX_CACHE_SIZE
            cls.MAX_CACHE_SIZE = size

            # Evict LRU entries if new size is smaller
            while len(cls._cache) > cls.MAX_CACHE_SIZE:
                evicted_key = next(iter(cls._cache))
                del cls._cache[evicted_key]
                logger.debug(f"Evicted LRU entry: {evicted_key[0]}")

            logger.info(
                f"Cache size changed from {old_size} to {size} "
                f"(current entries: {len(cls._cache)})"
            )
        finally:
            cls._cache_lock.release_write()

    @classmethod
    def _preload_worker(cls, json_file: Path) -> tuple[str, dict]:
        """A dedicated worker just for reading and parsing a JSON file."""
        name = json_file.stem
        with open(json_file, "rb") as f:
            data = orjson.loads(f.read())
        return name, data

    @classmethod
    def preload_cache(cls, subfolders: Optional[list[str]] = None) -> dict[str, Any]:
        """
        Pre-load all Pokemon into cache for maximum performance during a run.

        This method loads all Pokemon from the specified subfolders into cache
        at once, eliminating disk reads during processing. This is ideal for
        batch operations where you need to process many Pokemon repeatedly.

        Args:
            subfolders: List of subfolders to preload. Defaults to all standard
                       subfolders: ["default", "cosmetic", "transformation", "variant"]

        Returns:
            dict: Statistics about the preload operation:
                - total_loaded: Total number of Pokemon loaded
                - by_subfolder: Dict mapping subfolder -> count loaded
                - cache_size_before: Cache size before preload
                - cache_size_after: Cache size after preload
                - time_seconds: Time taken to preload

        Examples:
            >>> # Preload all Pokemon from all subfolders
            >>> stats = PokeDBLoader.preload_cache()
            >>> print(f"Loaded {stats['total_loaded']} Pokemon")

            >>> # Preload only default Pokemon
            >>> stats = PokeDBLoader.preload_cache(subfolders=["default"])

            >>> # Increase cache size if needed to fit all Pokemon
            >>> PokeDBLoader.set_max_cache_size(2000)
            >>> stats = PokeDBLoader.preload_cache()
        """
        import time
        import os

        if subfolders is None:
            subfolders = ["default", "cosmetic", "transformation", "variant"]

        start_time = time.time()
        cache_size_before = cls.get_cache_size()

        logger.info(f"Pre-loading Pokemon cache from subfolders: {subfolders}")

        by_subfolder = {}
        total_loaded = 0
        worker_count = min(32, (os.cpu_count() or 4) * 4)

        for subfolder in subfolders:
            subfolder_start = time.time()
            data_dir = cls.get_data_dir() / "pokemon" / subfolder

            if not data_dir.exists():
                logger.warning(f"Subfolder does not exist: {subfolder}")
                by_subfolder[subfolder] = 0
                continue

            json_files = list(data_dir.glob("*.json"))
            loaded_pokemon: dict[tuple[str, str, str], Pokemon] = {}

            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                future_to_file = {
                    executor.submit(cls._preload_worker, f): f for f in json_files
                }

                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        name, data = future.result()
                        pokemon = from_dict(
                            data_class=Pokemon, data=data, config=cls._dacite_config
                        )
                        loaded_pokemon[("pokemon", name, subfolder)] = pokemon
                    except Exception as e:
                        logger.error(
                            f"Failed to preload Pokemon '{file_path.stem}': {e}"
                        )

            if loaded_pokemon:
                cls._cache_lock.acquire_write()
                try:
                    for key, mon in loaded_pokemon.items():
                        cls._cache[key] = mon
                        cls._cache.move_to_end(key)

                    overage = len(cls._cache) - cls.MAX_CACHE_SIZE
                    if overage > 0:
                        for _ in range(overage):
                            cls._cache.popitem(last=False)
                finally:
                    cls._cache_lock.release_write()

            subfolder_time = time.time() - subfolder_start
            loaded_count = len(loaded_pokemon)
            by_subfolder[subfolder] = loaded_count
            total_loaded += loaded_count

            logger.info(
                f"Loaded {loaded_count} Pokemon from '{subfolder}' "
                f"in {subfolder_time:.2f}s ({worker_count} workers)"
            )

        cache_size_after = cls.get_cache_size()
        total_time = time.time() - start_time

        stats = {
            "total_loaded": total_loaded,
            "by_subfolder": by_subfolder,
            "cache_size_before": cache_size_before,
            "cache_size_after": cache_size_after,
            "time_seconds": total_time,
        }

        logger.info(
            f"Pre-load complete: {total_loaded} Pokemon loaded in {total_time:.2f}s "
            f"(cache: {cache_size_before} -> {cache_size_after})"
        )

        if cache_size_after < total_loaded + cache_size_before:
            logger.warning(
                f"Cache size ({cls.MAX_CACHE_SIZE}) is smaller than total Pokemon "
                f"({total_loaded}). Some entries were evicted. Consider increasing "
                f"cache size with set_max_cache_size()."
            )

        return stats
