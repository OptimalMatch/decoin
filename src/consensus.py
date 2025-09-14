import hashlib
import random
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from blockchain import Block, Blockchain, Transaction

@dataclass
class Validator:
    address: str
    stake: float
    reputation: float = 1.0
    blocks_validated: int = 0
    last_validation_time: float = 0
    is_active: bool = True
    
    def calculate_weight(self) -> float:
        stake_weight = self.stake * 0.7
        reputation_weight = self.reputation * 0.3
        return stake_weight + reputation_weight

class HybridConsensus:
    def __init__(self, blockchain: Blockchain):
        self.blockchain = blockchain
        self.validators: Dict[str, Validator] = {}
        self.minimum_stake = 1000
        self.stake_weight = 0.7
        self.work_weight = 0.3
        self.block_time = 2  # Reduced to match blockchain setting
        self.difficulty_adjustment_interval = 100
        self.max_validators_per_round = 10
        
    def register_validator(self, address: str, stake: float) -> bool:
        if stake < self.minimum_stake:
            return False

        if address in self.validators:
            self.validators[address].stake += stake
        else:
            self.validators[address] = Validator(
                address=address,
                stake=stake
            )
        print(f"Registered validator {address} with stake {stake}. Total validators: {len(self.validators)}")
        return True
    
    def unregister_validator(self, address: str) -> float:
        if address not in self.validators:
            return 0
        
        stake = self.validators[address].stake
        del self.validators[address]
        return stake
    
    def select_validator(self) -> Optional[str]:
        active_validators = [
            v for v in self.validators.values()
            if v.is_active
        ]

        if not active_validators:
            return None

        # Sort validators by address for consistent ordering across all nodes
        active_validators.sort(key=lambda v: v.address)

        # Use block height for deterministic round-robin
        block_height = len(self.blockchain.chain)

        # Simple round-robin based on block height
        # This ensures fair distribution and consistency across all nodes
        selected_index = block_height % len(active_validators)
        return active_validators[selected_index].address
    
    def validate_block_hybrid(self, block: Block, validator_address: str) -> Tuple[bool, float]:
        if validator_address not in self.validators:
            return False, 0
        
        validator = self.validators[validator_address]
        
        stake_valid = self.validate_stake(validator, block)
        if not stake_valid:
            return False, 0
        
        work_valid, work_score = self.validate_work(block)
        if not work_valid:
            return False, 0
        
        total_score = (stake_valid * self.stake_weight) + (work_score * self.work_weight)
        
        if total_score >= 0.5:
            validator.blocks_validated += 1
            validator.last_validation_time = time.time()
            validator.reputation = min(2.0, validator.reputation * 1.01)
            return True, total_score
        
        return False, total_score
    
    def validate_stake(self, validator: Validator, block: Block) -> bool:
        required_stake = self.calculate_required_stake(block)
        return validator.stake >= required_stake
    
    def calculate_required_stake(self, block: Block) -> float:
        base_stake = self.minimum_stake
        
        tx_value = sum(tx.amount for tx in block.transactions)
        stake_multiplier = 1 + (tx_value / 100000)
        
        return base_stake * stake_multiplier
    
    def validate_work(self, block: Block) -> Tuple[bool, float]:
        target = '0' * self.blockchain.difficulty
        if not block.block_hash.startswith(target):
            return False, 0
        
        leading_zeros = len(block.block_hash) - len(block.block_hash.lstrip('0'))
        work_score = leading_zeros / 64
        
        return True, work_score
    
    def mine_block_hybrid(self, block: Block, validator_address: str, timeout: int = 5) -> bool:
        if validator_address not in self.validators:
            return False
        
        validator = self.validators[validator_address]
        block.validator = validator_address
        block.stake_weight = self.stake_weight
        block.work_weight = self.work_weight
        
        start_time = time.time()
        nonce = 0
        
        base_difficulty = max(1, self.blockchain.difficulty - 2)
        
        while time.time() - start_time < timeout:
            block.nonce = nonce
            block.block_hash = block.calculate_hash()
            
            if block.block_hash.startswith('0' * base_difficulty):
                is_valid, score = self.validate_block_hybrid(block, validator_address)
                if is_valid:
                    return True
            
            nonce += 1
        
        return False
    
    def adjust_difficulty(self) -> None:
        if len(self.blockchain.chain) % self.difficulty_adjustment_interval != 0:
            return
        
        recent_blocks = self.blockchain.chain[-self.difficulty_adjustment_interval:]
        if len(recent_blocks) < 2:
            return
        
        time_taken = recent_blocks[-1].timestamp - recent_blocks[0].timestamp
        expected_time = self.block_time * len(recent_blocks)
        
        if time_taken < expected_time * 0.5:
            self.blockchain.difficulty += 1
        elif time_taken > expected_time * 2:
            self.blockchain.difficulty = max(1, self.blockchain.difficulty - 1)
    
    def calculate_rewards(self, block: Block) -> Dict[str, float]:
        rewards = {}
        
        base_reward = 50
        halvings = len(self.blockchain.chain) // 210000
        block_reward = base_reward / (2 ** halvings)
        
        tx_fees = sum(
            tx.metadata.get('fee', 0) for tx in block.transactions
        )
        
        total_reward = block_reward + tx_fees
        
        if block.validator:
            validator_reward = total_reward * 0.7
            rewards[block.validator] = validator_reward
            
            participating_validators = self.get_participating_validators(block)
            if participating_validators:
                participation_reward = total_reward * 0.3 / len(participating_validators)
                for v in participating_validators:
                    rewards[v] = rewards.get(v, 0) + participation_reward
        
        return rewards
    
    def get_participating_validators(self, block: Block) -> List[str]:
        participation_window = 300
        current_time = block.timestamp
        
        return [
            v.address for v in self.validators.values()
            if v.is_active and 
            abs(v.last_validation_time - current_time) < participation_window
        ]
    
    def slash_validator(self, address: str, reason: str) -> float:
        if address not in self.validators:
            return 0
        
        validator = self.validators[address]
        
        slash_percentages = {
            'double_signing': 0.1,
            'invalid_block': 0.05,
            'offline': 0.01,
            'malicious': 0.5
        }
        
        slash_percentage = slash_percentages.get(reason, 0.01)
        slash_amount = validator.stake * slash_percentage
        
        validator.stake -= slash_amount
        validator.reputation *= 0.5
        
        if validator.stake < self.minimum_stake:
            self.unregister_validator(address)
        
        return slash_amount

class ConsensusManager:
    def __init__(self, blockchain: Blockchain):
        self.blockchain = blockchain
        self.consensus = HybridConsensus(blockchain)
        self.is_mining = False
        self.min_transactions_for_block = 1  # Mine immediately when transactions arrive
        self.max_wait_time = 0.1  # Minimal wait time for maximum throughput
        self.last_block_time = time.time()
        
    def start_validation(self, validator_address: str) -> None:
        self.is_mining = True

        while self.is_mining:
            # Implement transaction batching
            current_time = time.time()
            time_since_last = current_time - self.last_block_time
            pending_count = len(self.blockchain.pending_transactions)

            # Wait for batch or timeout
            should_mine = (
                pending_count >= self.min_transactions_for_block or
                (pending_count > 0 and time_since_last >= self.max_wait_time)
            )

            if not should_mine:
                time.sleep(0.01)  # Minimal sleep for maximum responsiveness
                continue

            selected_validator = self.consensus.select_validator()
            if selected_validator != validator_address:
                time.sleep(0.01)  # Minimal sleep for maximum responsiveness
                continue

            block = self.blockchain.create_block(validator_address)
            if not block:
                continue

            success = self.consensus.mine_block_hybrid(block, validator_address)
            if success:
                if self.blockchain.add_block(block):
                    rewards = self.consensus.calculate_rewards(block)
                    tx_count = len(block.transactions) - 1  # Exclude coinbase
                    print(f"Block {block.index} mined with {tx_count} transactions! Rewards: {rewards}")
                    self.consensus.adjust_difficulty()
                    self.last_block_time = current_time

            time.sleep(0.01)  # Minimal sleep for maximum responsiveness
    
    def stop_validation(self) -> None:
        self.is_mining = False