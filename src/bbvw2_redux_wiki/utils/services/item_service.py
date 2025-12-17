"""
Service for updating item data.

This service handles:
1. Updating item costs
2. Updating TM moves
3. Copying new items from newer generations
"""

import orjson
from bbvw2_redux_wiki.utils.core.config import (
    POKEDB_GENERATIONS,
    POKEDB_VERSION_GROUPS,
)
from bbvw2_redux_wiki.utils.core.loader import PokeDBLoader
from bbvw2_redux_wiki.utils.core.logger import get_logger
from bbvw2_redux_wiki.utils.services.move_service import MoveService
from bbvw2_redux_wiki.utils.text.text_util import name_to_id

logger = get_logger(__name__)


class ItemService:
    """Service for updating item data."""

    @staticmethod
    def update_item_cost(item_name: str, new_cost: int) -> bool:
        """Update the cost of an item.

        Args:
            item_name (str): The name of the item (e.g., "Potion", "Full Restore")
            new_cost (int): The new cost value

        Returns:
            bool: True if the update was successful, False otherwise
        """
        item_id = name_to_id(item_name)

        # Load the item
        item = PokeDBLoader.load_item(item_id)
        if not item:
            logger.warning(f"Item '{item_name}' (id: {item_id}) not found")
            return False

        old_cost = item.cost
        item.cost = new_cost

        # Save the updated item
        PokeDBLoader.save_item(item_id, item)
        logger.info(f"Updated {item_name} cost: ${old_cost} -> ${new_cost}")

        return True

    @staticmethod
    def copy_new_item(item_name: str) -> bool:
        """Copy a new item from newer generation to parsed data folder.

        Args:
            item_name (str): Name of the item to copy

        Returns:
            bool: True if copied, False if skipped or error
        """
        # Normalize item name
        item_id = name_to_id(item_name)

        # Use PokeDBLoader to get paths
        data_dir = PokeDBLoader.get_data_dir()
        source_gen = POKEDB_GENERATIONS[-1]  # Use the latest generation as source
        source_item_dir = data_dir.parent / source_gen / "item"
        parsed_item_dir = PokeDBLoader.get_category_path("item")

        # Construct file paths
        source_path = source_item_dir / f"{item_id}.json"
        dest_path = parsed_item_dir / f"{item_id}.json"

        # Check if source exists
        if not source_path.exists():
            logger.warning(
                f"Item '{item_name}' not found in {source_gen}: {source_path}"
            )
            return False

        # Skip if destination already exists
        if dest_path.exists():
            logger.debug(f"Item '{item_name}' already exists in parsed data, skipping")
            return True  # Return True since item exists

        # Create destination directory if needed
        parsed_item_dir.mkdir(parents=True, exist_ok=True)

        # Load and save the item data
        try:
            # Load item data using orjson
            with open(source_path, "rb") as f:
                item_data = orjson.loads(f.read())

            # Save to parsed folder using orjson
            with open(dest_path, "wb") as f:
                f.write(
                    orjson.dumps(
                        item_data,
                        option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
                    )
                )

            logger.info(f"Copied item '{item_name}' from {source_gen} to parsed")
            return True
        except (OSError, IOError, ValueError) as e:
            logger.warning(f"Error copying item '{item_name}': {e}")
            return False

    @staticmethod
    def update_tm_move(tm_name: str, new_move_name: str) -> bool:
        """Update the move taught by a TM.

        This updates the TM's effect, short_effect, and flavor_text fields to reflect the new move.
        If the move doesn't exist in parsed data, it will be copied from a newer generation.

        Args:
            tm_name (str): The name of the TM (e.g., "TM01", "TM50")
            new_move_name (str): The name of the new move (e.g., "Dragon Claw")

        Returns:
            bool: True if the update was successful, False otherwise
        """
        tm_id = name_to_id(tm_name)
        move_id = name_to_id(new_move_name)

        # Load the TM item
        tm_item = PokeDBLoader.load_item(tm_id)
        if not tm_item:
            logger.warning(f"TM '{tm_name}' (id: {tm_id}) not found")
            return False

        # Try to load the new move, copy if it doesn't exist
        move = PokeDBLoader.load_move(move_id)
        if not move:
            logger.info(
                f"Move '{new_move_name}' not found in parsed data, attempting to copy from newer generation"
            )
            if not MoveService.copy_new_move(new_move_name):
                logger.error(f"Failed to copy move '{new_move_name}'")
                return False

            # Try loading again after copying
            move = PokeDBLoader.load_move(move_id)
            if not move:
                logger.error(
                    f"Move '{new_move_name}' still not found after copy attempt"
                )
                return False

        # Get the properly formatted move name from the move data
        proper_move_name = move.name.replace("-", " ").title()

        # Update the effect and short_effect to reference the new move
        tm_item.effect = f"Teaches {proper_move_name} to a compatible Pokémon."
        tm_item.short_effect = f"Teaches {proper_move_name} to a compatible Pokémon."

        # Update flavor_text for all version groups from the move's flavor text
        # Both move and TM flavor_text are GameVersionStringMap objects
        if hasattr(move.flavor_text, "keys"):
            # It's a version group object
            for version_group in POKEDB_VERSION_GROUPS:
                move_flavor = getattr(move.flavor_text, version_group, None)
                if move_flavor:
                    setattr(tm_item.flavor_text, version_group, move_flavor)
                else:
                    logger.debug(
                        f"No flavor text for {move_id} in version group {version_group}"
                    )

        # Save the updated TM
        PokeDBLoader.save_item(tm_id, tm_item)
        logger.info(f"Updated {tm_name} to teach {proper_move_name}")

        return True
