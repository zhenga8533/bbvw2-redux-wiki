"""
Base service class providing change tracking utilities for all services.
"""

from datetime import datetime, timezone
from typing import Any, Union

from bbvw2_redux_wiki.utils.core.logger import get_logger

logger = get_logger(__name__)


class BaseService:
    """Base service class providing change tracking utilities."""

    @staticmethod
    def record_change(
        data_object: Any,
        field: str,
        old_value: Any,
        new_value: Any,
        source: str = "unknown",
    ) -> bool:
        """Record a change to a data object.

        Prevents duplicate changes by checking if a change for the same field already exists.
        If it exists, updates the new_value and timestamp (keeping original old_value).
        If it doesn't exist, adds a new change record.

        Args:
            data_object: The data object to record change for (Pokemon, Move, Item, Ability)
            field: Human-readable field name (e.g., "Base Stats", "Type", "Ability")
            old_value: Previous value (will be stringified)
            new_value: New value (will be stringified)
            source: Source of the change (parser name, service name, etc.)

        Returns:
            bool: True if change was recorded (values differ), False if no-op
        """
        # Convert values to strings for comparison
        old_str = BaseService._value_to_string(old_value)
        new_str = BaseService._value_to_string(new_value)

        # Skip if values are identical
        if old_str == new_str:
            return False

        # Initialize changes list if needed
        if not hasattr(data_object, "changes"):
            data_object.changes = []

        # Check if a change for this field already exists
        existing_change = None
        for change in data_object.changes:
            if change.get("field") == field:
                existing_change = change
                break

        if existing_change:
            # Update existing change: keep original old_value, update new_value
            # Skip if the final value is the same as the existing new_value
            if existing_change.get("new_value") == new_str:
                return False

            existing_change["new_value"] = new_str
            existing_change["timestamp"] = datetime.now(timezone.utc).isoformat()
            existing_change["source"] = source
            logger.debug(
                f"Updated existing change: {field} = '{existing_change.get('old_value')}' → '{new_str}' (source: {source})"
            )
        else:
            # Create new change record
            change_record = {
                "field": field,
                "old_value": old_str,
                "new_value": new_str,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": source,
            }
            data_object.changes.append(change_record)
            logger.debug(
                f"Recorded change: {field} = '{old_str}' → '{new_str}' (source: {source})"
            )

        return True

    @staticmethod
    def _value_to_string(value: Any) -> str:
        """Convert a value to string representation for change tracking.

        Args:
            value: Any value to convert to string

        Returns:
            str: String representation of the value
        """
        if value is None:
            return "None"
        elif isinstance(value, list):
            # Handle lists (abilities, types, moves, etc.)
            return " / ".join(str(v) for v in value)
        elif isinstance(value, dict):
            # Handle dicts - convert to string
            return str(value)
        elif hasattr(value, "__dict__"):
            # Handle objects - convert to string representation
            return str(value)
        else:
            return str(value)

    @staticmethod
    def format_stat_change(old_stats: Any, new_stats: Any) -> tuple[str, str]:
        """Format base stats for change tracking.

        Args:
            old_stats: Old stats object or dict
            new_stats: New stats object or dict

        Returns:
            tuple[str, str]: (old_value_str, new_value_str)
        """

        def format_stats(stats):
            """Format a stats object into a readable string."""
            if stats is None:
                return "None"
            if hasattr(stats, "hp"):
                # Stats object
                return (
                    f"{stats.hp} HP / {stats.attack} Atk / {stats.defense} Def / "
                    f"{stats.special_attack} SAtk / {stats.special_defense} SDef / {stats.speed} Spd"
                )
            elif isinstance(stats, dict):
                # Dict with stat values
                return (
                    f"{stats.get('hp', '?')} HP / {stats.get('attack', '?')} Atk / {stats.get('defense', '?')} Def / "
                    f"{stats.get('special_attack', '?')} SAtk / {stats.get('special_defense', '?')} SDef / {stats.get('speed', '?')} Spd"
                )
            return str(stats)

        return (format_stats(old_stats), format_stats(new_stats))

    @staticmethod
    def format_type_change(old_types: list[str], new_types: list[str]) -> tuple[str, str]:
        """Format type changes for change tracking.

        Args:
            old_types: Old type list
            new_types: New type list

        Returns:
            tuple[str, str]: (old_value_str, new_value_str)
        """
        old_str = " / ".join(old_types) if old_types else "None"
        new_str = " / ".join(new_types) if new_types else "None"
        return (old_str, new_str)

    @staticmethod
    def format_ability_change(
        old_abilities: list[dict], new_abilities: list[dict]
    ) -> tuple[str, str]:
        """Format ability changes for change tracking.

        Args:
            old_abilities: Old abilities list
            new_abilities: New abilities list

        Returns:
            tuple[str, str]: (old_value_str, new_value_str)
        """

        def format_abilities(abilities):
            """Format abilities list into a readable string."""
            if not abilities:
                return "None"
            # Extract ability names in order of slot
            sorted_abilities = sorted(abilities, key=lambda a: a.get("slot", 0))
            names = [a.get("name", "?") for a in sorted_abilities]
            return " / ".join(names)

        return (format_abilities(old_abilities), format_abilities(new_abilities))

    @staticmethod
    def format_ev_yield_change(
        old_ev_yield: list[dict], new_ev_yield: list[dict]
    ) -> tuple[str, str]:
        """Format EV yield changes for change tracking.

        Args:
            old_ev_yield: Old EV yield list
            new_ev_yield: New EV yield list

        Returns:
            tuple[str, str]: (old_value_str, new_value_str)
        """

        def format_ev_yield(ev_yield):
            """Format EV yield list into a readable string."""
            if not ev_yield:
                return "None"
            # Format as "2 Atk, 1 Spd" etc
            stat_map = {
                "hp": "HP",
                "attack": "Atk",
                "defense": "Def",
                "special-attack": "SAtk",
                "special_attack": "SAtk",
                "special-defense": "SDef",
                "special_defense": "SDef",
                "speed": "Spd",
            }
            parts = []
            for ev in ev_yield:
                effort = ev.get("effort", 0)
                stat = ev.get("stat", "?")
                stat_short = stat_map.get(stat, stat)
                parts.append(f"{effort} {stat_short}")
            return ", ".join(parts)

        return (format_ev_yield(old_ev_yield), format_ev_yield(new_ev_yield))

    @staticmethod
    def format_move_list_change(
        old_moves: list[dict], new_moves: list[dict]
    ) -> tuple[str, str]:
        """Format move list changes for change tracking.

        Args:
            old_moves: Old moves list
            new_moves: New moves list

        Returns:
            tuple[str, str]: (old_value_str, new_value_str)
        """

        def format_moves(moves):
            """Format move list into a readable string (count only)."""
            if not moves:
                return "None"
            # Simplified format: just show the count
            count = len(moves)
            return f"{count} move{'s' if count != 1 else ''}"

        return (format_moves(old_moves), format_moves(new_moves))

    @staticmethod
    def format_gender_ratio_change(
        old_ratio: int, new_ratio: int
    ) -> tuple[str, str]:
        """Format gender ratio changes for change tracking.

        Args:
            old_ratio: Old gender rate (-1 to 8)
            new_ratio: New gender rate (-1 to 8)

        Returns:
            tuple[str, str]: (old_value_str, new_value_str)
        """

        def format_ratio(ratio):
            """Format gender ratio into readable string."""
            if ratio == -1:
                return "Genderless"
            elif ratio == 0:
                return "100% Male"
            elif ratio == 8:
                return "100% Female"
            else:
                # Calculate percentages
                female_percent = (ratio / 8) * 100
                male_percent = 100 - female_percent
                return f"{male_percent:.1f}% Male / {female_percent:.1f}% Female"

        return (format_ratio(old_ratio), format_ratio(new_ratio))
