"""
Service for copying new moves from newer generation to parsed data folder.
"""

from typing import Any

import orjson

from src.utils.core.config import POKEDB_GENERATIONS, POKEDB_VERSION_GROUPS
from src.utils.core.loader import PokeDBLoader
from src.utils.core.logger import get_logger
from src.utils.text.dict_util import get_most_common_value
from src.utils.text.text_util import name_to_id

logger = get_logger(__name__)


class MoveService:
    """Service for copying moves from newer generation to parsed folder."""

    @staticmethod
    def _normalize_version_group_fields(data: dict[str, Any], field_name: str) -> None:
        """Normalize version group fields to only include configured version groups.

        Args:
            data (dict[str, Any]): The move data dictionary.
            field_name (str): The name of the field to process (e.g., "accuracy", "type").
        """
        if field_name not in data:
            return

        field_value = data[field_name]

        # Only process if it's a dict (version group mapping)
        if not isinstance(field_value, dict):
            return

        # Get most common value from existing version groups
        most_common = get_most_common_value(field_value)

        # Create new dict with only configured version groups
        normalized_value = {}
        for version_group in POKEDB_VERSION_GROUPS:
            # Use existing value if present, otherwise use most common
            normalized_value[version_group] = field_value.get(
                version_group, most_common
            )
            if version_group not in field_value:
                logger.debug(f"Added {version_group} to {field_name}: {most_common}")

        # Replace the field value with normalized version
        data[field_name] = normalized_value

    @staticmethod
    def _process_move_data(data: dict[str, Any]) -> dict[str, Any]:
        """Process move data by normalizing version group fields to match config.

        Args:
            data (dict[str, Any]): The move data dictionary.

        Returns:
            dict[str, Any]: The modified move data with normalized version group fields.
        """
        # Fields that use GameVersionIntMap or GameVersionStringMap
        version_fields = [
            "accuracy",
            "power",
            "pp",
            "type",
            "effect_chance",
            "effect",
            "short_effect",
            "flavor_text",
        ]

        for field in version_fields:
            MoveService._normalize_version_group_fields(data, field)

        return data

    @staticmethod
    def copy_new_move(move_name: str) -> bool:
        """Copy a new move from newer generation to parsed data folder.

        Args:
            move_name (str): Name of the move to copy

        Returns:
            bool: True if copied, False if skipped or error
        """
        # Normalize move name
        move_id = name_to_id(move_name)

        # Use PokeDBLoader to get paths
        data_dir = PokeDBLoader.get_data_dir()
        source_gen = POKEDB_GENERATIONS[-1]  # Use the latest generation as source
        source_move_dir = data_dir.parent / source_gen / "move"
        parsed_move_dir = PokeDBLoader.get_category_path("move")

        # Construct file paths
        source_path = source_move_dir / f"{move_id}.json"
        dest_path = parsed_move_dir / f"{move_id}.json"

        # Check if source exists
        if not source_path.exists():
            logger.warning(
                f"Move '{move_name}' not found in {source_gen}: {source_path}"
            )
            return False

        # Skip if destination already exists
        if dest_path.exists():
            logger.debug(f"Move '{move_name}' already exists in parsed data, skipping")
            return False

        # Create destination directory if needed
        parsed_move_dir.mkdir(parents=True, exist_ok=True)

        # Load, process, and save the move data
        try:
            # Load move data using orjson (2-3x faster than json)
            with open(source_path, "rb") as f:
                move_data = orjson.loads(f.read())

            # Process to add configured version group fields
            processed_data = MoveService._process_move_data(move_data)

            # Save to parsed folder using orjson
            with open(dest_path, "wb") as f:
                f.write(
                    orjson.dumps(
                        processed_data,
                        option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
                    )
                )

            logger.info(
                f"Copied and processed move '{move_name}' from {source_gen} to parsed"
            )
            return True
        except (OSError, IOError, ValueError) as e:
            logger.warning(f"Error copying move '{move_name}': {e}")
            return False

    @staticmethod
    def update_move_type(move_name: str, new_type: str) -> bool:
        """Update the type of an existing move in the parsed data folder.

        Args:
            move_name (str): Name of the move to modify
            new_type (str): New type to set for the move

        Returns:
            bool: True if modified, False if error
        """
        # Normalize move name
        move_id = name_to_id(move_name)
        type_id = name_to_id(new_type)

        try:
            # Load the move using PokeDBLoader
            move = PokeDBLoader.load_move(move_id)
            if move is None:
                return False

            # Update type for all version groups
            for version_key in move.type.__slots__:
                setattr(move.type, version_key, type_id)

            # Save using PokeDBLoader
            PokeDBLoader.save_move(move_id, move)
            logger.info(f"Changed type of move '{move_name}' to '{type_id}'")
            return True
        except (OSError, IOError, ValueError) as e:
            logger.warning(f"Error changing type of move '{move_name}': {e}")
            return False

    @staticmethod
    def update_move_attribute(move_name: str, attribute: str, new_value: str) -> bool:
        """Update an attribute of an existing move in the parsed data folder.

        Args:
            move_name (str): Name of the move to modify
            attribute (str): Attribute to update (e.g., "power", "pp", "priority", "accuracy", "type")
            new_value (str): New value to set for the attribute

        Returns:
            bool: True if modified, False if error
        """
        # Normalize move name and attribute
        move_id = name_to_id(move_name)
        attribute = attribute.lower().strip()

        # Map attribute names to field names
        attribute_map = {
            "power": "power",
            "pp": "pp",
            "priority": "priority",
            "accuracy": "accuracy",
            "type": "type",
        }

        if attribute not in attribute_map:
            logger.warning(
                f"Unsupported attribute '{attribute}' for move '{move_name}'"
            )
            return False

        field_name = attribute_map[attribute]

        try:
            # Load the move using PokeDBLoader
            move = PokeDBLoader.load_move(move_id)
            if move is None:
                logger.warning(f"Move '{move_name}' not found in parsed data")
                return False

            # Get the field object
            if not hasattr(move, field_name):
                logger.warning(f"Move object has no field '{field_name}'")
                return False

            field_obj = getattr(move, field_name)

            # Process the new value based on attribute type
            if attribute == "type":
                processed_value = name_to_id(new_value)
            elif attribute in ["power", "pp", "accuracy"]:
                if "Never" in new_value:
                    processed_value = None
                else:
                    cleaned_value = "".join(filter(str.isdigit, new_value))
                    processed_value = int(cleaned_value)
            elif attribute == "priority":
                processed_value = int(new_value)
            else:
                processed_value = new_value

            # Update the attribute
            # Check if it's a version group object or a plain value
            if hasattr(field_obj, "__slots__"):
                # Version group object - update all version groups
                for version_key in field_obj.__slots__:
                    setattr(field_obj, version_key, processed_value)
            else:
                # Plain value - set directly on the move object
                setattr(move, field_name, processed_value)

            # Save using PokeDBLoader
            PokeDBLoader.save_move(move_id, move)
            logger.info(
                f"Updated {attribute} of move '{move_name}' to '{processed_value}'"
            )
            return True
        except (OSError, IOError, ValueError) as e:
            logger.warning(f"Error updating {attribute} of move '{move_name}': {e}")
            return False
