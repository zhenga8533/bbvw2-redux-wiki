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
from dataclasses import dataclass, field, fields
from typing import Any


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
            "special_attack",
            "special_defense",
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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EVYield":
        """
        Create an EVYield object from a dictionary.

        Note: The backend data repository uses snake_case for JSON field names,
        but the stat VALUES may still be in kebab-case in some legacy data.
        This method converts kebab-case stat values to snake_case for
        backwards compatibility.

        Example:
            Data: {"stat": "special-defense", "effort": 2}
            Becomes: EVYield(stat="special_defense", effort=2)
        """
        # Convert kebab-case to snake_case for stat values
        # (Field names are already snake_case from the JSON)
        if "stat" in data and isinstance(data["stat"], str):
            data["stat"] = data["stat"].replace("-", "_")
        return cls(**data)


@dataclass(slots=True)
class Cries:
    """Contains URLs to a Pokémon's cries."""

    latest: str
    legacy: str


@dataclass(slots=True)
class DreamWorld:
    front_default: Optional[str]
    front_female: Optional[str]


@dataclass(slots=True)
class Home:
    front_default: Optional[str]
    front_female: Optional[str]
    front_shiny: Optional[str]
    front_shiny_female: Optional[str]


@dataclass(slots=True)
class OfficialArtwork:
    front_default: Optional[str]
    front_shiny: Optional[str]


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


@dataclass(slots=True)
class OtherSprites:
    dream_world: DreamWorld
    home: Home
    official_artwork: OfficialArtwork
    showdown: Showdown


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


@dataclass(slots=True)
class Versions:
    black_white: GenerationSprites


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
    trigger: str = ""
    time_of_day: str = ""
    needs_overworld_rain: bool = False
    turn_upside_down: bool = False

    def __post_init__(self):
        """Validate evolution details fields."""
        if not isinstance(self.trigger, str):
            raise ValueError(f"trigger must be a string, got: {type(self.trigger)}")
        if not isinstance(self.time_of_day, str):
            raise ValueError(
                f"time_of_day must be a string, got: {type(self.time_of_day)}"
            )
        if not isinstance(self.needs_overworld_rain, bool):
            raise ValueError(
                f"needs_overworld_rain must be a boolean, got: {type(self.needs_overworld_rain)}"
            )
        if not isinstance(self.turn_upside_down, bool):
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


# endregion


# region Top-Level Data Structures
@dataclass(slots=True)
class Item:
    """Represents a Pokémon item (e.g., Aguav Berry)."""

    id: int
    name: str
    source_url: str
    cost: int
    fling_power: int
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
        if not isinstance(self.cost, int) or self.cost < 0:
            raise ValueError(f"cost must be a non-negative integer, got: {self.cost}")
        if not isinstance(self.fling_power, int) or self.fling_power < 0:
            raise ValueError(
                f"fling_power must be a non-negative integer, got: {self.fling_power}"
            )


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
        if not isinstance(self.is_main_series, bool):
            raise ValueError(
                f"is_main_series must be a boolean, got: {type(self.is_main_series)}"
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
        if (
            not isinstance(self.priority, int)
            or self.priority < MIN_MOVE_PRIORITY
            or self.priority > MAX_MOVE_PRIORITY
        ):
            raise ValueError(
                f"priority must be an integer between {MIN_MOVE_PRIORITY} and {MAX_MOVE_PRIORITY}, got: {self.priority}"
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
        if (
            not isinstance(self.types, list)
            or not self.types
            or not all(isinstance(t, str) for t in self.types)
        ):
            raise ValueError("types must be a non-empty list of strings")
        if not isinstance(self.height, int) or self.height < 0:
            raise ValueError(
                f"height must be a non-negative integer, got: {self.height}"
            )
        if not isinstance(self.weight, int) or self.weight < 0:
            raise ValueError(
                f"weight must be a non-negative integer, got: {self.weight}"
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


# endregion
