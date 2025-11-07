"""
Service for updating Pokemon move-related data (level-up moves, TMs/HMs).
"""

from src.utils.core.config import VERSION_GROUP
from src.utils.core.loader import PokeDBLoader
from src.utils.core.logger import get_logger
from src.utils.data.models import MoveLearn
from src.utils.text.text_util import name_to_id

logger = get_logger(__name__)


class PokemonMoveService:
    """Service for updating Pokemon move-related data."""

    @staticmethod
    def update_levelup_moves(
        pokemon: str, moves: list[tuple[int, str]], forme: str = ""
    ) -> bool:
        """Update level-up moves for a Pokemon.

        Args:
            pokemon (str): The name of the Pokemon to update.
            moves (list[tuple[int, str]]): A list of tuples containing level and move name.
            forme (str, optional): The forme of the Pokemon (e.g., "attack", "defense"). Defaults to "".

        Returns:
            bool: True if the level-up moves were updated successfully, False otherwise.
        """
        # Normalize pokemon name and append forme if present
        pokemon_id = name_to_id(pokemon)
        if forme:
            pokemon_id = f"{pokemon_id}-{forme}"

        try:
            # Load the Pokemon using PokeDBLoader
            pokemon_data = PokeDBLoader.load_pokemon(pokemon_id)
            if pokemon_data is None:
                forme_str = f" ({forme} forme)" if forme else ""
                logger.warning(
                    f"Pokemon '{pokemon}'{forme_str} not found in parsed data (ID: {pokemon_id})"
                )
                return False

            # Build new level_up moves list as MoveLearn objects
            new_levelup_moves = []
            for level, move_name in moves:
                move_id = name_to_id(move_name)

                # Validate move exists in database
                move_data = PokeDBLoader.load_move(move_id)
                if not move_data:
                    logger.warning(
                        f"Move '{move_name}' (ID: {move_id}) not found in database. Skipping validation but saving anyway."
                    )

                new_move = MoveLearn(
                    name=move_id,
                    level_learned_at=level,
                    version_groups=[VERSION_GROUP],
                )
                new_levelup_moves.append(new_move)

            # Replace level_up moves
            pokemon_data.moves.level_up = new_levelup_moves

            # Save using PokeDBLoader
            PokeDBLoader.save_pokemon(pokemon_id, pokemon_data)
            logger.info(
                f"Updated level-up moves for '{pokemon_id}': {len(new_levelup_moves)} moves"
            )
            return True

        except (OSError, IOError, ValueError) as e:
            logger.warning(f"Error updating level-up moves for '{pokemon}': {e}")
            return False

    @staticmethod
    def update_machine_moves(
        pokemon: str, moves: list[tuple[str, str, str]], forme: str = ""
    ) -> bool:
        """Update TM/HM compatibility for a Pokemon.

        Args:
            pokemon (str): The name of the Pokemon to update.
            moves (list[tuple[str, str, str]]): A list of tuples containing machine type, number, and move name.
            forme (str, optional): The forme of the Pokemon (e.g., "attack", "defense"). Defaults to "".

        Returns:
            bool: True if the machine moves were updated successfully, False otherwise.
        """
        # Normalize pokemon name and append forme if present
        pokemon_id = name_to_id(pokemon)
        if forme:
            pokemon_id = f"{pokemon_id}-{forme}"

        try:
            # Load the Pokemon using PokeDBLoader
            pokemon_data = PokeDBLoader.load_pokemon(pokemon_id)
            if pokemon_data is None:
                forme_str = f" ({forme} forme)" if forme else ""
                logger.warning(
                    f"Pokemon '{pokemon}'{forme_str} not found in parsed data (ID: {pokemon_id})"
                )
                return False

            # Add new machine moves
            # Note: pokemon_data.moves.machine is a list of MoveLearn objects
            for machine_type, number, move_name in moves:
                move_id = name_to_id(move_name)

                # Validate move exists in database
                move_data = PokeDBLoader.load_move(move_id)
                if not move_data:
                    logger.warning(
                        f"Move '{move_name}' (ID: {move_id}) not found in database. Skipping validation but saving anyway."
                    )

                # Check if move already exists in machine moves
                existing_move = None
                for m in pokemon_data.moves.machine:
                    if m.name == move_id:
                        existing_move = m
                        break

                if existing_move:
                    # Update version groups if needed
                    if VERSION_GROUP not in existing_move.version_groups:
                        existing_move.version_groups.append(VERSION_GROUP)
                else:
                    # Add new machine move as a MoveLearn object
                    new_move = MoveLearn(
                        name=move_id,
                        level_learned_at=0,
                        version_groups=[VERSION_GROUP],
                    )
                    pokemon_data.moves.machine.append(new_move)

            # Save using PokeDBLoader
            PokeDBLoader.save_pokemon(pokemon_id, pokemon_data)
            logger.info(
                f"Updated machine moves for '{pokemon_id}': added {len(moves)} TM/HM moves"
            )
            return True

        except (OSError, IOError, ValueError) as e:
            logger.warning(f"Error updating machine moves for '{pokemon}': {e}")
            return False
