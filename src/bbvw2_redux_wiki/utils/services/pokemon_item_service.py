"""
Service for updating Pokemon held item data.
"""

import re

from bbvw2_redux_wiki.utils.core.config import VERSION_GROUP
from bbvw2_redux_wiki.utils.core.loader import PokeDBLoader
from bbvw2_redux_wiki.utils.core.logger import get_logger
from bbvw2_redux_wiki.utils.services.base_service import BaseService
from bbvw2_redux_wiki.utils.text.text_util import name_to_id, parse_pokemon_forme

logger = get_logger(__name__)


class PokemonItemService(BaseService):
    """Service for updating Pokemon held item data."""

    @staticmethod
    def update_held_item(
        pokemon: str, item_name: str, rarity: int, forme: str = "", attribute: str = ""
    ) -> bool:
        """Update held item for a Pokemon.

        Args:
            pokemon (str): The name of the Pokemon to update.
            item_name (str): The name of the held item.
            rarity (int): The percentage chance (0-100) of the item being held.
            forme (str, optional): The forme of the Pokemon (e.g., "attack", "defense"). Defaults to "".
            attribute (str, optional): The attribute name (e.g., "Held Item (Plant Forme)"). If present, forme is extracted from it.

        Returns:
            bool: True if the held item was updated successfully, False otherwise.
        """
        # Extract forme from attribute name if present
        # Pattern: "Held Item (Plant Forme)" -> forme="plant"
        forme_from_attr = ""
        if attribute and " Forme)" in attribute:
            # Match pattern: "(Something Forme)" or "(Complete / Something Forme)"
            forme_match = re.search(r"(?:/\s*)?([A-Za-z\s]+)\s+Forme\)", attribute)
            if forme_match:
                forme_name = forme_match.group(1).strip()
                # Parse the forme name to handle complex cases
                _, forme_from_attr = parse_pokemon_forme(f"{pokemon} {forme_name}")

        # Use forme from attribute if present, otherwise use the passed forme parameter
        if forme_from_attr:
            forme = forme_from_attr

        # Normalize pokemon name and append forme if present
        pokemon_id = name_to_id(pokemon)
        if forme:
            pokemon_id = f"{pokemon_id}-{forme}"

        # Normalize item name
        item_id = name_to_id(item_name)

        try:
            # Load the Pokemon using PokeDBLoader
            pokemon_data = PokeDBLoader.load_pokemon(pokemon_id)
            if pokemon_data is None:
                forme_str = f" ({forme} forme)" if forme else ""
                logger.warning(
                    f"Pokemon '{pokemon}'{forme_str} not found in parsed data (ID: {pokemon_id})"
                )
                return False

            # Validate item exists in database
            item_data = PokeDBLoader.load_item(item_id)
            if not item_data:
                logger.warning(
                    f"Item '{item_name}' (ID: {item_id}) not found in database. Skipping validation but saving anyway."
                )

            # Capture old held items for change tracking
            old_held_items = list(pokemon_data.held_items.keys())

            # Update held_items
            # Structure: {item_name: {version_group: rarity}}
            if item_id not in pokemon_data.held_items:
                pokemon_data.held_items[item_id] = {}

            pokemon_data.held_items[item_id][VERSION_GROUP] = rarity

            # Record change
            new_held_items = list(pokemon_data.held_items.keys())
            if item_id not in old_held_items:
                # New item added
                BaseService.record_change(
                    pokemon_data,
                    field="Held Items",
                    old_value=", ".join(old_held_items) if old_held_items else "None",
                    new_value=", ".join(new_held_items),
                    source="pokemon_item_service",
                )

            # Save using PokeDBLoader
            PokeDBLoader.save_pokemon(pokemon_id, pokemon_data)
            logger.info(
                f"Updated held item for '{pokemon_id}': {item_id} at {rarity}% rate"
            )
            return True

        except (OSError, IOError, ValueError) as e:
            logger.warning(f"Error updating held item for '{pokemon}': {e}")
            return False
