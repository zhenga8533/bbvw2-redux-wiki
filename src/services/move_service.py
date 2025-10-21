"""
Service for copying new moves from gen8 to parsed data folder.
"""

import shutil

from src.data.pokedb_loader import PokeDBLoader
from src.utils.logger_util import get_logger
from src.utils.text_util import name_to_id

logger = get_logger(__name__)


class MoveService:
    """Service for copying moves from gen8 to parsed folder."""

    @staticmethod
    def copy_new_move(move_name: str) -> bool:
        """
        Copy a new move from gen8 to parsed data folder.

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

        # Copy the file
        try:
            shutil.copy2(source_path, dest_path)
            logger.info(f"Copied move '{move_name}' from gen8 to parsed")
            return True
        except (OSError, IOError) as e:
            logger.error(f"Error copying move '{move_name}': {e}")
            return False
