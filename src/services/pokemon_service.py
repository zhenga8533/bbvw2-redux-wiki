"""
Service for updating Pokemon attributes in parsed data folder.
"""

import json
import re
from collections import Counter
from typing import Any

from src.data.pokedb_loader import PokeDBLoader
from src.models.pokedb import MoveLearn
from src.utils.logger_util import get_logger
from src.utils.text_util import name_to_id

logger = get_logger(__name__)


class PokemonService:

    @staticmethod
    def update_attribute(
        pokemon: str, attribute: str, value: str, forme: str = ""
    ) -> bool:
        """
        Update an attribute of an existing Pokemon in the parsed data folder.

        Supported attributes:
        - Base Stats: HP, Attack, Defense, Sp.Atk, Sp.Def, Speed
        - Type: Single or dual typing
        - Ability: Regular abilities and hidden ability
        - EVs: Effort Value yields
        - Base Happiness: Initial friendship/happiness value
        - Base Experience: Experience gained when defeated
        - Catch Rate: Capture probability
        - Gender Ratio: Male/Female distribution

        Version handling:
        - "(Complete / Classic)": Applied (same for both versions)
        - "(Complete)": Applied (Complete version only)
        - "(Classic)": Skipped (Classic-only changes are ignored)

        Forme handling:
        - If forme is provided, appends "-{forme}" to pokemon_id
        - Example: pokemon="Deoxys", forme="attack" -> "deoxys-attack"

        Args:
            pokemon: Name of the Pokemon to modify
            attribute: Attribute to modify (e.g., "Base Stats (Complete)", "Ability (Complete / Attack Forme)")
            value: New value to set for the attribute
            forme: Optional forme name (e.g., "attack", "defense", "plant")

        Returns:
            bool: True if modified, False if error or skipped
        """
        # Normalize pokemon name and append forme if present
        pokemon_id = name_to_id(pokemon)
        if forme:
            pokemon_id = f"{pokemon_id}-{forme}"

        # Determine if we should process this attribute
        # Patterns:
        #   - "(Complete / Classic)": Same for both versions, process it
        #   - "(Complete)": Complete only, process it
        #   - "(Classic)": Classic only, skip it
        if "Complete" in attribute:
            # Complete version only, process it
            pass
        elif "Classic" in attribute:
            # Classic only, skip it
            logger.debug(
                f"Skipping Classic-only attribute '{attribute}' for '{pokemon}'"
            )
            return False

        # Extract the base attribute name (remove version markers)
        attribute_base = attribute.split(" (")[0].strip()

        try:
            # Load the Pokemon using PokeDBLoader
            pokemon_data = PokeDBLoader.load_pokemon(pokemon_id)
            if pokemon_data is None:
                forme_str = f" ({forme} forme)" if forme else ""
                logger.warning(
                    f"Pokemon '{pokemon}'{forme_str} not found in parsed data (ID: {pokemon_id})"
                )
                return False

            # Route to appropriate handler based on attribute
            if attribute_base == "Base Stats":
                return PokemonService._update_base_stats(
                    pokemon_id, pokemon_data, value
                )
            elif attribute_base == "Type":
                return PokemonService._update_type(pokemon_id, pokemon_data, value)
            elif attribute_base == "Ability":
                return PokemonService._update_ability(pokemon_id, pokemon_data, value)
            elif attribute_base == "EVs":
                return PokemonService._update_evs(pokemon_id, pokemon_data, value)
            elif attribute_base == "Base Happiness":
                return PokemonService._update_base_happiness(
                    pokemon_id, pokemon_data, value
                )
            elif attribute_base == "Base Experience":
                return PokemonService._update_base_experience(
                    pokemon_id, pokemon_data, value
                )
            elif attribute_base == "Catch Rate":
                return PokemonService._update_catch_rate(
                    pokemon_id, pokemon_data, value
                )
            elif attribute_base == "Gender Ratio":
                return PokemonService._update_gender_ratio(
                    pokemon_id, pokemon_data, value
                )
            else:
                logger.debug(
                    f"Attribute '{attribute_base}' not yet implemented for '{pokemon}'"
                )
                return False

        except (OSError, IOError, ValueError) as e:
            logger.error(f"Error updating {attribute_base} of Pokemon '{pokemon}': {e}")
            return False

    @staticmethod
    def _update_base_stats(pokemon_id: str, pokemon_data: Any, value: str) -> bool:
        """
        Update base stats for a Pokemon.

        Args:
            pokemon_id: Pokemon ID
            pokemon_data: Pokemon dataclass object
            value: Base stats string (e.g., "80 HP / 82 Atk / 83 Def / 100 SAtk / 100 SDef / 80 Spd / 525 BST")

        Returns:
            bool: True if successful
        """
        # Parse: "80 HP / 82 Atk / 83 Def / 100 SAtk / 100 SDef / 80 Spd / 525 BST"
        parts = value.split(" / ")
        if len(parts) != 7:
            logger.error(f"Invalid base stats format: {value}")
            return False

        try:
            hp = int(parts[0].split()[0])
            attack = int(parts[1].split()[0])
            defense = int(parts[2].split()[0])
            sp_attack = int(parts[3].split()[0])
            sp_defense = int(parts[4].split()[0])
            speed = int(parts[5].split()[0])

            # Update stats object
            pokemon_data.stats.hp = hp
            pokemon_data.stats.attack = attack
            pokemon_data.stats.defense = defense
            pokemon_data.stats.special_attack = sp_attack
            pokemon_data.stats.special_defense = sp_defense
            pokemon_data.stats.speed = speed

            # Save using PokeDBLoader
            PokeDBLoader.save_pokemon(pokemon_id, pokemon_data)
            logger.info(
                f"Updated base stats for '{pokemon_id}': "
                f"{hp}/{attack}/{defense}/{sp_attack}/{sp_defense}/{speed}"
            )
            return True

        except (ValueError, IndexError) as e:
            logger.error(f"Error parsing base stats '{value}': {e}")
            return False

    @staticmethod
    def _update_type(pokemon_id: str, pokemon_data: Any, value: str) -> bool:
        """
        Update type for a Pokemon.

        Args:
            pokemon_id: Pokemon ID
            pokemon_data: Pokemon dataclass object
            value: Type string (e.g., "Fire / Dragon" or "Fire")

        Returns:
            bool: True if successful
        """
        # Parse: "Fire / Dragon" or "Fire"
        types = [name_to_id(t.strip()) for t in value.split(" / ")]

        # Update types list (single or dual)
        pokemon_data.types = types

        # Save using PokeDBLoader
        PokeDBLoader.save_pokemon(pokemon_id, pokemon_data)
        type_str = " / ".join(types)
        logger.info(f"Updated type for '{pokemon_id}': {type_str}")
        return True

    @staticmethod
    def _update_ability(pokemon_id: str, pokemon_data: Any, value: str) -> bool:
        """
        Update abilities for a Pokemon.

        Args:
            pokemon_id: Pokemon ID
            pokemon_data: Pokemon dataclass object
            value: Ability string (e.g., "Overgrow / Overgrow / Chlorophyll")

        Returns:
            bool: True if successful
        """
        # Parse: "ability1 / ability2 / hidden_ability"
        abilities = [name_to_id(a.strip()) for a in value.split(" / ")]

        if len(abilities) != 3:
            logger.error(f"Invalid ability format (expected 3 abilities): {value}")
            return False

        # Build new abilities list
        # Structure: [{"name": str, "is_hidden": bool, "slot": int}]
        new_abilities = []

        # Add first ability (slot 1)
        new_abilities.append({"name": abilities[0], "is_hidden": False, "slot": 1})

        # Add second ability (slot 2) only if different from first
        if abilities[1] != abilities[0]:
            new_abilities.append({"name": abilities[1], "is_hidden": False, "slot": 2})

        # Add hidden ability (slot 3)
        new_abilities.append({"name": abilities[2], "is_hidden": True, "slot": 3})

        # Update abilities
        pokemon_data.abilities = new_abilities

        # Save using PokeDBLoader
        PokeDBLoader.save_pokemon(pokemon_id, pokemon_data)
        ability_str = " / ".join(abilities)
        logger.info(f"Updated abilities for '{pokemon_id}': {ability_str}")
        return True

    @staticmethod
    def _update_evs(pokemon_id: str, pokemon_data: Any, value: str) -> bool:
        """
        Update EV yields for a Pokemon.

        Args:
            pokemon_id: Pokemon ID
            pokemon_data: Pokemon dataclass object
            value: EV yield string (e.g., "2 Atk" or "1 SAtk, 1 Spd")

        Returns:
            bool: True if successful
        """
        # Parse: "2 Atk" or "1 SAtk, 1 Spd"
        # Map short names to stat names
        stat_map = {
            "HP": "hp",
            "Atk": "attack",
            "Def": "defense",
            "SAtk": "special-attack",
            "SDef": "special-defense",
            "Spd": "speed",
        }

        ev_yields = []
        parts = [p.strip() for p in value.split(",")]

        for part in parts:
            tokens = part.split()
            if len(tokens) != 2:
                logger.error(f"Invalid EV yield format: {part}")
                return False

            effort = int(tokens[0])
            stat_short = tokens[1]

            if stat_short not in stat_map:
                logger.error(f"Unknown stat abbreviation: {stat_short}")
                return False

            ev_yields.append({"stat": stat_map[stat_short], "effort": effort})

        # Update EV yield
        pokemon_data.ev_yield = ev_yields

        # Save using PokeDBLoader
        PokeDBLoader.save_pokemon(pokemon_id, pokemon_data)
        logger.info(f"Updated EV yields for '{pokemon_id}': {value}")
        return True

    @staticmethod
    def _update_base_happiness(pokemon_id: str, pokemon_data: Any, value: str) -> bool:
        """
        Update base happiness for a Pokemon.

        Args:
            pokemon_id: Pokemon ID
            pokemon_data: Pokemon dataclass object
            value: Base happiness string (e.g., "70")

        Returns:
            bool: True if successful
        """
        try:
            base_happiness = int(value.strip())
            pokemon_data.base_happiness = base_happiness

            # Save using PokeDBLoader
            PokeDBLoader.save_pokemon(pokemon_id, pokemon_data)
            logger.info(f"Updated base happiness for '{pokemon_id}': {base_happiness}")
            return True

        except ValueError as e:
            logger.error(f"Error parsing base happiness '{value}': {e}")
            return False

    @staticmethod
    def _update_base_experience(pokemon_id: str, pokemon_data: Any, value: str) -> bool:
        """
        Update base experience for a Pokemon.

        Args:
            pokemon_id: Pokemon ID
            pokemon_data: Pokemon dataclass object
            value: Base experience string (e.g., "248")

        Returns:
            bool: True if successful
        """
        try:
            base_experience = int(value.strip())
            pokemon_data.base_experience = base_experience

            # Save using PokeDBLoader
            PokeDBLoader.save_pokemon(pokemon_id, pokemon_data)
            logger.info(
                f"Updated base experience for '{pokemon_id}': {base_experience}"
            )
            return True

        except ValueError as e:
            logger.error(f"Error parsing base experience '{value}': {e}")
            return False

    @staticmethod
    def _update_catch_rate(pokemon_id: str, pokemon_data: Any, value: str) -> bool:
        """
        Update catch rate for a Pokemon.

        Args:
            pokemon_id: Pokemon ID
            pokemon_data: Pokemon dataclass object
            value: Catch rate string (e.g., "45")

        Returns:
            bool: True if successful
        """
        try:
            catch_rate = int(value.strip())
            pokemon_data.capture_rate = catch_rate

            # Save using PokeDBLoader
            PokeDBLoader.save_pokemon(pokemon_id, pokemon_data)
            logger.info(f"Updated catch rate for '{pokemon_id}': {catch_rate}")
            return True

        except ValueError as e:
            logger.error(f"Error parsing catch rate '{value}': {e}")
            return False

    @staticmethod
    def _update_gender_ratio(pokemon_id: str, pokemon_data: Any, value: str) -> bool:
        """
        Update gender ratio for a Pokemon.

        Args:
            pokemon_id: Pokemon ID
            pokemon_data: Pokemon dataclass object
            value: Gender ratio string (e.g., "50% Male, 50% Female" or "100% Male")

        Returns:
            bool: True if successful
        """
        # Parse: "87.5% Male, 12.5% Female" or "50% Male, 50% Female"
        # PokeAPI gender_rate:
        #   -1: Genderless
        #   0: Always male (100% male)
        #   1: 87.5% male, 12.5% female
        #   2: 75% male, 25% female
        #   3: 62.5% male, 37.5% female
        #   4: 50% male, 50% female
        #   5: 37.5% male, 62.5% female
        #   6: 25% male, 75% female
        #   7: 12.5% male, 87.5% female
        #   8: Always female (100% female)

        value_lower = value.lower()

        if "genderless" in value_lower or "no gender" in value_lower:
            gender_rate = -1
        elif "100% male" in value_lower:
            gender_rate = 0
        elif "100% female" in value_lower:
            gender_rate = 8
        else:
            # Extract female percentage
            match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*female", value_lower)
            if not match:
                logger.error(f"Could not parse gender ratio: {value}")
                return False

            female_percent = float(match.group(1))

            # Map to gender_rate (eighths)
            gender_rate_map = {
                0.0: 0,
                12.5: 1,
                25.0: 2,
                37.5: 3,
                50.0: 4,
                62.5: 5,
                75.0: 6,
                87.5: 7,
                100.0: 8,
            }

            if female_percent not in gender_rate_map:
                logger.error(f"Unsupported gender ratio: {female_percent}% female")
                return False

            gender_rate = gender_rate_map[female_percent]

        pokemon_data.gender_rate = gender_rate

        # Save using PokeDBLoader
        PokeDBLoader.save_pokemon(pokemon_id, pokemon_data)
        logger.info(
            f"Updated gender ratio for '{pokemon_id}': {value} (rate={gender_rate})"
        )
        return True

    @staticmethod
    def update_levelup_moves(
        pokemon: str, moves: list[tuple[int, str]], forme: str = ""
    ) -> bool:
        """
        Update level-up moves for a Pokemon.

        Args:
            pokemon: Name of the Pokemon to modify
            moves: List of (level, move_name) tuples
            forme: Optional forme name (e.g., "attack", "defense", "plant")

        Returns:
            bool: True if successful
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
                new_move = MoveLearn(
                    name=move_id,
                    level_learned_at=level,
                    version_groups=["black-2-white-2"]
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
            logger.error(f"Error updating level-up moves for '{pokemon}': {e}")
            return False

    @staticmethod
    def update_machine_moves(
        pokemon: str, moves: list[tuple[str, str, str]], forme: str = ""
    ) -> bool:
        """
        Update TM/HM compatibility for a Pokemon.

        Args:
            pokemon: Name of the Pokemon to modify
            moves: List of (machine_type, number, move_name) tuples
                   e.g., [("TM", "56", "Weather Ball")]
            forme: Optional forme name (e.g., "attack", "defense", "plant")

        Returns:
            bool: True if successful
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

                # Check if move already exists in machine moves
                existing_move = None
                for m in pokemon_data.moves.machine:
                    if m.name == move_id:
                        existing_move = m
                        break

                if existing_move:
                    # Update version groups if needed
                    if "black-2-white-2" not in existing_move.version_groups:
                        existing_move.version_groups.append("black-2-white-2")
                else:
                    # Add new machine move as a MoveLearn object
                    new_move = MoveLearn(
                        name=move_id,
                        level_learned_at=0,
                        version_groups=["black-2-white-2"]
                    )
                    pokemon_data.moves.machine.append(new_move)

            # Save using PokeDBLoader
            PokeDBLoader.save_pokemon(pokemon_id, pokemon_data)
            logger.info(
                f"Updated machine moves for '{pokemon_id}': added {len(moves)} TM/HM moves"
            )
            return True

        except (OSError, IOError, ValueError) as e:
            logger.error(f"Error updating machine moves for '{pokemon}': {e}")
            return False

    @staticmethod
    def update_held_item(
        pokemon: str, item_name: str, rarity: int, forme: str = ""
    ) -> bool:
        """
        Update held item for a Pokemon.

        Args:
            pokemon: Name of the Pokemon to modify
            item_name: Name of the held item
            rarity: Percentage chance (0-100)
            forme: Optional forme name (e.g., "attack", "defense", "plant")

        Returns:
            bool: True if successful
        """
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

            # Update held_items
            # Structure: {item_name: {version_group: rarity}}
            if item_id not in pokemon_data.held_items:
                pokemon_data.held_items[item_id] = {}

            pokemon_data.held_items[item_id]["black-2-white-2"] = rarity

            # Save using PokeDBLoader
            PokeDBLoader.save_pokemon(pokemon_id, pokemon_data)
            logger.info(
                f"Updated held item for '{pokemon_id}': {item_id} at {rarity}% rate"
            )
            return True

        except (OSError, IOError, ValueError) as e:
            logger.error(f"Error updating held item for '{pokemon}': {e}")
            return False
