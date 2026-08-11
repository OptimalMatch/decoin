"""Hybrid consensus scoring tests.

Added with the book-repairs pass: consensus.py shipped with no runnable tests
(test_consensus.py.disabled targets classes that never existed), so the scoring
bug — a boolean multiplied by a weight, which made the "hybrid" score always
clear its threshold — had no coverage. These lock the repaired behaviour.
"""
import pytest

from blockchain import Blockchain
from consensus import HybridConsensus


def _mined_block(blockchain, validator):
    block = blockchain.create_block(validator)
    block.mine_block(blockchain.difficulty)
    return block


class TestHybridScoring:
    def test_score_combines_stake_and_work(self):
        bc = Blockchain()
        hc = HybridConsensus(bc)
        hc.register_validator("rich", 8000)
        hc.register_validator("poor", 2000)
        block = _mined_block(bc, "rich")

        ok_rich, score_rich = hc.validate_block_hybrid(block, "rich")
        ok_poor, score_poor = hc.validate_block_hybrid(block, "poor")

        # Both pass the hard gates (stake >= required, valid proof-of-work)...
        assert ok_rich and ok_poor
        # ...but stake is GRADED now, not a boolean 0.7: more stake, higher score.
        assert score_rich > score_poor
        # And the work component is real: a positive contribution, below 1.
        assert 0 < score_poor < 1

    def test_below_minimum_stake_is_not_registered(self):
        bc = Blockchain()
        hc = HybridConsensus(bc)
        assert hc.register_validator("tiny", 500) is False
        assert hc.register_validator("ok", 2000) is True

    def test_mine_block_hybrid_produces_an_addable_block(self):
        bc = Blockchain()
        hc = HybridConsensus(bc)
        hc.register_validator("v", 5000)

        block = bc.create_block("v")
        assert hc.mine_block_hybrid(block, "v", timeout=5) is True
        # The mined block satisfies the chain's own validation rules.
        assert bc.add_block(block) is True
        assert len(bc.chain) == 2
