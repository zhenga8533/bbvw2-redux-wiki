"""
Helper utilities for loading PokeDB JSON data into dataclass structures.
"""

from __future__ import annotations

import os
import threading
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from enum import IntEnum
from pathlib import Path
from typing import Any, Generator, Optional, Type, TypeVar, cast

import orjson
from dacite import Config, DaciteError, from_dict

from src.utils.core.logger import get_logger
from src.utils.data.constants import POKEMON_FORM_SUBFOLDERS
from src.utils.data.models import (
    Ability,
    Item,
    Move,
    Pokemon,
    PokemonMoves,
)
from src.utils.text.text_util import name_to_id

logger = get_logger(__name__)
T = TypeVar("T")


class ReadWriteLock:
    """A read-write lock implementation for better concurrency."""

    def __init__(self):
        """Initialize the read-write lock."""
        self._readers = 0
        self._writers = 0
        self._read_waiters = 0
        self._write_waiters = 0
        self._lock = threading.Lock()
        self._read_ok = threading.Condition(self._lock)
        self._write_ok = threading.Condition(self._lock)

    def acquire_read(self) -> None:
        """Acquire a read lock (shared)."""
        with self._lock:
            self._read_waiters += 1
            try:
                while self._writers > 0:
                    self._read_ok.wait()
                self._readers += 1
            finally:
                self._read_waiters -= 1

    def release_read(self) -> None:
        """Release a read lock."""
        with self._lock:
            self._readers -= 1
            if self._readers == 0:
                self._write_ok.notify()

    def acquire_write(self) -> None:
        """Acquire a write lock (exclusive)."""
        with self._lock:
            self._write_waiters += 1
            try:
                while self._readers > 0 or self._writers > 0:
                    self._write_ok.wait()
                self._writers = 1
            finally:
                self._write_waiters -= 1

    def release_write(self) -> None:
        """Release a write lock."""
        with self._lock:
            self._writers = 0
            if self._write_waiters > 0:
                self._write_ok.notify()
            else:
                self._read_ok.notify_all()

    def read_lock(self) -> _ReadLockContext:
        """Context manager for read lock."""
        return _ReadLockContext(self)

    def write_lock(self) -> _WriteLockContext:
        """Context manager for write lock."""
        return _WriteLockContext(self)


class _ReadLockContext:
    """Context manager for read lock."""

    def __init__(self, lock: ReadWriteLock):
        """Initialize the read lock context manager.

        Args:
            lock (ReadWriteLock): The read-write lock to manage.
        """
        self.lock = lock

    def __enter__(self) -> _ReadLockContext:
        """Acquire the read lock.

        Returns:
            _ReadLockContext: The read lock context manager.
        """
        self.lock.acquire_read()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release the read lock.

        Returns:
            bool: Always returns False to propagate exceptions.
        """
        self.lock.release_read()
        return False


class _WriteLockContext:
    """Context manager for write lock."""

    def __init__(self, lock: ReadWriteLock):
        """Initialize the write lock context manager.

        Args:
            lock (ReadWriteLock): The read-write lock to manage.
        """
        self.lock = lock

    def __enter__(self) -> _WriteLockContext:
        """Acquire the write lock.

        Returns:
            _WriteLockContext: The write lock context manager.
        """
        self.lock.acquire_write()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release the write lock.

        Returns:
            bool: Always returns False to propagate exceptions.
        """
        self.lock.release_write()
        return False


class PokeDBLoader:
    """
    Utility class for loading PokeDB JSON files into structured dataclasses.

    Supports loading from both the original data and the parsed working copy.
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
    This class is THREAD-SAFE! All cache operations and file I/O are protected by locks to
    prevent race conditions. You can safely use this class from multiple threads concurrently.
    """

    # Maximum number of Pokemon to cache (LRU eviction)
    MAX_CACHE_SIZE = 9999

    # Class-level data directory (configurable, defaults to None = use default path)
    _data_dir: Optional[Path] = None

    # Unified cache: OrderedDict for LRU behavior
    # Key format: ("type", name, subfolder) for pokemon or ("type", name) for others
    # Value: Pokemon | Move | Ability | Item
    _cache: OrderedDict[tuple[str, ...], Pokemon | Move | Ability | Item] = (
        OrderedDict()
    )

    # Subfolder cache: Maps pokemon name to its subfolder
    # This allows save_pokemon to know which subfolder to use
    _subfolder_cache: dict[str, str] = {}

    # Cache statistics
    _cache_hits: int = 0
    _cache_misses: int = 0

    # Thread locks
    _cache_lock = ReadWriteLock()  # For cache operations
    _data_dir_lock = threading.Lock()  # For data directory operations
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
        """Get the current data directory path (thread-safe).

        Returns:
            Path: The data directory path (either custom or default)
        """
        with cls._data_dir_lock:
            if cls._data_dir is None:
                # Default to <project_root>/data/pokedb/parsed
                # Path is: src/utils/core/loader.py -> parent = core -> parent = utils -> parent = src -> parent = project_root
                cls._data_dir = (
                    Path(__file__).parent.parent.parent.parent
                    / "data"
                    / "pokedb"
                    / "parsed"
                )
            return cls._data_dir

    @classmethod
    def set_data_dir(cls, path: Path) -> None:
        """Set a custom data directory path (thread-safe).

        Args:
            path (Path): The new data directory path
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
        """Find a file, with fallback to check for variants with form suffixes.

        Args:
            category (str): The category folder (pokemon, move, ability, item)
            name (str): The name of the JSON file (without .json extension)
            subfolder (Optional[str], optional): The subfolder within the category. Defaults to None.

        Returns:
            Optional[Path]: The found file path, or None if not found
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
        """Find all form files for a given Pokemon and return the base Pokemon data.

        Args:
            pokemon_id (str): The Pokemon species ID (e.g., 'Wormadam', 'wormadam', or 'WORMADAM')

        Returns:
            tuple[list[tuple[str, str]], Optional[Pokemon]]: A tuple containing a list of form files and the base Pokemon object.
        """
        # Normalize the pokemon_id to ID format
        pokemon_id = name_to_id(pokemon_id)

        # Load the base Pokemon data to get the forms list
        pokemon = PokeDBLoader.load_pokemon(pokemon_id)

        if pokemon is None:
            # If file not found, return empty list and None
            return ([], None)

        if not pokemon.forms:
            # If no forms field, return just the base Pokemon
            return ([(pokemon_id, "default")], pokemon)

        # Return all forms from the forms field
        return ([(form.name, form.category) for form in pokemon.forms], pokemon)

    @classmethod
    def _load_json(
        cls,
        category: str,
        name: str,
        subfolder: Optional[str] = None,
        silent: bool = False,
    ) -> dict:
        """Load a JSON file from the PokeDB directory.

        Args:
            category (str): The category folder (pokemon, move, ability, item)
            name (str): The name of the JSON file (without .json extension)
            subfolder (Optional[str], optional): The subfolder within the category. Defaults to None.
            silent (bool, optional): If True, don't log error messages for file not found. Defaults to False.

        Raises:
            FileNotFoundError: If the file doesn't exist

        Returns:
            dict: The parsed JSON data
        """
        file_path = cls._find_file(category, name, subfolder)

        if file_path is None:
            # Provide helpful error message
            data_dir = cls.get_data_dir()
            if subfolder:
                search_location = data_dir / category / subfolder
            else:
                search_location = data_dir / category
            if not silent:
                logger.warning(f"File not found: {name}.json in {search_location}")
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
        """Load all JSON files from a category folder.

        Args:
            category (str): The category folder (pokemon, move, ability, item)
            subfolder (Optional[str], optional): The subfolder within the category. Defaults to None.

        Returns:
            dict[str, dict]: Mapping of filename (without .json) to parsed JSON data
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
        cls,
        cache_key: tuple[str, ...],
        item: Pokemon | Move | Ability | Item,
        item_type: str,
        name: str,
    ) -> None:
        """Update the cache with a new item, handling LRU eviction.

        Args:
            cache_key (tuple[str, ...]): The cache key
            item (Pokemon | Move | Ability | Item): The item to cache
            item_type (str): The type of item (pokemon, move, ability, item)
            name (str): The name of the item (for logging)
        """
        # Double-checked locking: check if already cached with read lock first
        with cls._cache_lock.read_lock():
            if cache_key in cls._cache:
                # Another thread already cached it, just update access order
                # Note: We can't safely move_to_end with read lock, so we'll
                # acquire write lock below
                needs_update = True
            else:
                needs_update = False

        if needs_update:
            # Update LRU order with write lock
            with cls._cache_lock.write_lock():
                if cache_key in cls._cache:
                    cls._cache.move_to_end(cache_key)
                    return

        # Add to cache with write lock
        with cls._cache_lock.write_lock():
            # Check again if another thread cached it while we were waiting
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

    @classmethod
    def load_pokemon(
        cls, name: str, subfolder: Optional[str] = None
    ) -> Optional[Pokemon]:
        """Load a Pokemon JSON file with thread-safe LRU caching.

        Args:
            name (str): Pokemon name (e.g., 'Pikachu', 'pikachu', or 'PIKACHU')
            subfolder (Optional[str], optional): The subfolder to search in. Defaults to None.

        Returns:
            Optional[Pokemon]: The loaded Pokemon, or None if not found.
        """
        # Normalize the name to ID format
        name = name_to_id(name)

        # If subfolder is provided, use the original behavior
        if subfolder is not None:
            return cls._load_pokemon_from_subfolder(name, subfolder)

        # Check if we have a cached subfolder for this Pokemon
        with cls._cache_lock.read_lock():
            cached_subfolder = cls._subfolder_cache.get(name)

        if cached_subfolder:
            # Try the cached subfolder first
            result = cls._load_pokemon_from_subfolder(name, cached_subfolder)
            if result:
                return result
            # If not found in cached subfolder, fall through to search all

        # Search all subfolders in order
        for search_subfolder in POKEMON_FORM_SUBFOLDERS:
            result = cls._load_pokemon_from_subfolder(name, search_subfolder)
            if result:
                # Cache the subfolder for future saves
                with cls._cache_lock.write_lock():
                    cls._subfolder_cache[name] = search_subfolder
                logger.debug(
                    f"Found Pokemon '{name}' in subfolder '{search_subfolder}', cached for future saves"
                )
                return result

        logger.warning(f"Pokemon '{name}' not found in any subfolder")
        return None

    @classmethod
    def _load_pokemon_from_subfolder(
        cls, name: str, subfolder: str
    ) -> Optional[Pokemon]:
        """Load a Pokemon from a specific subfolder.

        Args:
            name (str): Pokemon name (e.g., 'Pikachu', 'pikachu', or 'PIKACHU')
            subfolder (str): The subfolder to search in.

        Raises:
            TypeError: If the cached item is not a Pokemon.

        Returns:
            Optional[Pokemon]: The loaded Pokemon, or None if not found.
        """
        cache_key = ("pokemon", name, subfolder)

        # Check cache first (with read lock for better concurrency)
        with cls._cache_lock.read_lock():
            if cache_key in cls._cache:
                cls._cache_hits += 1
                result = cls._cache[cache_key]
                logger.debug(
                    f"Loading Pokemon '{name}' from cache (subfolder: {subfolder}) "
                    f"[hit rate: {cls.get_cache_hit_rate():.1%}]"
                )
                if not isinstance(result, Pokemon):
                    raise TypeError(
                        f"Cached item for key {cache_key} is not a Pokemon: {type(result)}"
                    )
                return result
            # Cache miss
            cls._cache_misses += 1

        # Load from file (outside cache lock to allow parallel file reads)
        logger.debug(f"Loading Pokemon '{name}' from disk (subfolder: {subfolder})")
        try:
            # Use silent=True to avoid error logging during auto-detection search
            data = cls._load_json("pokemon", name, subfolder, silent=True)
        except FileNotFoundError:
            logger.debug(f"Pokemon '{name}' not found in subfolder '{subfolder}'")
            return None

        try:
            pokemon = from_dict(
                data_class=Pokemon, data=data, config=cls._dacite_config
            )
        except (DaciteError, ValueError, TypeError) as e:
            logger.error(f"Error deserializing Pokemon '{name}': {e}", exc_info=True)
            return None

        # Cache the result with LRU eviction and update subfolder cache
        cls._update_cache(cache_key, pokemon, "pokemon", name)

        # Update subfolder cache so save operations use the correct location
        with cls._cache_lock.write_lock():
            cls._subfolder_cache[name] = subfolder

        return pokemon

    @classmethod
    def _load_all_generic(
        cls,
        category: str,
        dataclass_type: Type[T],
        subfolder: Optional[str] = None,
    ) -> dict[str, T]:
        """Load all items of a given category.

        Args:
            category (str): The category folder (pokemon, move, ability, item)
            dataclass_type (Type[T]): The dataclass type to instantiate
            subfolder (Optional[str], optional): The subfolder to search in. Defaults to None.

        Returns:
            dict[str, T]: Mapping of item name to dataclass objects
        """
        raw_data = cls._load_all_json(category, subfolder)
        result = {}
        for name, data in raw_data.items():
            try:
                # Preprocess Move data: convert empty list to None for machine field
                # (machine can be str, dict, or None)
                if (
                    category == "move"
                    and "machine" in data
                    and isinstance(data["machine"], list)
                ):
                    if len(data["machine"]) == 0:
                        data["machine"] = None
                    else:
                        logger.warning(
                            f"Move '{name}' has unexpected machine format: {data['machine']}"
                        )

                result[name] = from_dict(
                    data_class=dataclass_type, data=data, config=cls._dacite_config
                )
            except (DaciteError, TypeError, ValueError) as e:
                logger.error(f"Error loading {category} '{name}': {e}", exc_info=True)
        return result

    @classmethod
    def load_all_pokemon(cls, subfolder: str = "default") -> dict[str, Pokemon]:
        """Load all Pokemon from a specific subfolder.

        Args:
            subfolder (str, optional): The subfolder to search in. Defaults to "default".

        Returns:
            dict[str, Pokemon]: Mapping of Pokemon name to Pokemon dataclass objects
        """
        return cls._load_all_generic("pokemon", Pokemon, subfolder)

    @classmethod
    def load_move(cls, name: str) -> Optional[Move]:
        """Load a Move JSON file and return as a Move dataclass.

        Args:
            name (str): Move name (e.g., 'Thunderbolt', 'thunderbolt', or 'THUNDERBOLT')

        Raises:
            TypeError: If the cached item is not a Move.

        Returns:
            Optional[Move]: Move dataclass object, or None if not found
        """
        # Normalize the name to ID format
        name = name_to_id(name)
        cache_key = ("move", name)

        # Check cache first (with read lock)
        with cls._cache_lock.read_lock():
            if cache_key in cls._cache:
                cls._cache_hits += 1
                result = cls._cache[cache_key]
                logger.debug(
                    f"Loading Move '{name}' from cache "
                    f"[hit rate: {cls.get_cache_hit_rate():.1%}]"
                )
                if not isinstance(result, Move):
                    raise TypeError(
                        f"Cached item for key {cache_key} is not a Move: {type(result)}"
                    )
                return result
            # Cache miss
            cls._cache_misses += 1

        # Load from file
        try:
            data = cls._load_json("move", name)
        except FileNotFoundError:
            logger.debug(f"Move '{name}' not found")
            return None

        # Preprocess: Convert empty list to None for machine field
        # (machine can be str, dict, or None)
        if "machine" in data and isinstance(data["machine"], list):
            if len(data["machine"]) == 0:
                data["machine"] = None
            else:
                # If non-empty list, log warning but don't fail
                logger.warning(
                    f"Move '{name}' has unexpected machine format: {data['machine']}"
                )

        try:
            move = from_dict(data_class=Move, data=data, config=cls._dacite_config)
        except (DaciteError, ValueError, TypeError) as e:
            logger.error(f"Error deserializing Move '{name}': {e}", exc_info=True)
            return None

        # Cache the result
        cls._update_cache(cache_key, move, "move", name)
        return move

    @classmethod
    def load_all_moves(cls) -> dict[str, Move]:
        """Load all moves and return as Move dataclasses.

        Returns:
            dict[str, Move]: Mapping of move name to Move dataclass objects
        """
        return cls._load_all_generic("move", Move)

    @classmethod
    def load_ability(cls, name: str) -> Optional[Ability]:
        """Load an Ability JSON file and return as an Ability dataclass.

        Args:
            name (str): Ability name (e.g., 'Intimidate', 'intimidate', or 'INTIMIDATE')

        Raises:
            TypeError: If the cached item is not an Ability.

        Returns:
            Optional[Ability]: Ability dataclass object, or None if not found
        """
        # Normalize the name to ID format
        name = name_to_id(name)
        cache_key = ("ability", name)

        # Check cache first (with read lock)
        with cls._cache_lock.read_lock():
            if cache_key in cls._cache:
                cls._cache_hits += 1
                result = cls._cache[cache_key]
                logger.debug(
                    f"Loading Ability '{name}' from cache "
                    f"[hit rate: {cls.get_cache_hit_rate():.1%}]"
                )
                if not isinstance(result, Ability):
                    raise TypeError(
                        f"Cached item for key {cache_key} is not an Ability: {type(result)}"
                    )
                return result
            # Cache miss
            cls._cache_misses += 1

        # Load from file
        try:
            data = cls._load_json("ability", name)
        except FileNotFoundError:
            logger.debug(f"Ability '{name}' not found")
            return None

        try:
            ability = from_dict(
                data_class=Ability, data=data, config=cls._dacite_config
            )
        except (DaciteError, ValueError, TypeError) as e:
            logger.error(f"Error deserializing Ability '{name}': {e}", exc_info=True)
            return None

        # Cache the result
        cls._update_cache(cache_key, ability, "ability", name)
        return ability

    @classmethod
    def load_all_abilities(cls) -> dict[str, Ability]:
        """Load all abilities and return as Ability dataclasses.

        Returns:
            dict[str, Ability]: Mapping of ability name to Ability dataclass objects
        """
        return cls._load_all_generic("ability", Ability)

    @classmethod
    def load_item(cls, name: str) -> Optional[Item]:
        """Load an Item JSON file and return as an Item dataclass.

        Args:
            name (str): Item name (e.g., 'Potion', 'potion', or 'POTION')

        Raises:
            TypeError: If the cached item is not an Item.

        Returns:
            Optional[Item]: Item dataclass object, or None if not found
        """
        # Normalize the name to ID format
        name = name_to_id(name)
        cache_key = ("item", name)

        # Check cache first (with read lock)
        with cls._cache_lock.read_lock():
            if cache_key in cls._cache:
                cls._cache_hits += 1
                result = cls._cache[cache_key]
                logger.debug(
                    f"Loading Item '{name}' from cache "
                    f"[hit rate: {cls.get_cache_hit_rate():.1%}]"
                )
                if not isinstance(result, Item):
                    raise TypeError(
                        f"Cached item for key {cache_key} is not an Item: {type(result)}"
                    )
                return result
            # Cache miss
            cls._cache_misses += 1

        # Load from file
        try:
            data = cls._load_json("item", name)
        except FileNotFoundError:
            logger.debug(f"Item '{name}' not found")
            return None

        try:
            item = from_dict(data_class=Item, data=data, config=cls._dacite_config)
        except (DaciteError, ValueError, TypeError) as e:
            logger.error(f"Error deserializing Item '{name}': {e}", exc_info=True)
            return None

        # Cache the result
        cls._update_cache(cache_key, item, "item", name)
        return item

    @classmethod
    def load_all_items(cls) -> dict[str, Item]:
        """
        Load all items and return as Item dataclasses.

        Returns:
            dict[str, Item]: Mapping of item name to Item dataclass objects
        """
        return cls._load_all_generic("item", Item)

    @classmethod
    def get_pokemon_count(cls, subfolder: str = "default") -> int:
        """Get the count of Pokemon in a subfolder.

        Args:
            subfolder (str, optional): Subfolder name. Defaults to "default".

        Returns:
            int: Number of Pokemon JSON files
        """
        dir_path = cls.get_data_dir() / "pokemon" / subfolder
        if not dir_path.exists():
            return 0
        return len(list(dir_path.glob("*.json")))

    @classmethod
    def get_category_path(cls, category: str, subfolder: Optional[str] = None) -> Path:
        """Get the path to a category folder.

        Args:
            category (str): Category name (e.g., 'pokemon', 'move', 'ability', 'item')
            subfolder (Optional[str], optional): Subfolder name. Defaults to None.

        Returns:
            Path: Path to the category folder
        """
        data_dir = cls.get_data_dir()
        if subfolder:
            return data_dir / category / subfolder
        return data_dir / category

    @classmethod
    def _save_data(
        cls,
        name: str,
        data: Pokemon | Move | Ability | Item,
        category: str,
        subfolder: Optional[str] = None,
    ) -> Path:
        """Save data to a JSON file and update cache.

        Args:
            name (str): Name of the data (e.g., 'Pikachu', 'Thunderbolt', etc.)
            data (Pokemon | Move | Ability | Item): The dataclass object to save
            category (str): Category of the data (e.g., 'pokemon', 'move', 'ability', 'item')
            subfolder (Optional[str], optional): Subfolder name. Defaults to None.

        Returns:
            Path: Path to the saved file
        """
        # Normalize the name to ID format
        name = name_to_id(name)

        # Construct file path
        if subfolder:
            file_path = cls.get_data_dir() / category / subfolder / f"{name}.json"
        else:
            file_path = cls.get_data_dir() / category / f"{name}.json"

        # Use file lock to prevent concurrent writes
        with cls._file_lock:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Saving {category} '{name}' to {file_path}")
            temp_path = file_path.with_suffix(".tmp")
            try:
                # Write to temp file first, then atomic rename (safer)
                with open(temp_path, "wb") as f:
                    # Import necessary types for dict factory
                    from src.utils.data.models import (
                        GameStringMap,
                        GameVersionIntMap,
                        GameVersionStringMap,
                        PokemonMoves,
                        SpriteVersions,
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
                                    GameStringMap,
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
                            asdict(cast(Any, data), dict_factory=dict_factory),
                            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
                        )
                    )

                # Atomic rename (or as close as possible on Windows)
                temp_path.replace(file_path)
            except (OSError, IOError) as e:
                logger.error(f"Error saving {category} '{name}': {e}", exc_info=True)
                # Clean up temp file if it exists
                if temp_path.exists():
                    temp_path.unlink()
                raise

        # Update cache with the new data
        if subfolder:
            cache_key = (category, name, subfolder)
        else:
            cache_key = (category, name)
        cls._update_cache(cache_key, data, category, name)

        # If saving a Pokemon with a subfolder, update the subfolder cache
        if category == "pokemon" and subfolder:
            with cls._cache_lock.write_lock():
                cls._subfolder_cache[name] = subfolder

        logger.info(f"Successfully saved {category} '{name}'")
        return file_path

    @classmethod
    def save_pokemon(
        cls, name: str, data: Pokemon, subfolder: Optional[str] = None
    ) -> Path:
        """Save Pokemon data to a JSON file and update cache (thread-safe).

        Args:
            name (str): Pokemon name (e.g., 'Pikachu', 'pikachu', or 'PIKACHU')
            data (Pokemon): Pokemon dataclass object
            subfolder (Optional[str], optional): Subfolder name. Defaults to None.

        Returns:
            Path: Path to the saved file
        """
        # Normalize the name to ID format
        normalized_name = name_to_id(name)

        # Determine the subfolder to use
        if subfolder is None:
            with cls._cache_lock.read_lock():
                subfolder = cls._subfolder_cache.get(normalized_name, "default")
            logger.debug(
                f"Using {'cached' if normalized_name in cls._subfolder_cache else 'default'} "
                f"subfolder '{subfolder}' for saving '{normalized_name}'"
            )

        return cls._save_data(name, data, "pokemon", subfolder)

    @classmethod
    def save_move(cls, name: str, data: Move) -> Path:
        """Save Move data to a JSON file and update cache (thread-safe).

        Args:
            name (str): Move name (e.g., 'Thunderbolt', 'thunderbolt', or 'THUNDERBOLT')
            data (Move): Move dataclass object

        Returns:
            Path: Path to the saved file
        """
        return cls._save_data(name, data, "move")

    @classmethod
    def save_ability(cls, name: str, data: Ability) -> Path:
        """Save Ability data to a JSON file and update cache (thread-safe).

        Args:
            name (str): Ability name (e.g., 'Intimidate', 'intimidate', or 'INTIMIDATE')
            data (Ability): Ability dataclass object

        Returns:
            Path: Path to the saved file
        """
        return cls._save_data(name, data, "ability")

    @classmethod
    def save_item(cls, name: str, data: Item) -> Path:
        """Save Item data to a JSON file and update cache (thread-safe).

        Args:
            name (str): Item name (e.g., 'Potion', 'potion', or 'POTION')
            data (Item): Item dataclass object

        Returns:
            Path: Path to the saved file
        """
        return cls._save_data(name, data, "item")

    @classmethod
    def clear_cache(cls) -> None:
        """Clear all caches (Pokemon, Move, Ability, Item) and reset statistics (thread-safe)."""
        with cls._cache_lock.write_lock():
            # Count entries by type
            pokemon_size = sum(1 for k in cls._cache if k[0] == "pokemon")
            move_size = sum(1 for k in cls._cache if k[0] == "move")
            ability_size = sum(1 for k in cls._cache if k[0] == "ability")
            item_size = sum(1 for k in cls._cache if k[0] == "item")
            total_size = len(cls._cache)
            subfolder_cache_size = len(cls._subfolder_cache)

            cls._cache.clear()
            cls._subfolder_cache.clear()
            cls._cache_hits = 0
            cls._cache_misses = 0

            logger.info(
                f"Cleared unified cache ({total_size} total entries: "
                f"{pokemon_size} Pokemon, {move_size} Moves, "
                f"{ability_size} Abilities, {item_size} Items) and "
                f"subfolder cache ({subfolder_cache_size} entries)"
            )

    @classmethod
    def get_cache_size(cls) -> int:
        """Get the total number of cached items across all caches (thread-safe).

        Returns:
            int: Total number of items currently in all caches
        """
        with cls._cache_lock.read_lock():
            return len(cls._cache)

    @classmethod
    def get_cache_stats(cls) -> dict[str, Any]:
        """Get cache statistics (thread-safe).

        Returns:
            dict[str, Any]: Dictionary containing cache statistics.
        """
        with cls._cache_lock.read_lock():
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

    @classmethod
    def get_cache_hit_rate(cls) -> float:
        """Get the cache hit rate (thread-safe).

        Returns:
            float: Cache hit rate between 0.0 and 1.0
        """
        with cls._cache_lock.read_lock():
            total = cls._cache_hits + cls._cache_misses
            return cls._cache_hits / total if total > 0 else 0.0

    @classmethod
    def set_max_cache_size(cls, size: int) -> None:
        """Set the maximum cache size (thread-safe).

        Args:
            size (int): New maximum cache size (must be > 0)

        Raises:
            ValueError: If size is not positive
        """
        if size <= 0:
            raise ValueError(f"Cache size must be positive, got: {size}")

        with cls._cache_lock.write_lock():
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

    @classmethod
    def _preload_worker(cls, json_file: Path) -> tuple[str, dict]:
        """Load a single JSON file into the cache.

        Args:
            json_file (Path): Path to the JSON file to load.

        Returns:
            tuple[str, dict]: Tuple of (name, parsed JSON data).
        """
        name = json_file.stem
        with open(json_file, "rb") as f:
            data = orjson.loads(f.read())
        return name, data

    @classmethod
    def preload_cache(cls, subfolders: Optional[list[str]] = None) -> dict[str, Any]:
        """Pre-load all Pokemon into cache for maximum performance during a run.

        Args:
            subfolders (Optional[list[str]], optional): List of subfolders to preload. Defaults to None.

        Returns:
            dict[str, Any]: Statistics about the preload operation.
        """
        if subfolders is None:
            subfolders = POKEMON_FORM_SUBFOLDERS

        start_time = time.time()
        cache_size_before = cls.get_cache_size()

        # Early warning if cache size might be too small
        data_dir = cls.get_data_dir()
        estimated_pokemon_count = 0
        for subfolder in subfolders:
            pokemon_dir = data_dir / "pokemon" / subfolder
            if pokemon_dir.exists():
                estimated_pokemon_count += len(list(pokemon_dir.glob("*.json")))

        if estimated_pokemon_count > cls.MAX_CACHE_SIZE:
            logger.warning(
                f"Cache size ({cls.MAX_CACHE_SIZE}) is smaller than estimated Pokemon count "
                f"({estimated_pokemon_count}). Some entries will be evicted during preload. "
                f"Consider increasing cache size with set_max_cache_size({estimated_pokemon_count})."
            )

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
                with cls._cache_lock.write_lock():
                    for key, mon in loaded_pokemon.items():
                        cls._cache[key] = mon
                        cls._cache.move_to_end(key)

                    overage = len(cls._cache) - cls.MAX_CACHE_SIZE
                    if overage > 0:
                        for _ in range(overage):
                            cls._cache.popitem(last=False)

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

    @classmethod
    def iterate_pokemon(
        cls,
        subfolders: Optional[list[str]] = None,
        include_non_default: bool = False,
        deduplicate: bool = True,
    ) -> Generator[Pokemon, None, None]:
        """Iterate over Pokemon from specified subfolders with optional deduplication.

        Args:
            subfolders (Optional[list[str]], optional): List of subfolders to preload. Defaults to None.
            include_non_default (bool, optional): If True, includes non-default forms. Defaults to False.
            deduplicate (bool, optional): If True, ensures each Pokemon is unique. Defaults to True.

        Yields:
            Generator[Pokemon, None, None]: Yields each unique Pokemon from the specified subfolders.
        """
        if subfolders is None:
            subfolders = POKEMON_FORM_SUBFOLDERS

        seen_pokemon: set[tuple[str, Optional[int]]] = set()
        pokemon_base_dir = cls.get_data_dir() / "pokemon"

        for subfolder in subfolders:
            pokemon_dir = pokemon_base_dir / subfolder
            if not pokemon_dir.exists():
                logger.debug(f"Subfolder not found, skipping: {subfolder}")
                continue

            pokemon_files = sorted(pokemon_dir.glob("*.json"))

            for pokemon_file in pokemon_files:
                try:
                    pokemon = cls.load_pokemon(pokemon_file.stem, subfolder=subfolder)

                    if not pokemon:
                        continue

                    # Filter for default forms unless include_non_default is True
                    if not include_non_default and not pokemon.is_default:
                        continue

                    # Deduplicate if requested
                    if deduplicate:
                        # Create unique key to prevent duplicates
                        pokemon_key = (
                            pokemon.name,
                            pokemon.pokedex_numbers.get("national"),
                        )

                        if pokemon_key in seen_pokemon:
                            continue

                        seen_pokemon.add(pokemon_key)

                    yield pokemon

                except Exception as e:
                    logger.warning(f"Error loading Pokemon {pokemon_file.stem}: {e}")
                    continue
