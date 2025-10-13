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
from typing import Any, Dict, List, Literal, Optional


# region Helper Classes for Pokémon Structure
@dataclass
class PokemonAbility:
    """Represents an ability a Pokémon can have."""

    name: str
    is_hidden: bool
    slot: int

    def __post_init__(self):
        """Validate ability fields."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"Ability name must be a non-empty string, got: {self.name}")
        if not isinstance(self.is_hidden, bool):
            raise ValueError(f"is_hidden must be a boolean, got: {type(self.is_hidden)}")
        if not isinstance(self.slot, int) or self.slot < 1 or self.slot > 3:
            raise ValueError(f"Ability slot must be an integer between 1 and 3, got: {self.slot}")


@dataclass
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
        stat_fields = ['hp', 'attack', 'defense', 'special_attack', 'special_defense', 'speed']
        for field_name in stat_fields:
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer, got: {value}")


@dataclass
class EVYield:
    """Represents the effort value yield of a Pokémon."""

    stat: str
    effort: int

    def __post_init__(self):
        """Validate EV yield fields."""
        valid_stats = {'hp', 'attack', 'defense', 'special_attack', 'special_defense', 'speed'}
        if not isinstance(self.stat, str) or self.stat not in valid_stats:
            raise ValueError(f"stat must be one of {valid_stats}, got: {self.stat}")
        if not isinstance(self.effort, int) or self.effort < 0 or self.effort > 3:
            raise ValueError(f"effort must be an integer between 0 and 3, got: {self.effort}")


@dataclass
class Cries:
    """Contains URLs to a Pokémon's cries."""

    latest: str
    legacy: str


@dataclass
class DreamWorld:
    front_default: Optional[str]
    front_female: Optional[str]


@dataclass
class Home:
    front_default: Optional[str]
    front_female: Optional[str]
    front_shiny: Optional[str]
    front_shiny_female: Optional[str]


@dataclass
class OfficialArtwork:
    front_default: Optional[str]
    front_shiny: Optional[str]


@dataclass
class Showdown:
    back_default: Optional[str]
    back_female: Optional[str]
    back_shiny: Optional[str]
    back_shiny_female: Optional[str]
    front_default: Optional[str]
    front_female: Optional[str]
    front_shiny: Optional[str]
    front_shiny_female: Optional[str]


@dataclass
class OtherSprites:
    dream_world: DreamWorld
    home: Home
    official_artwork: OfficialArtwork
    showdown: Showdown


@dataclass
class AnimatedSprites:
    back_default: Optional[str]
    back_female: Optional[str]
    back_shiny: Optional[str]
    back_shiny_female: Optional[str]
    front_default: Optional[str]
    front_female: Optional[str]
    front_shiny: Optional[str]
    front_shiny_female: Optional[str]


@dataclass
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


@dataclass
class Versions:
    black_white: GenerationSprites = field(metadata={"data_key": "black-white"})


@dataclass
class Sprites:
    """Contains URLs to all Pokémon sprites."""

    back_default: Optional[str]
    back_shiny: Optional[str]
    front_default: Optional[str]
    front_shiny: Optional[str]
    other: OtherSprites
    versions: Versions


@dataclass
class EvolutionDetails:
    item: Optional[str] = None
    gender: Optional[int] = None
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
            raise ValueError(f"time_of_day must be a string, got: {type(self.time_of_day)}")
        if not isinstance(self.needs_overworld_rain, bool):
            raise ValueError(f"needs_overworld_rain must be a boolean, got: {type(self.needs_overworld_rain)}")
        if not isinstance(self.turn_upside_down, bool):
            raise ValueError(f"turn_upside_down must be a boolean, got: {type(self.turn_upside_down)}")

        # Validate optional integer fields with reasonable ranges
        if self.gender is not None and (not isinstance(self.gender, int) or self.gender not in (1, 2)):
            raise ValueError(f"gender must be None or 1 (female) or 2 (male), got: {self.gender}")
        if self.min_level is not None and (not isinstance(self.min_level, int) or self.min_level < 1 or self.min_level > 100):
            raise ValueError(f"min_level must be None or between 1 and 100, got: {self.min_level}")
        if self.min_happiness is not None and (not isinstance(self.min_happiness, int) or self.min_happiness < 0 or self.min_happiness > 255):
            raise ValueError(f"min_happiness must be None or between 0 and 255, got: {self.min_happiness}")
        if self.min_beauty is not None and (not isinstance(self.min_beauty, int) or self.min_beauty < 0 or self.min_beauty > 255):
            raise ValueError(f"min_beauty must be None or between 0 and 255, got: {self.min_beauty}")
        if self.min_affection is not None and (not isinstance(self.min_affection, int) or self.min_affection < 0 or self.min_affection > 255):
            raise ValueError(f"min_affection must be None or between 0 and 255, got: {self.min_affection}")
        if self.relative_physical_stats is not None and (not isinstance(self.relative_physical_stats, int) or self.relative_physical_stats not in (-1, 0, 1)):
            raise ValueError(f"relative_physical_stats must be None, -1, 0, or 1, got: {self.relative_physical_stats}")


@dataclass
class EvolutionNode:
    species_name: str
    evolves_to: List["EvolutionNode"]
    evolution_details: Optional[EvolutionDetails] = None

    def __post_init__(self):
        """Validate evolution node fields."""
        if not isinstance(self.species_name, str) or not self.species_name.strip():
            raise ValueError(f"species_name must be a non-empty string, got: {self.species_name}")
        if not isinstance(self.evolves_to, list):
            raise ValueError("evolves_to must be a list")


@dataclass
class EvolutionChain:
    species_name: str = ""
    evolves_to: List[EvolutionNode] = field(default_factory=list)

    def __post_init__(self):
        """Validate evolution chain fields."""
        if not isinstance(self.species_name, str):
            raise ValueError(f"species_name must be a string, got: {type(self.species_name)}")
        if not isinstance(self.evolves_to, list):
            raise ValueError("evolves_to must be a list")


@dataclass
class MoveLearn:
    name: str
    level_learned_at: int
    version_groups: List[str]

    def __post_init__(self):
        """Validate move learn fields."""
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"name must be a non-empty string, got: {self.name}")
        if not isinstance(self.level_learned_at, int) or self.level_learned_at < 0:
            raise ValueError(f"level_learned_at must be a non-negative integer, got: {self.level_learned_at}")
        if not isinstance(self.version_groups, list) or not all(isinstance(vg, str) for vg in self.version_groups):
            raise ValueError("version_groups must be a list of strings")


@dataclass
class PokemonMoves:
    tutor: List[MoveLearn]
    machine: List[MoveLearn]
    level_up: List[MoveLearn] = field(metadata={"data_key": "level-up"})


# endregion


# region Helper Classes for Move Structure
@dataclass
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
        for field_name in ['min_hits', 'max_hits', 'min_turns', 'max_turns']:
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, int) or value < 0):
                raise ValueError(f"{field_name} must be None or a non-negative integer, got: {value}")

        # Validate percentage/chance fields (0-100)
        for field_name in ['crit_rate', 'ailment_chance', 'flinch_chance', 'stat_chance']:
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 0 or value > 100:
                raise ValueError(f"{field_name} must be an integer between 0 and 100, got: {value}")

        # Validate drain and healing (-100 to 100, can be negative for drain)
        for field_name in ['drain', 'healing']:
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < -100 or value > 100:
                raise ValueError(f"{field_name} must be an integer between -100 and 100, got: {value}")


# endregion


# region Top-Level Data Structures
@dataclass
class Item:
    """Represents a Pokémon item (e.g., Aguav Berry)."""

    id: int
    name: str
    source_url: str
    cost: int
    fling_power: int
    fling_effect: Optional[str]
    attributes: List[str]
    category: str
    effect: str
    short_effect: str
    flavor_text: Dict[str, str]
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
            raise ValueError(f"fling_power must be a non-negative integer, got: {self.fling_power}")


@dataclass
class Ability:
    """Represents a Pokémon ability (e.g., Anticipation)."""

    id: int
    name: str
    source_url: str
    is_main_series: bool
    effect: Dict[str, str]
    short_effect: str
    flavor_text: Dict[str, str]

    def __post_init__(self):
        """Validate ability fields."""
        if not isinstance(self.id, int) or self.id <= 0:
            raise ValueError(f"id must be a positive integer, got: {self.id}")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"name must be a non-empty string, got: {self.name}")
        if not isinstance(self.is_main_series, bool):
            raise ValueError(f"is_main_series must be a boolean, got: {type(self.is_main_series)}")


@dataclass
class Move:
    """Represents a Pokémon move (e.g., Beat Up)."""

    id: int
    name: str
    source_url: str
    accuracy: Dict[str, int]
    power: Dict[str, Optional[int]]
    pp: Dict[str, int]
    priority: int
    damage_class: str
    type: Dict[str, str]
    target: str
    generation: str
    effect_chance: Dict[str, Optional[int]]
    effect: Dict[str, str]
    short_effect: Dict[str, str]
    flavor_text: Dict[str, str]
    stat_changes: List[Any]
    machine: Optional[Any]
    metadata: MoveMetadata

    def __post_init__(self):
        """Validate move fields."""
        if not isinstance(self.id, int) or self.id <= 0:
            raise ValueError(f"id must be a positive integer, got: {self.id}")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"name must be a non-empty string, got: {self.name}")
        if not isinstance(self.priority, int) or self.priority < -7 or self.priority > 5:
            raise ValueError(f"priority must be an integer between -7 and 5, got: {self.priority}")


@dataclass
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
            raise ValueError(f"category must be one of {valid_categories}, got: {self.category}")


@dataclass
class Pokemon:
    """Represents a Pokémon (e.g., Aggron)."""

    id: int
    name: str
    species: str
    is_default: bool
    source_url: str
    types: List[str]
    abilities: List[PokemonAbility]
    stats: Stats
    ev_yield: List[EVYield]
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
    pokedex_numbers: Dict[str, int]
    color: str
    shape: str
    egg_groups: List[str]
    flavor_text: Dict[str, str]
    genus: str
    generation: str
    evolution_chain: EvolutionChain
    held_items: Dict[str, Dict[str, int]]
    moves: PokemonMoves
    forms: List[Form]

    def __post_init__(self):
        """Validate Pokemon fields."""
        if not isinstance(self.id, int) or self.id <= 0:
            raise ValueError(f"id must be a positive integer, got: {self.id}")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"name must be a non-empty string, got: {self.name}")
        if not isinstance(self.species, str) or not self.species.strip():
            raise ValueError(f"species must be a non-empty string, got: {self.species}")
        if not isinstance(self.is_default, bool):
            raise ValueError(f"is_default must be a boolean, got: {type(self.is_default)}")
        if not isinstance(self.types, list) or not self.types or not all(isinstance(t, str) for t in self.types):
            raise ValueError("types must be a non-empty list of strings")
        if not isinstance(self.height, int) or self.height < 0:
            raise ValueError(f"height must be a non-negative integer, got: {self.height}")
        if not isinstance(self.weight, int) or self.weight < 0:
            raise ValueError(f"weight must be a non-negative integer, got: {self.weight}")
        if not isinstance(self.base_experience, int) or self.base_experience < 0:
            raise ValueError(f"base_experience must be a non-negative integer, got: {self.base_experience}")
        if not isinstance(self.base_happiness, int) or self.base_happiness < 0 or self.base_happiness > 255:
            raise ValueError(f"base_happiness must be between 0 and 255, got: {self.base_happiness}")
        if not isinstance(self.capture_rate, int) or self.capture_rate < 0 or self.capture_rate > 255:
            raise ValueError(f"capture_rate must be between 0 and 255, got: {self.capture_rate}")
        if not isinstance(self.hatch_counter, int) or self.hatch_counter < 0:
            raise ValueError(f"hatch_counter must be a non-negative integer, got: {self.hatch_counter}")
        if not isinstance(self.gender_rate, int) or self.gender_rate < -1 or self.gender_rate > 8:
            raise ValueError(f"gender_rate must be between -1 and 8, got: {self.gender_rate}")


# endregion
