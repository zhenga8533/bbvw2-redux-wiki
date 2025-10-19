"""
PokeDB data structures for parsing JSON files from the PokeDB repository.

This module defines dataclasses that correspond to the JSON structure of
Pokémon, items, moves, and abilities data.

Expected directory structure:
data/pokedb/
├── gen5/
│   ├── ability/
│   ├── item/
│   ├── move/
│   └── pokemon/
│       ├── cosmetic/
│       ├── default/
│       ├── transformation/
│       └── variant/
└── parsed/  (working copy of gen5 for modifications)
    └── ... (same structure as gen5)
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Literal, Optional


# region Enums and Constants
class Gender(IntEnum):
    """Represents gender constants for evolution triggers."""

    FEMALE = 1
    MALE = 2


# Pokemon Constants
MIN_ABILITY_SLOT = 1
MAX_ABILITY_SLOTS = 3
MIN_EV_YIELD = 0
MAX_EV_YIELD = 3
MIN_POKEMON_LEVEL = 1
MAX_POKEMON_LEVEL = 100
MIN_STAT_VALUE = 0
MIN_HAPPINESS = 0
MAX_HAPPINESS = 255
MIN_BEAUTY = 0
MAX_BEAUTY = 255
MIN_AFFECTION = 0
MAX_AFFECTION = 255
MIN_CAPTURE_RATE = 0
MAX_CAPTURE_RATE = 255
MIN_GENDER_RATE = -1
MAX_GENDER_RATE = 8

# Move Constants
MIN_MOVE_PRIORITY = -7
MAX_MOVE_PRIORITY = 5
MIN_PERCENTAGE = 0
MAX_PERCENTAGE = 100
MIN_DRAIN_HEALING = -100
MAX_DRAIN_HEALING = 100
# endregion


# region Helper Classes for Pokémon Structure
@dataclass(slots=True)
class PokemonAbility:
    """Represents an ability a Pokémon can have."""

    name: str
    is_hidden: bool
    slot: int

    def __post_init__(self):
        """Validate ability fields."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(
                f"Ability name must be a non-empty string, got: {self.name}"
            )
        if not isinstance(self.is_hidden, bool):
            raise ValueError(
                f"is_hidden must be a boolean, got: {type(self.is_hidden)}"
            )
        if (
            not isinstance(self.slot, int)
            or self.slot < MIN_ABILITY_SLOT
            or self.slot > MAX_ABILITY_SLOTS
        ):
            raise ValueError(
                f"Ability slot must be an integer between {MIN_ABILITY_SLOT} and {MAX_ABILITY_SLOTS}, got: {self.slot}"
            )


@dataclass(slots=True)
class Stats:
    """Represents the base stats of a Pokémon."""

    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int

    def __post_init__(self):
        """Validate stats are non-negative integers."""
        stat_fields = [
            "hp",
            "attack",
            "defense",
            "special_attack",
            "special_defense",
            "speed",
        ]
        for field_name in stat_fields:
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < MIN_STAT_VALUE:
                raise ValueError(
                    f"{field_name} must be a non-negative integer, got: {value}"
                )


@dataclass(slots=True)
class EVYield:
    """Represents the effort value yield of a Pokémon."""

    stat: str
    effort: int

    def __post_init__(self):
        """Validate EV yield fields."""
        valid_stats = {
            "hp",
            "attack",
            "defense",
            "special-attack",
            "special-defense",
            "speed",
        }
        if not isinstance(self.stat, str) or self.stat not in valid_stats:
            raise ValueError(f"stat must be one of {valid_stats}, got: {self.stat}")
        if (
            not isinstance(self.effort, int)
            or self.effort < MIN_EV_YIELD
            or self.effort > MAX_EV_YIELD
        ):
            raise ValueError(
                f"effort must be an integer between {MIN_EV_YIELD} and {MAX_EV_YIELD}, got: {self.effort}"
            )


@dataclass(slots=True)
class Cries:
    """Contains URLs to a Pokémon's cries."""

    latest: str
    legacy: Optional[str]

    def __post_init__(self):
        """Validate cries fields."""
        if not isinstance(self.latest, str):
            raise ValueError(f"latest must be a string, got: {type(self.latest)}")


@dataclass(slots=True)
class DreamWorld:
    front_default: Optional[str]
    front_female: Optional[str]

    def __post_init__(self):
        """Validate DreamWorld sprite URLs."""
        if self.front_default is not None and not isinstance(self.front_default, str):
            raise ValueError(
                f"front_default must be None or a string, got: {type(self.front_default)}"
            )
        if self.front_female is not None and not isinstance(self.front_female, str):
            raise ValueError(
                f"front_female must be None or a string, got: {type(self.front_female)}"
            )


@dataclass(slots=True)
class Home:
    front_default: Optional[str]
    front_female: Optional[str]
    front_shiny: Optional[str]
    front_shiny_female: Optional[str]

    def __post_init__(self):
        """Validate Home sprite URLs."""
        optional_fields = [
            "front_default",
            "front_female",
            "front_shiny",
            "front_shiny_female",
        ]
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise ValueError(
                    f"{field_name} must be None or a string, got: {type(value)}"
                )


@dataclass(slots=True)
class OfficialArtwork:
    front_default: Optional[str]
    front_shiny: Optional[str]

    def __post_init__(self):
        """Validate OfficialArtwork sprite URLs."""
        if self.front_default is not None and not isinstance(self.front_default, str):
            raise ValueError(
                f"front_default must be None or a string, got: {type(self.front_default)}"
            )
        if self.front_shiny is not None and not isinstance(self.front_shiny, str):
            raise ValueError(
                f"front_shiny must be None or a string, got: {type(self.front_shiny)}"
            )


@dataclass(slots=True)
class Showdown:
    back_default: Optional[str]
    back_female: Optional[str]
    back_shiny: Optional[str]
    back_shiny_female: Optional[str]
    front_default: Optional[str]
    front_female: Optional[str]
    front_shiny: Optional[str]
    front_shiny_female: Optional[str]

    def __post_init__(self):
        """Validate Showdown sprite URLs."""
        optional_fields = [
            "back_default",
            "back_female",
            "back_shiny",
            "back_shiny_female",
            "front_default",
            "front_female",
            "front_shiny",
            "front_shiny_female",
        ]
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise ValueError(
                    f"{field_name} must be None or a string, got: {type(value)}"
                )


@dataclass(slots=True)
class OtherSprites:
    dream_world: DreamWorld
    home: Home
    official_artwork: OfficialArtwork
    showdown: Showdown

    def __post_init__(self):
        """Validate OtherSprites nested objects."""
        if not isinstance(self.dream_world, DreamWorld):
            raise ValueError(
                f"dream_world must be a DreamWorld instance, got: {type(self.dream_world)}"
            )
        if not isinstance(self.home, Home):
            raise ValueError(f"home must be a Home instance, got: {type(self.home)}")
        if not isinstance(self.official_artwork, OfficialArtwork):
            raise ValueError(
                f"official_artwork must be an OfficialArtwork instance, got: {type(self.official_artwork)}"
            )
        if not isinstance(self.showdown, Showdown):
            raise ValueError(
                f"showdown must be a Showdown instance, got: {type(self.showdown)}"
            )


@dataclass(slots=True)
class AnimatedSprites:
    back_default: Optional[str]
    back_female: Optional[str]
    back_shiny: Optional[str]
    back_shiny_female: Optional[str]
    front_default: Optional[str]
    front_female: Optional[str]
    front_shiny: Optional[str]
    front_shiny_female: Optional[str]

    def __post_init__(self):
        """Validate AnimatedSprites URLs."""
        optional_fields = [
            "back_default",
            "back_female",
            "back_shiny",
            "back_shiny_female",
            "front_default",
            "front_female",
            "front_shiny",
            "front_shiny_female",
        ]
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise ValueError(
                    f"{field_name} must be None or a string, got: {type(value)}"
                )


@dataclass(slots=True)
class GenerationSprites:
    animated: AnimatedSprites
    back_default: Optional[str]
    back_female: Optional[str]
    back_shiny: Optional[str]
    back_shiny_female: Optional[str]
    front_default: Optional[str]
    front_female: Optional[str]
    front_shiny: Optional[str]
    front_shiny_female: Optional[str]

    def __post_init__(self):
        """Validate GenerationSprites nested objects and URLs."""
        if not isinstance(self.animated, AnimatedSprites):
            raise ValueError(
                f"animated must be an AnimatedSprites instance, got: {type(self.animated)}"
            )
        optional_fields = [
            "back_default",
            "back_female",
            "back_shiny",
            "back_shiny_female",
            "front_default",
            "front_female",
            "front_shiny",
            "front_shiny_female",
        ]
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise ValueError(
                    f"{field_name} must be None or a string, got: {type(value)}"
                )


@dataclass(slots=True)
class Versions:
    black_white: GenerationSprites

    def __post_init__(self):
        """Validate Versions nested objects."""
        if not isinstance(self.black_white, GenerationSprites):
            raise ValueError(
                f"black_white must be a GenerationSprites instance, got: {type(self.black_white)}"
            )


@dataclass(slots=True)
class Sprites:
    """Contains URLs to all Pokémon sprites."""

    back_default: Optional[str]
    back_shiny: Optional[str]
    front_default: Optional[str]
    front_shiny: Optional[str]
    other: OtherSprites
    versions: Versions
    back_female: Optional[str] = None
    front_female: Optional[str] = None
    front_shiny_female: Optional[str] = None
    back_shiny_female: Optional[str] = None

    def __post_init__(self):
        """Validate Sprites nested objects and URLs."""
        if not isinstance(self.other, OtherSprites):
            raise ValueError(
                f"other must be an OtherSprites instance, got: {type(self.other)}"
            )
        if not isinstance(self.versions, Versions):
            raise ValueError(
                f"versions must be a Versions instance, got: {type(self.versions)}"
            )
        optional_fields = [
            "back_default",
            "back_shiny",
            "front_default",
            "front_shiny",
            "back_female",
            "front_female",
            "front_shiny_female",
            "back_shiny_female",
        ]
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise ValueError(
                    f"{field_name} must be None or a string, got: {type(value)}"
                )


@dataclass(slots=True)
class EvolutionDetails:
    item: Optional[str] = None
    gender: Optional[Gender] = None
    held_item: Optional[str] = None
    known_move: Optional[str] = None
    known_move_type: Optional[str] = None
    location: Optional[str] = None
    min_level: Optional[int] = None
    min_happiness: Optional[int] = None
    min_beauty: Optional[int] = None
    min_affection: Optional[int] = None
    party_species: Optional[str] = None
    party_type: Optional[str] = None
    relative_physical_stats: Optional[int] = None
    trade_species: Optional[str] = None
    trigger: Optional[str] = None
    time_of_day: Optional[str] = None
    needs_overworld_rain: Optional[bool] = None
    turn_upside_down: Optional[bool] = None

    def __post_init__(self):
        """Validate evolution details fields."""
        # Validate optional string fields
        string_fields = [
            "item",
            "held_item",
            "known_move",
            "known_move_type",
            "location",
            "party_species",
            "party_type",
            "trade_species",
            "trigger",
            "time_of_day",
        ]
        for field_name in string_fields:
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise ValueError(
                    f"{field_name} must be None or a string, got: {type(value)}"
                )

        # Validate boolean fields
        if self.needs_overworld_rain is not None and not isinstance(
            self.needs_overworld_rain, bool
        ):
            raise ValueError(
                f"needs_overworld_rain must be a boolean, got: {type(self.needs_overworld_rain)}"
            )
        if self.turn_upside_down is not None and not isinstance(
            self.turn_upside_down, bool
        ):
            raise ValueError(
                f"turn_upside_down must be a boolean, got: {type(self.turn_upside_down)}"
            )

        def _validate_optional_int(
            val: Optional[int], name: str, min_val: int, max_val: int
        ):
            """Helper to validate an optional integer within a range."""
            if val is not None and (
                not isinstance(val, int) or not (min_val <= val <= max_val)
            ):
                raise ValueError(
                    f"{name} must be None or between {min_val} and {max_val}, got: {val}"
                )

        # Validate optional integer fields with reasonable ranges
        if self.gender is not None and self.gender not in list(Gender):
            raise ValueError(
                f"gender must be None or a valid Gender enum, got: {self.gender}"
            )
        _validate_optional_int(
            self.min_level, "min_level", MIN_POKEMON_LEVEL, MAX_POKEMON_LEVEL
        )
        _validate_optional_int(
            self.min_happiness, "min_happiness", MIN_HAPPINESS, MAX_HAPPINESS
        )
        _validate_optional_int(self.min_beauty, "min_beauty", MIN_BEAUTY, MAX_BEAUTY)
        _validate_optional_int(
            self.min_affection, "min_affection", MIN_AFFECTION, MAX_AFFECTION
        )
        if self.relative_physical_stats is not None and (
            not isinstance(self.relative_physical_stats, int)
            or self.relative_physical_stats not in (-1, 0, 1)
        ):
            raise ValueError(
                f"relative_physical_stats must be None, -1, 0, or 1, got: {self.relative_physical_stats}"
            )


@dataclass(slots=True)
class EvolutionNode:
    species_name: str
    evolves_to: list["EvolutionNode"]
    evolution_details: Optional[EvolutionDetails] = None

    def __post_init__(self):
        """Validate evolution node fields."""
        if not isinstance(self.species_name, str) or not self.species_name.strip():
            raise ValueError(
                f"species_name must be a non-empty string, got: {self.species_name}"
            )
        if not isinstance(self.evolves_to, list):
            raise ValueError("evolves_to must be a list")


@dataclass(slots=True)
class EvolutionChain:
    species_name: str = ""
    evolves_to: list[EvolutionNode] = field(default_factory=list)

    def __post_init__(self):
        """Validate evolution chain fields."""
        if not isinstance(self.species_name, str):
            raise ValueError(
                f"species_name must be a string, got: {type(self.species_name)}"
            )
        if not isinstance(self.evolves_to, list):
            raise ValueError("evolves_to must be a list")


@dataclass(slots=True)
class MoveLearn:
    name: str
    level_learned_at: int
    version_groups: list[str]

    def __post_init__(self):
        """Validate move learn fields."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"name must be a non-empty string, got: {self.name}")
        if not isinstance(self.level_learned_at, int) or self.level_learned_at < 0:
            raise ValueError(
                f"level_learned_at must be a non-negative integer, got: {self.level_learned_at}"
            )
        if not isinstance(self.version_groups, list) or not all(
            isinstance(vg, str) for vg in self.version_groups
        ):
            raise ValueError("version_groups must be a list of strings")


@dataclass(slots=True)
class PokemonMoves:
    egg: list[MoveLearn] = field(default_factory=list)
    tutor: list[MoveLearn] = field(default_factory=list)
    machine: list[MoveLearn] = field(default_factory=list)
    level_up: list[MoveLearn] = field(default_factory=list)
    extra_fields: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PokemonMoves":
        """Create a PokemonMoves object from a dictionary, allowing extra fields."""
        # Convert each move list to MoveLearn objects
        known_fields = {"egg", "tutor", "machine", "level_up"}
        init_data = {}
        for move_type in known_fields:
            init_data[move_type] = [
                MoveLearn(**move)
                for move in data.get(move_type, [])
                if isinstance(move, dict)
            ]

        # Store any unexpected fields in extra_fields
        extra = {k: v for k, v in data.items() if k not in known_fields}
        init_data["extra_fields"] = extra
        return cls(**init_data)


# endregion


# region Helper Classes for Move Structure
@dataclass(slots=True)
class MoveMetadata:
    ailment: str
    category: str
    min_hits: Optional[int]
    max_hits: Optional[int]
    min_turns: Optional[int]
    max_turns: Optional[int]
    drain: int
    healing: int
    crit_rate: int
    ailment_chance: int
    flinch_chance: int
    stat_chance: int

    def __post_init__(self):
        """Validate move metadata fields."""
        if not isinstance(self.ailment, str):
            raise ValueError(f"ailment must be a string, got: {type(self.ailment)}")
        if not isinstance(self.category, str):
            raise ValueError(f"category must be a string, got: {type(self.category)}")

        # Validate optional integer fields
        for field_name in ["min_hits", "max_hits", "min_turns", "max_turns"]:
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, int) or value < 0):
                raise ValueError(
                    f"{field_name} must be None or a non-negative integer, got: {value}"
                )

        # Validate percentage/chance fields (0-100)
        for field_name in [
            "crit_rate",
            "ailment_chance",
            "flinch_chance",
            "stat_chance",
        ]:
            value = getattr(self, field_name)
            if (
                not isinstance(value, int)
                or value < MIN_PERCENTAGE
                or value > MAX_PERCENTAGE
            ):
                raise ValueError(
                    f"{field_name} must be an integer between {MIN_PERCENTAGE} and {MAX_PERCENTAGE}, got: {value}"
                )

        # Validate drain and healing (-100 to 100, can be negative for drain)
        for field_name in ["drain", "healing"]:
            value = getattr(self, field_name)
            if (
                not isinstance(value, int)
                or value < MIN_DRAIN_HEALING
                or value > MAX_DRAIN_HEALING
            ):
                raise ValueError(
                    f"{field_name} must be an integer between {MIN_DRAIN_HEALING} and {MAX_DRAIN_HEALING}, got: {value}"
                )


@dataclass(slots=True)
class StatChange:
    """Represents a stat change from a move."""

    change: int
    stat: str

    def __post_init__(self):
        """Validate stat change fields."""
        valid_stats = {
            "hp",
            "attack",
            "defense",
            "special_attack",
            "special_defense",
            "speed",
            "accuracy",
            "evasion",
        }
        if not isinstance(self.stat, str) or self.stat not in valid_stats:
            raise ValueError(f"stat must be one of {valid_stats}, got: {self.stat}")
        if not isinstance(self.change, int):
            raise ValueError(f"change must be an integer, got: {type(self.change)}")


# endregion


# region Top-Level Data Structures
@dataclass(slots=True)
class Item:
    """Represents a Pokémon item (e.g., Aguav Berry)."""

    id: int
    name: str
    source_url: str
    cost: int
    fling_power: Optional[int]
    fling_effect: Optional[str]
    attributes: list[str]
    category: str
    effect: str
    short_effect: str
    flavor_text: dict[str, str]
    sprite: str

    def __post_init__(self):
        """Validate item fields."""
        if not isinstance(self.id, int) or self.id <= 0:
            raise ValueError(f"id must be a positive integer, got: {self.id}")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"name must be a non-empty string, got: {self.name}")
        if not isinstance(self.source_url, str):
            raise ValueError(
                f"source_url must be a string, got: {type(self.source_url)}"
            )
        if not isinstance(self.cost, int) or self.cost < 0:
            raise ValueError(f"cost must be a non-negative integer, got: {self.cost}")
        if self.fling_power is not None and (
            not isinstance(self.fling_power, int) or self.fling_power < 0
        ):
            raise ValueError(
                f"fling_power must be a non-negative integer, got: {self.fling_power}"
            )
        if self.fling_effect is not None and not isinstance(self.fling_effect, str):
            raise ValueError(
                f"fling_effect must be None or a string, got: {type(self.fling_effect)}"
            )
        if not isinstance(self.attributes, list) or not all(
            isinstance(attr, str) for attr in self.attributes
        ):
            raise ValueError("attributes must be a list of strings")
        if not isinstance(self.category, str) or not self.category.strip():
            raise ValueError(
                f"category must be a non-empty string, got: {self.category}"
            )
        if not isinstance(self.effect, str):
            raise ValueError(f"effect must be a string, got: {type(self.effect)}")
        if not isinstance(self.short_effect, str):
            raise ValueError(
                f"short_effect must be a string, got: {type(self.short_effect)}"
            )
        if not isinstance(self.flavor_text, dict):
            raise ValueError(
                f"flavor_text must be a dict, got: {type(self.flavor_text)}"
            )
        if not isinstance(self.sprite, str):
            raise ValueError(f"sprite must be a string, got: {type(self.sprite)}")


@dataclass(slots=True)
class Ability:
    """Represents a Pokémon ability (e.g., Anticipation)."""

    id: int
    name: str
    source_url: str
    is_main_series: bool
    effect: dict[str, str]
    short_effect: str
    flavor_text: dict[str, str]

    def __post_init__(self):
        """Validate ability fields."""
        if not isinstance(self.id, int) or self.id <= 0:
            raise ValueError(f"id must be a positive integer, got: {self.id}")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"name must be a non-empty string, got: {self.name}")
        if not isinstance(self.source_url, str):
            raise ValueError(
                f"source_url must be a string, got: {type(self.source_url)}"
            )
        if not isinstance(self.is_main_series, bool):
            raise ValueError(
                f"is_main_series must be a boolean, got: {type(self.is_main_series)}"
            )
        if not isinstance(self.effect, dict):
            raise ValueError(f"effect must be a dict, got: {type(self.effect)}")
        if not isinstance(self.short_effect, str):
            raise ValueError(
                f"short_effect must be a string, got: {type(self.short_effect)}"
            )
        if not isinstance(self.flavor_text, dict):
            raise ValueError(
                f"flavor_text must be a dict, got: {type(self.flavor_text)}"
            )


@dataclass(slots=True)
class Move:
    """Represents a Pokémon move (e.g., Beat Up)."""

    id: int
    name: str
    source_url: str
    accuracy: dict[str, int]
    power: dict[str, Optional[int]]
    pp: dict[str, int]
    priority: int
    damage_class: str
    type: dict[str, str]
    target: str
    generation: str
    effect_chance: dict[str, Optional[int]]
    effect: dict[str, str]
    short_effect: dict[str, str]
    flavor_text: dict[str, str]
    stat_changes: list[StatChange]
    machine: Optional[dict[str, Any]]
    metadata: MoveMetadata

    def __post_init__(self):
        """Validate move fields."""
        if not isinstance(self.id, int) or self.id <= 0:
            raise ValueError(f"id must be a positive integer, got: {self.id}")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"name must be a non-empty string, got: {self.name}")
        if not isinstance(self.source_url, str):
            raise ValueError(
                f"source_url must be a string, got: {type(self.source_url)}"
            )
        if not isinstance(self.accuracy, dict):
            raise ValueError(f"accuracy must be a dict, got: {type(self.accuracy)}")
        if not isinstance(self.power, dict):
            raise ValueError(f"power must be a dict, got: {type(self.power)}")
        if not isinstance(self.pp, dict):
            raise ValueError(f"pp must be a dict, got: {type(self.pp)}")
        if (
            not isinstance(self.priority, int)
            or self.priority < MIN_MOVE_PRIORITY
            or self.priority > MAX_MOVE_PRIORITY
        ):
            raise ValueError(
                f"priority must be an integer between {MIN_MOVE_PRIORITY} and {MAX_MOVE_PRIORITY}, got: {self.priority}"
            )
        if not isinstance(self.damage_class, str) or not self.damage_class.strip():
            raise ValueError(
                f"damage_class must be a non-empty string, got: {self.damage_class}"
            )
        if not isinstance(self.type, dict):
            raise ValueError(f"type must be a dict, got: {type(self.type)}")
        if not isinstance(self.target, str) or not self.target.strip():
            raise ValueError(f"target must be a non-empty string, got: {self.target}")
        if not isinstance(self.generation, str) or not self.generation.strip():
            raise ValueError(
                f"generation must be a non-empty string, got: {self.generation}"
            )
        if not isinstance(self.effect_chance, dict):
            raise ValueError(
                f"effect_chance must be a dict, got: {type(self.effect_chance)}"
            )
        if not isinstance(self.effect, dict):
            raise ValueError(f"effect must be a dict, got: {type(self.effect)}")
        if not isinstance(self.short_effect, dict):
            raise ValueError(
                f"short_effect must be a dict, got: {type(self.short_effect)}"
            )
        if not isinstance(self.flavor_text, dict):
            raise ValueError(
                f"flavor_text must be a dict, got: {type(self.flavor_text)}"
            )
        if not isinstance(self.stat_changes, list):
            raise ValueError(
                f"stat_changes must be a list, got: {type(self.stat_changes)}"
            )
        if self.machine is not None and not isinstance(self.machine, dict):
            raise ValueError(
                f"machine must be None or a dict, got: {type(self.machine)}"
            )
        if not isinstance(self.metadata, MoveMetadata):
            raise ValueError(
                f"metadata must be a MoveMetadata instance, got: {type(self.metadata)}"
            )


@dataclass(slots=True)
class Form:
    """Represents a Pokémon form (e.g., Mega Charizard X)."""

    name: str
    category: Literal["default", "cosmetic", "transformation", "variant"]

    def __post_init__(self):
        """Validate form fields."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"name must be a non-empty string, got: {self.name}")
        valid_categories = {"default", "cosmetic", "transformation", "variant"}
        if self.category not in valid_categories:
            raise ValueError(
                f"category must be one of {valid_categories}, got: {self.category}"
            )


@dataclass(slots=True)
class Pokemon:
    """Represents a Pokémon (e.g., Aggron)."""

    id: int
    name: str
    species: str
    is_default: bool
    source_url: str
    types: list[str]
    abilities: list[PokemonAbility]
    stats: Stats
    ev_yield: list[EVYield]
    height: int
    weight: int
    cries: Cries
    sprites: Sprites
    base_experience: int
    base_happiness: int
    capture_rate: int
    hatch_counter: int
    gender_rate: int
    has_gender_differences: bool
    is_baby: bool
    is_legendary: bool
    is_mythical: bool
    pokedex_numbers: dict[str, int]
    color: str
    shape: str
    egg_groups: list[str]
    flavor_text: dict[str, str]
    genus: str
    generation: str
    evolution_chain: EvolutionChain
    held_items: dict[str, dict[str, int]]
    moves: PokemonMoves
    forms: list[Form]

    def __post_init__(self):
        """Validate Pokemon fields."""
        if not isinstance(self.id, int) or self.id <= 0:
            raise ValueError(f"id must be a positive integer, got: {self.id}")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"name must be a non-empty string, got: {self.name}")
        if not isinstance(self.species, str) or not self.species.strip():
            raise ValueError(f"species must be a non-empty string, got: {self.species}")
        if not isinstance(self.is_default, bool):
            raise ValueError(
                f"is_default must be a boolean, got: {type(self.is_default)}"
            )
        if not isinstance(self.source_url, str):
            raise ValueError(
                f"source_url must be a string, got: {type(self.source_url)}"
            )
        if (
            not isinstance(self.types, list)
            or not self.types
            or not all(isinstance(t, str) for t in self.types)
        ):
            raise ValueError("types must be a non-empty list of strings")
        if not isinstance(self.abilities, list) or not all(
            isinstance(a, PokemonAbility) for a in self.abilities
        ):
            raise ValueError("abilities must be a list of PokemonAbility instances")
        if not isinstance(self.stats, Stats):
            raise ValueError(f"stats must be a Stats instance, got: {type(self.stats)}")
        if not isinstance(self.ev_yield, list) or not all(
            isinstance(ev, EVYield) for ev in self.ev_yield
        ):
            raise ValueError("ev_yield must be a list of EVYield instances")
        if not isinstance(self.height, int) or self.height < 0:
            raise ValueError(
                f"height must be a non-negative integer, got: {self.height}"
            )
        if not isinstance(self.weight, int) or self.weight < 0:
            raise ValueError(
                f"weight must be a non-negative integer, got: {self.weight}"
            )
        if not isinstance(self.cries, Cries):
            raise ValueError(f"cries must be a Cries instance, got: {type(self.cries)}")
        if not isinstance(self.sprites, Sprites):
            raise ValueError(
                f"sprites must be a Sprites instance, got: {type(self.sprites)}"
            )
        if (
            not isinstance(self.base_experience, int)
            or self.base_experience < MIN_STAT_VALUE
        ):
            raise ValueError(
                f"base_experience must be a non-negative integer, got: {self.base_experience}"
            )
        if (
            not isinstance(self.base_happiness, int)
            or self.base_happiness < MIN_HAPPINESS
            or self.base_happiness > MAX_HAPPINESS
        ):
            raise ValueError(
                f"base_happiness must be between {MIN_HAPPINESS} and {MAX_HAPPINESS}, got: {self.base_happiness}"
            )
        if (
            not isinstance(self.capture_rate, int)
            or self.capture_rate < MIN_CAPTURE_RATE
            or self.capture_rate > MAX_CAPTURE_RATE
        ):
            raise ValueError(
                f"capture_rate must be between {MIN_CAPTURE_RATE} and {MAX_CAPTURE_RATE}, got: {self.capture_rate}"
            )
        if (
            not isinstance(self.hatch_counter, int)
            or self.hatch_counter < MIN_STAT_VALUE
        ):
            raise ValueError(
                f"hatch_counter must be a non-negative integer, got: {self.hatch_counter}"
            )
        if (
            not isinstance(self.gender_rate, int)
            or self.gender_rate < MIN_GENDER_RATE
            or self.gender_rate > MAX_GENDER_RATE
        ):
            raise ValueError(
                f"gender_rate must be between {MIN_GENDER_RATE} and {MAX_GENDER_RATE}, got: {self.gender_rate}"
            )
        if not isinstance(self.has_gender_differences, bool):
            raise ValueError(
                f"has_gender_differences must be a boolean, got: {type(self.has_gender_differences)}"
            )
        if not isinstance(self.is_baby, bool):
            raise ValueError(f"is_baby must be a boolean, got: {type(self.is_baby)}")
        if not isinstance(self.is_legendary, bool):
            raise ValueError(
                f"is_legendary must be a boolean, got: {type(self.is_legendary)}"
            )
        if not isinstance(self.is_mythical, bool):
            raise ValueError(
                f"is_mythical must be a boolean, got: {type(self.is_mythical)}"
            )
        if not isinstance(self.pokedex_numbers, dict):
            raise ValueError(
                f"pokedex_numbers must be a dict, got: {type(self.pokedex_numbers)}"
            )
        if not isinstance(self.color, str) or not self.color.strip():
            raise ValueError(f"color must be a non-empty string, got: {self.color}")
        if not isinstance(self.shape, str) or not self.shape.strip():
            raise ValueError(f"shape must be a non-empty string, got: {self.shape}")
        if not isinstance(self.egg_groups, list) or not all(
            isinstance(eg, str) for eg in self.egg_groups
        ):
            raise ValueError("egg_groups must be a list of strings")
        if not isinstance(self.flavor_text, dict):
            raise ValueError(
                f"flavor_text must be a dict, got: {type(self.flavor_text)}"
            )
        if not isinstance(self.genus, str):
            raise ValueError(f"genus must be a string, got: {type(self.genus)}")
        if not isinstance(self.generation, str) or not self.generation.strip():
            raise ValueError(
                f"generation must be a non-empty string, got: {self.generation}"
            )
        if not isinstance(self.evolution_chain, EvolutionChain):
            raise ValueError(
                f"evolution_chain must be an EvolutionChain instance, got: {type(self.evolution_chain)}"
            )
        if not isinstance(self.held_items, dict):
            raise ValueError(f"held_items must be a dict, got: {type(self.held_items)}")
        if not isinstance(self.moves, PokemonMoves):
            raise ValueError(
                f"moves must be a PokemonMoves instance, got: {type(self.moves)}"
            )
        if not isinstance(self.forms, list) or not all(
            isinstance(f, Form) for f in self.forms
        ):
            raise ValueError("forms must be a list of Form instances")


# endregion
