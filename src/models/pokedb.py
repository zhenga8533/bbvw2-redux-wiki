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


@dataclass
class Stats:
    """Represents the base stats of a Pokémon."""

    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int


@dataclass
class EVYield:
    """Represents the effort value yield of a Pokémon."""

    stat: str
    effort: int


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


@dataclass
class EvolutionNode:
    species_name: str
    evolves_to: List["EvolutionNode"]
    evolution_details: Optional[EvolutionDetails] = None


@dataclass
class EvolutionChain:
    species_name: str = ""
    evolves_to: List[EvolutionNode] = field(default_factory=list)


@dataclass
class MoveLearn:
    name: str
    level_learned_at: int
    version_groups: List[str]


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


@dataclass
class Form:
    """Represents a Pokémon form (e.g., Mega Charizard X)."""

    name: str
    category: Literal["default", "cosmetic", "transformation", "variant"]


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


# endregion
