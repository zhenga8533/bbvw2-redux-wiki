"""
Domain models for the wiki generator.

This module exports all data structures (dataclasses) that represent
the domain entities: Pokemon, moves, items, abilities, and their related structures.
"""

from .pokedb import (
    # Helper/Map models
    GameVersionStringMap,
    GameVersionIntMap,
    # Pokemon-related models
    Pokemon,
    PokemonAbility,
    PokemonMoves,
    Stats,
    EVYield,
    Cries,
    Sprites,
    Form,
    # Evolution models
    EvolutionChain,
    EvolutionNode,
    EvolutionDetails,
    Gender,
    # Move-related models
    Move,
    MoveLearn,
    MoveMetadata,
    StatChange,
    # Item models
    Item,
    # Ability models
    Ability,
    # Sprite-related models
    OtherSprites,
    AnimatedSprites,
    GenerationSprites,
    SpriteVersions,  # Renamed from Versions
    DreamWorld,
    Home,
    OfficialArtwork,
    Showdown,
)

__all__ = [
    # Helper/Map models
    "GameVersionStringMap",
    "GameVersionIntMap",
    # Pokemon-related models
    "Pokemon",
    "PokemonAbility",
    "PokemonMoves",
    "Stats",
    "EVYield",
    "Cries",
    "Sprites",
    "Form",
    # Evolution models
    "EvolutionChain",
    "EvolutionNode",
    "EvolutionDetails",
    "Gender",
    # Move-related models
    "Move",
    "MoveLearn",
    "MoveMetadata",
    "StatChange",
    # Item models
    "Item",
    # Ability models
    "Ability",
    # Sprite-related models
    "OtherSprites",
    "AnimatedSprites",
    "GenerationSprites",
    "SpriteVersions",
    "DreamWorld",
    "Home",
    "OfficialArtwork",
    "Showdown",
]
