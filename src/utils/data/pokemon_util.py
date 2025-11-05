"""
Utility functions for Pokemon data processing and iteration.

This module provides common Pokemon-related utilities that are used across
multiple generators, including iterating over Pokemon forms with deduplication.
"""

from pathlib import Path
from typing import Generator, List, Optional, Set, Tuple

from src.data.pokedb_loader import PokeDBLoader
from src.models.pokedb import Pokemon
from src.utils.data.constants import POKEMON_FORM_SUBFOLDERS_STANDARD
from src.utils.core.config import POKEDB_SPRITE_VERSION
from src.utils.core.logger import get_logger

logger = get_logger(__name__)


def get_pokemon_sprite_url(
    pokemon: Pokemon,
    prefer_animated: bool = True,
    sprite_type: str = "front_default",
) -> Optional[str]:
    """
    Get the appropriate sprite URL for a Pokemon.

    This function consolidates the sprite selection logic used throughout the codebase.
    It handles:
    - Cosmetic forms (which don't have animated GIFs)
    - Animated sprite preference for default/variant/transformation forms
    - Fallback to PNG sprites when animated not available
    - Support for different sprite types (front/back, default/shiny, male/female)

    Args:
        pokemon: Pokemon object containing sprite data
        prefer_animated: If True, prefer animated GIF over PNG for non-cosmetic forms
        sprite_type: Type of sprite to retrieve. Options:
                    - 'front_default', 'back_default'
                    - 'front_shiny', 'back_shiny'
                    - 'front_female', 'back_female'
                    - 'front_shiny_female', 'back_shiny_female'

    Returns:
        Sprite URL if found, None otherwise

    Example:
        >>> from src.data.pokedb_loader import PokeDBLoader
        >>> pokemon = PokeDBLoader.load_pokemon("pikachu")
        >>> sprite_url = get_pokemon_sprite_url(pokemon)
        >>> # Returns animated GIF URL for Pikachu
        >>> sprite_url = get_pokemon_sprite_url(pokemon, prefer_animated=False)
        >>> # Returns PNG URL for Pikachu
    """
    if not pokemon or not pokemon.sprites:
        return None

    # Check if this is a cosmetic form (cosmetic forms don't have animated GIFs)
    is_cosmetic = any(form.category == "cosmetic" for form in pokemon.forms)

    sprite_url = None

    # For cosmetic forms, use PNG sprites only
    if is_cosmetic:
        sprite_url = getattr(pokemon.sprites, sprite_type, None)
        return sprite_url

    # For non-cosmetic forms, prefer animated GIF if requested
    if (
        prefer_animated
        and hasattr(pokemon.sprites, "versions")
        and pokemon.sprites.versions
    ):
        sprite_version = getattr(pokemon.sprites.versions, POKEDB_SPRITE_VERSION, None)
        if sprite_version and sprite_version.animated:
            sprite_url = getattr(sprite_version.animated, sprite_type, None)

    # Fall back to PNG sprite if animated not available or not preferred
    if not sprite_url:
        sprite_url = getattr(pokemon.sprites, sprite_type, None)

    return sprite_url


def iterate_pokemon(
    pokemon_base_dir: Path,
    subfolders: Optional[List[str]] = None,
    include_non_default: bool = False,
    deduplicate: bool = True,
) -> Generator[Pokemon, None, None]:
    """
    Iterate over Pokemon from specified subfolders with optional deduplication.

    This function consolidates the Pokemon iteration logic previously duplicated
    across move_generator, item_generator, and ability_generator. It handles:
    - Loading Pokemon from multiple form subfolders
    - Filtering for is_default Pokemon (unless include_non_default=True)
    - Deduplicating Pokemon by (name, national_dex) key
    - Error handling for failed Pokemon loads

    Args:
        pokemon_base_dir: Base directory containing Pokemon form subfolders
        subfolders: List of subfolder names to scan (e.g., ["default", "transformation", "variant"])
                   If None, uses POKEMON_FORM_SUBFOLDERS_STANDARD from constants
        include_non_default: If True, includes non-default forms (alternate forms, regional variants)
        deduplicate: If True, ensures each Pokemon (by name + national dex) is yielded only once

    Yields:
        Pokemon objects loaded from the specified subfolders

    Example:
        >>> pokemon_dir = Path("data/pokedb/parsed/pokemon")
        >>> for pokemon in iterate_pokemon(pokemon_dir):
        ...     print(f"Processing {pokemon.name}")
        ...     # Do something with the pokemon

        >>> # Include all forms including cosmetic
        >>> for pokemon in iterate_pokemon(pokemon_dir, subfolders=["default", "transformation", "variant", "cosmetic"]):
        ...     print(pokemon.name)
    """
    if subfolders is None:
        subfolders = POKEMON_FORM_SUBFOLDERS_STANDARD

    seen_pokemon: Set[Tuple[str, Optional[int]]] = set()

    for subfolder in subfolders:
        pokemon_dir = pokemon_base_dir / subfolder
        if not pokemon_dir.exists():
            logger.debug(f"Subfolder not found, skipping: {subfolder}")
            continue

        pokemon_files = sorted(pokemon_dir.glob("*.json"))

        for pokemon_file in pokemon_files:
            try:
                pokemon = PokeDBLoader.load_pokemon(
                    pokemon_file.stem, subfolder=subfolder
                )

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
