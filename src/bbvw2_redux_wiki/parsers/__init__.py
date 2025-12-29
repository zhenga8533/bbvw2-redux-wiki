"""
Parser package for processing documentation files.
"""

from .evolution_changes_parser import EvolutionChangesParser
from .gift_pokemon_parser import GiftPokemonParser
from .item_changes_parser import ItemChangesParser
from .legendary_locations_parser import LegendaryLocationsParser
from .move_changes_parser import MoveChangesParser
from .pokemon_changes_parser import PokemonChangesParser
from .trade_changes_parser import TradeChangesParser
from .trainer_changes_parser import TrainerChangesParser
from .type_changes_parser import TypeChangesParser
from .wild_area_changes_parser import WildAreaChangesParser

__all__ = [
    "EvolutionChangesParser",
    "GiftPokemonParser",
    "ItemChangesParser",
    "LegendaryLocationsParser",
    "MoveChangesParser",
    "PokemonChangesParser",
    "TradeChangesParser",
    "TrainerChangesParser",
    "TypeChangesParser",
    "WildAreaChangesParser",
]
