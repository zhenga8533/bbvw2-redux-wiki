"""
Service class for managing Pokemon evolution chain operations.

This service encapsulates the logic for updating and manipulating
evolution chains, separating it from the parser implementation.
"""

import copy
from typing import Optional

from src.utils.pokedb_structure import (
    EvolutionChain,
    EvolutionNode,
    EvolutionDetails,
)


class EvolutionService:
    """
    Service for managing Pokemon evolution chain updates.

    Provides methods to update evolution chains with new evolution methods
    while preserving or replacing existing data as needed.
    """

    @staticmethod
    def update_evolution_chain(
        evolution_chain: EvolutionChain,
        pokemon_id: str,
        evolution_id: str,
        evolution_details: EvolutionDetails,
        keep_existing: bool = False,
        already_processed: Optional[set] = None,
    ) -> EvolutionChain:
        """
        Update an evolution chain with new evolution details.

        Args:
            evolution_chain: The evolution chain to update
            pokemon_id: ID of the Pokemon that is evolving
            evolution_id: ID of the evolution target
            evolution_details: The new evolution details
            keep_existing: If True, add to existing methods; if False, replace
            already_processed: Set of pokemon_ids already processed (for internal use)

        Returns:
            EvolutionChain: The updated evolution chain
        """
        if already_processed is None:
            already_processed = set()

        EvolutionService._update_evolution_node(
            evolution_chain,
            pokemon_id,
            evolution_id,
            evolution_details,
            keep_existing,
            already_processed,
        )

        return evolution_chain

    @staticmethod
    def _update_evolution_node(
        evolution_node: EvolutionChain | EvolutionNode,
        pokemon_id: str,
        evolution_id: str,
        evolution_details: EvolutionDetails,
        keep_existing: bool,
        already_processed: set,
    ) -> None:
        """Recursively update evolution nodes."""
        species_name = evolution_node.species_name
        evolves_to = evolution_node.evolves_to
        # Match on the PARENT species (the one that evolves)
        species_match = species_name == pokemon_id

        # Clean out evolution methods (keeps one backup)
        if species_match and not keep_existing and pokemon_id not in already_processed:
            already_processed.add(pokemon_id)
            found = False

            # Use reverse iteration to safely remove items
            for i in range(len(evolves_to) - 1, -1, -1):
                evo = evolves_to[i]
                if evo.species_name != evolution_id:
                    continue

                # Remove all but one existing evolution method
                if found:
                    evolves_to.pop(i)
                else:
                    evo.evolution_details = None
                    found = True

        for evo in evolves_to:
            # Recurse if not the target species
            if not species_match:
                EvolutionService._update_evolution_node(
                    evo,
                    pokemon_id,
                    evolution_id,
                    evolution_details,
                    keep_existing,
                    already_processed,
                )
                continue

            # Skip if not the target evolution
            if evo.species_name != evolution_id:
                continue

            # Update the evolution details
            if evo.evolution_details is None:
                evo.evolution_details = evolution_details
            else:
                node_copy = copy.deepcopy(evo)
                node_copy.evolution_details = evolution_details
                evolves_to.append(node_copy)
            break

    @staticmethod
    def find_evolution_target(
        evolution_chain: EvolutionChain | EvolutionNode, target_id: str
    ) -> Optional[EvolutionNode]:
        """
        Find a specific evolution node in the chain.

        Args:
            evolution_chain: The chain to search
            target_id: The species ID to find

        Returns:
            EvolutionNode if found, None otherwise
        """
        if evolution_chain.species_name == target_id:
            # For EvolutionChain, we need to wrap it conceptually
            # but this is more for validation purposes
            return None

        for evo in evolution_chain.evolves_to:
            if evo.species_name == target_id:
                return evo

            # Recurse into child evolutions
            found = EvolutionService.find_evolution_target(evo, target_id)
            if found:
                return found

        return None
