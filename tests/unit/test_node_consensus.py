"""The node and its P2P layer must share ONE consensus/validator registry.

Previously each held its own ConsensusManager, so a validator registered over
the network was invisible to the mining loop and vice versa — every node saw
only itself as a validator and the testnet never reached consensus.
"""
import pytest

from node import DeCoinNode


class TestSharedConsensusRegistry:
    def test_node_and_p2p_share_one_consensus_manager(self):
        node = DeCoinNode()
        assert node.consensus_manager is node.node.consensus_manager

    def test_validator_registered_over_the_network_is_visible_to_mining(self):
        node = DeCoinNode()
        # Simulate a registration arriving through the P2P layer.
        node.node.consensus_manager.consensus.register_validator("DECvalidator", 5000)
        # The mining path reads node.consensus_manager — it must see it.
        assert "DECvalidator" in node.consensus_manager.consensus.validators

    def test_validator_registered_by_the_node_is_visible_to_the_network(self):
        node = DeCoinNode()
        node.consensus_manager.consensus.register_validator("DECminer", 5000)
        assert "DECminer" in node.node.consensus_manager.consensus.validators
