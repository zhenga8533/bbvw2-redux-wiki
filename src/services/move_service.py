"""
Service for copying new moves from gen8 to parsed data folder.
"""

import json
from collections import Counter
from typing import Any

from src.data.pokedb_loader import PokeDBLoader
from src.utils.logger_util import get_logger
from src.utils.text_util import name_to_id

logger = get_logger(__name__)


class MoveService:
    """Service for copying moves from gen8 to parsed folder."""

    @staticmethod
    def _get_most_common_value(version_dict: dict[str, Any]) -> Any:
        """
        Get the most common value from a version group dictionary.

        If there's a tie, returns the first value in insertion order.

        Args:
            version_dict: Dictionary with version group keys and their values

        Returns:
            The most common value, or None if dict is empty or all values are None
        """
        if not version_dict:
            return None

        # Filter out None values
        non_none_values = [v for v in version_dict.values() if v is not None]

        if not non_none_values:
            return None

        # Count occurrences
        counter = Counter(non_none_values)

        # Get most common - returns list of (value, count) tuples
        # In case of tie, Counter.most_common() returns them in first-seen order
        most_common = counter.most_common(1)

        return most_common[0][0] if most_common else None

    @staticmethod
    def _add_gen5_version_fields(data: dict[str, Any], field_name: str) -> None:
        """
        Add black_white and black_2_white_2 fields to a version group dictionary.

        Uses the most common value from existing version groups.
        Modifies the data dict in place.

        Args:
            data: The move data dictionary
            field_name: Name of the field to process (e.g., "accuracy", "type")
        """
        if field_name not in data:
            return

        field_value = data[field_name]

        # Only process if it's a dict (version group mapping)
        if not isinstance(field_value, dict):
            return

        # Get most common value
        most_common = MoveService._get_most_common_value(field_value)

        # Add black_white field if missing
        if "black_white" not in field_value:
            field_value["black_white"] = most_common
            logger.debug(f"Added black_white to {field_name}: {most_common}")

        # Add black_2_white_2 field if missing
        if "black_2_white_2" not in field_value:
            field_value["black_2_white_2"] = most_common
            logger.debug(f"Added black_2_white_2 to {field_name}: {most_common}")

    @staticmethod
    def _process_gen8_move_data(data: dict[str, Any]) -> dict[str, Any]:
        """
        Process gen8 move data by adding black_white and black_2_white_2 fields.

        Args:
            data: Raw gen8 move JSON data

        Returns:
            Modified move data with Gen 5 version fields added
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
            MoveService._add_gen5_version_fields(data, field)

        return data

    @staticmethod
    def copy_new_move(move_name: str) -> bool:
        """
        Copy a new move from gen8 to parsed data folder.

        Processes gen8 move data to add black_white and black_2_white_2 fields
        with the most common value across all existing version groups.

        Does NOT delete old moves or overwrite existing moves.

        Args:
            move_name: Name of the move to copy

        Returns:
            bool: True if copied, False if skipped or error
        """
        # Normalize move name
        move_id = name_to_id(move_name)

        # Get directory paths
        data_dir = PokeDBLoader.get_data_dir()
        gen8_move_dir = data_dir.parent / "gen8" / "move"
        parsed_move_dir = data_dir / "move"

        # Construct file paths
        source_path = gen8_move_dir / f"{move_id}.json"
        dest_path = parsed_move_dir / f"{move_id}.json"

        # Check if source exists
        if not source_path.exists():
            logger.warning(f"Move '{move_name}' not found in gen8: {source_path}")
            return False

        # Skip if destination already exists
        if dest_path.exists():
            logger.debug(f"Move '{move_name}' already exists in parsed data, skipping")
            return False

        # Create destination directory if needed
        parsed_move_dir.mkdir(parents=True, exist_ok=True)

        # Load, process, and save the move data
        try:
            # Load gen8 move data
            with open(source_path, "r", encoding="utf-8") as f:
                move_data = json.load(f)

            # Process to add black_2_white_2 fields
            processed_data = MoveService._process_gen8_move_data(move_data)

            # Save to parsed folder
            with open(dest_path, "w", encoding="utf-8") as f:
                json.dump(processed_data, f, indent=4, ensure_ascii=False)

            logger.info(f"Copied and processed move '{move_name}' from gen8 to parsed")
            return True
        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.error(f"Error copying move '{move_name}': {e}")
            return False
