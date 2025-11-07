"""
Service class for managing Pokemon evolution chain operations.

This service encapsulates the logic for updating and manipulating
evolution chains, separating it from the parser implementation.
"""

import copy
from typing import Optional

from src.utils.core.loader import PokeDBLoader
from src.utils.core.logger import get_logger
from src.utils.data.models import EvolutionChain, EvolutionDetails, EvolutionNode

logger = get_logger(__name__)


class EvolutionService:
    """
    Service for managing Pokemon evolution chain updates.

    Provides methods to update evolution chains with new evolution methods
    while preserving or replacing existing data as needed.
    """

    @staticmethod
    def update_evolution_chain(
        pokemon_id: str,
        evolution_id: str,
        evolution_chain: EvolutionChain,
        evolution_details: EvolutionDetails,
        keep_existing: bool = False,
        processed: Optional[set] = None,
    ) -> EvolutionChain:
        """Update an evolution chain with new evolution details.

        Args:
            pokemon_id (str): ID of the Pokemon that is evolving
            evolution_id (str): ID of the evolution target
            evolution_chain (EvolutionChain): The evolution chain to update
            evolution_details (EvolutionDetails): The new evolution details
            keep_existing (bool, optional): If True, add to existing methods; if False, replace
            processed (Optional[set], optional): Set of pokemon_ids already processed (for internal use)

        Returns:
            EvolutionChain: The updated evolution chain
        """
        if processed is None:
            processed = set()

        mode = "addition" if keep_existing else "replacement"
        logger.debug(
            f"Updating evolution chain: {pokemon_id} -> {evolution_id} (mode: {mode})",
            extra={
                "pokemon_id": pokemon_id,
                "evolution_id": evolution_id,
                "keep_existing": keep_existing,
            },
        )

        EvolutionService._update_evolution_node(
            evolution_chain,
            evolution_chain,
            pokemon_id,
            evolution_id,
            evolution_details,
            keep_existing,
            processed,
        )

        # Save the updated chain to ALL Pokemon in the chain
        all_species = EvolutionService._collect_all_species(evolution_chain)
        for species_id in all_species:
            EvolutionService._save_evolution_node(species_id, evolution_chain)

        logger.debug(f"Successfully updated evolution chain for {pokemon_id}")
        return evolution_chain

    @staticmethod
    def _clean_existing_evolution_methods(
        evolves_to: list[EvolutionNode],
        evolution_id: str,
    ) -> None:
        """Clean out ALL existing evolution methods for the target evolution.

        Args:
            evolves_to (list[EvolutionNode]): List of evolution nodes to clean
            evolution_id (str): The ID of the evolution target to remove
        """
        # Use reverse iteration to safely remove items while iterating
        for i in range(len(evolves_to) - 1, -1, -1):
            evo = evolves_to[i]
            if evo.species_name == evolution_id:
                # Remove all existing evolutions to this target
                evolves_to.pop(i)

    @staticmethod
    def _evolution_details_equal(
        details1: EvolutionDetails,
        details2: EvolutionDetails,
    ) -> bool:
        """Compare two evolution details objects for equality.

        Args:
            details1 (EvolutionDetails): The first evolution details object
            details2 (EvolutionDetails): The second evolution details object

        Returns:
            bool: True if the evolution details are equivalent, False otherwise
        """
        # Compare all relevant fields
        return (
            details1.trigger == details2.trigger
            and details1.min_level == details2.min_level
            and details1.item == details2.item
            and details1.held_item == details2.held_item
            and details1.known_move == details2.known_move
            and details1.known_move_type == details2.known_move_type
            and details1.min_happiness == details2.min_happiness
            and details1.min_affection == details2.min_affection
            and details1.min_beauty == details2.min_beauty
            and details1.time_of_day == details2.time_of_day
            and details1.location == details2.location
            and details1.party_species == details2.party_species
            and details1.party_type == details2.party_type
            and details1.trade_species == details2.trade_species
            and details1.gender == details2.gender
            and details1.relative_physical_stats == details2.relative_physical_stats
            and details1.needs_overworld_rain == details2.needs_overworld_rain
            and details1.turn_upside_down == details2.turn_upside_down
        )

    @staticmethod
    def _apply_evolution_update(
        evolves_to: list[EvolutionNode],
        evolution_id: str,
        evolution_details: EvolutionDetails,
    ) -> None:
        """Apply new evolution details to the target evolution.

        Args:
            evolves_to (list[EvolutionNode]): List of evolution nodes to update
            evolution_id (str): ID of the evolution target
            evolution_details (EvolutionDetails): New evolution details to apply
        """
        # Check if this exact evolution method already exists
        for evo in evolves_to:
            if evo.species_name == evolution_id and evo.evolution_details:
                if EvolutionService._evolution_details_equal(
                    evo.evolution_details, evolution_details
                ):
                    logger.debug(
                        f"Evolution method already exists for {evolution_id}, skipping duplicate"
                    )
                    return

        # Check if an evolution to the target already exists (with different method)
        for evo in evolves_to:
            if evo.species_name == evolution_id:
                # Evolution exists - add as alternate method (keep_existing=True case)
                node_copy = copy.deepcopy(evo)
                node_copy.evolution_details = evolution_details
                evolves_to.append(node_copy)
                logger.debug(f"Added alternate evolution method for {evolution_id}")
                return

        # No evolution to the target exists - create a new one
        new_node = EvolutionNode(
            species_name=evolution_id,
            evolution_details=evolution_details,
            evolves_to=[],
        )
        evolves_to.append(new_node)
        logger.debug(f"Created new evolution node for {evolution_id}")

    @staticmethod
    def _update_evolution_node(
        original_chain: EvolutionChain,
        evolution_node: EvolutionChain | EvolutionNode,
        pokemon_id: str,
        evolution_id: str,
        evolution_details: EvolutionDetails,
        keep_existing: bool,
        processed: set,
    ) -> None:
        """Recursively update evolution nodes in the chain.

        Args:
            original_chain (EvolutionChain): The root evolution chain
            evolution_node (EvolutionChain | EvolutionNode): The current evolution node
            pokemon_id (str): The ID of the Pokemon being evolved
            evolution_id (str): The ID of the evolution target
            evolution_details (EvolutionDetails): The new evolution details to apply
            keep_existing (bool): If True, keep existing evolution methods; if False, replace them
            processed (set): Set of processed Pokemon IDs
        """
        species_name = evolution_node.species_name
        evolves_to = evolution_node.evolves_to

        # Check if this node is the Pokemon we're looking for
        species_match = species_name == pokemon_id

        # Clean out old evolution methods if we're replacing (not adding)
        if species_match and not keep_existing and pokemon_id not in processed:
            processed.add(pokemon_id)
            EvolutionService._clean_existing_evolution_methods(evolves_to, evolution_id)

        # Process each evolution path
        update_applied = False
        for evo in evolves_to:
            # If this isn't the target Pokemon, recurse deeper
            if not species_match:
                EvolutionService._update_evolution_node(
                    original_chain,
                    evo,
                    pokemon_id,
                    evolution_id,
                    evolution_details,
                    keep_existing,
                    processed,
                )
                continue

            # Skip if this evolution isn't our target
            if evo.species_name != evolution_id:
                continue

            # Apply the evolution update
            EvolutionService._apply_evolution_update(
                evolves_to, evolution_id, evolution_details
            )
            update_applied = True
            break

        # If we found the right Pokemon but didn't apply an update
        # (because the target evolution doesn't exist), apply it now
        if species_match and not update_applied:
            EvolutionService._apply_evolution_update(
                evolves_to, evolution_id, evolution_details
            )

    @staticmethod
    def _collect_all_species(node: EvolutionChain | EvolutionNode) -> set[str]:
        """Collect all species IDs in an evolution chain.

        Args:
            node (EvolutionChain | EvolutionNode): The evolution chain or node to traverse

        Returns:
            set[str]: A set of all species IDs in the chain
        """
        species_ids = {node.species_name}
        for evolution in node.evolves_to:
            species_ids.update(EvolutionService._collect_all_species(evolution))
        return species_ids

    @staticmethod
    def _save_evolution_node(pokemon_id: str, evolution_chain: EvolutionChain):
        """Save the evolution chain for a specific Pokemon.

        Args:
            pokemon_id (str): ID of the Pokemon to save the evolution chain for
            evolution_chain (EvolutionChain): The evolution chain to save
        """
        # Get all form files and the pre-loaded base Pokemon object
        form_files, base_pokemon_data = PokeDBLoader.find_all_form_files(pokemon_id)

        if not form_files:
            logger.warning(
                f"No form files found for {pokemon_id}, cannot save evolution chain."
            )
            return

        # Save to all form files
        for form_name, category in form_files:
            try:
                logger.debug(
                    f"Saving evolution chain for {pokemon_id} form: {form_name} (category: {category})"
                )

                # If we are processing the base form that we already loaded, reuse the object.
                # Otherwise, load the specific form data from disk.
                if base_pokemon_data and form_name == base_pokemon_data.name:
                    pokemon_data = base_pokemon_data
                else:
                    pokemon_data = PokeDBLoader.load_pokemon(
                        form_name, subfolder=category
                    )
                    if not pokemon_data:
                        logger.warning(
                            f"Failed to load form file during save: {form_name} in {category}, skipping"
                        )
                        continue

                # Update the evolution chain and save
                pokemon_data.evolution_chain = evolution_chain
                PokeDBLoader.save_pokemon(form_name, pokemon_data, subfolder=category)

            except FileNotFoundError:
                logger.warning(
                    f"Form file not found during save: {form_name} in {category}, skipping"
                )
