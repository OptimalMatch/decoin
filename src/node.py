#!/usr/bin/env python3

import asyncio
import argparse
import json
from typing import Optional
from blockchain import Blockchain
from consensus import ConsensusManager
from transactions import TransactionBuilder, TransactionValidator
from network import P2PNode

class DeCoinNode:
    def __init__(self, config_file: Optional[str] = None):
        self.config = self.load_config(config_file)
        self.blockchain = Blockchain()
        self.node = P2PNode(
            host=self.config['host'],
            port=self.config['port'],
            blockchain=self.blockchain
        )
        self.consensus_manager = ConsensusManager(self.blockchain)
        self.transaction_builder = TransactionBuilder()
        self.is_mining = False
        self.validator_address = self.config.get('validator_address')
        
    def load_config(self, config_file: Optional[str]) -> dict:
        default_config = {
            'host': '0.0.0.0',
            'port': 8333,
            'validator_address': None,
            'initial_peers': [],
            'mining_enabled': False,
            'api_enabled': True,
            'api_port': 8080
        }
        
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    default_config.update(config)
            except Exception as e:
                print(f"Error loading config file: {e}")
        
        return default_config
    
    async def start(self):
        print(f"Starting DeCoin node on {self.config['host']}:{self.config['port']}")
        
        await self.node.start()
        
        for peer in self.config['initial_peers']:
            asyncio.create_task(self.node.connect_to_peer(peer))
        
        if self.config['mining_enabled'] and self.validator_address:
            self.start_mining()
        
        if self.config['api_enabled']:
            asyncio.create_task(self.start_api())
        
        await asyncio.Event().wait()
    
    def start_mining(self):
        if not self.validator_address:
            print("No validator address configured")
            return
        
        stake = 10000
        success = self.consensus_manager.consensus.register_validator(
            self.validator_address, 
            stake
        )
        
        if success:
            print(f"Started mining with validator {self.validator_address}")
            self.is_mining = True
            asyncio.create_task(self.mining_loop())
        else:
            print("Failed to register as validator")
    
    async def mining_loop(self):
        wait_count = 0
        while self.is_mining:
            # Mine blocks when there are pending transactions or periodically for rewards
            if len(self.blockchain.pending_transactions) >= 1:
                # Simple round-robin mining based on block height
                # This ensures all nodes get a chance to mine
                block_height = len(self.blockchain.chain)
                node_index = {
                    'validator1_address': 0,
                    'validator2_address': 1,
                    'validator3_address': 2,
                    'validator4_address': 3
                }.get(self.validator_address, 0)

                # Each node mines every 4th block (or fewer if there are fewer nodes)
                total_nodes = 4
                expected_miner = block_height % total_nodes
                should_mine = expected_miner == node_index

                # If we've waited too long and have many pending transactions, mine anyway
                if not should_mine and wait_count > 10 and len(self.blockchain.pending_transactions) > 3:
                    print(f"Node {node_index}: Taking over mining after waiting (expected miner {expected_miner} seems offline)")
                    should_mine = True
                    wait_count = 0

                if should_mine:
                    print(f"Node {node_index}: Mining block {block_height} with {len(self.blockchain.pending_transactions)} transactions")
                    wait_count = 0
                    block = self.blockchain.create_block(self.validator_address)
                    
                    if block:
                        success = self.consensus_manager.consensus.mine_block_hybrid(
                            block, 
                            self.validator_address
                        )
                        
                        if success:
                            if self.blockchain.add_block(block):
                                print(f"Mined block {block.index}")
                                await self.node.broadcast_block(block)
                                
                                rewards = self.consensus_manager.consensus.calculate_rewards(block)
                                print(f"Rewards earned: {rewards}")
                else:
                    wait_count += 1
                    if wait_count % 5 == 0:
                        print(f"Node {node_index}: Waiting for miner {expected_miner} (wait count: {wait_count})")
            else:
                wait_count = 0

            await asyncio.sleep(1)
    
    async def start_api(self):
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from api_fastapi import DeCoinAPI
        import uvicorn
        import asyncio
        
        # Create FastAPI app
        api = DeCoinAPI(self)
        
        # Configure uvicorn server
        config = uvicorn.Config(
            app=api.app,
            host="0.0.0.0",
            port=self.config['api_port'],
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        # Run server in background
        asyncio.create_task(server.serve())
        print(f"API server started on port {self.config['api_port']}")
        print(f"Swagger UI available at http://localhost:{self.config['api_port']}/docs")
        print(f"ReDoc available at http://localhost:{self.config['api_port']}/redoc")

async def main():
    parser = argparse.ArgumentParser(description='DeCoin Node')
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host address')
    parser.add_argument('--port', type=int, default=8333, help='Port number')
    parser.add_argument('--mining', action='store_true', help='Enable mining')
    parser.add_argument('--validator', type=str, help='Validator address')
    parser.add_argument('--peers', nargs='+', help='Initial peer addresses')
    
    args = parser.parse_args()
    
    config = {}
    if args.config:
        config['config_file'] = args.config
    
    node = DeCoinNode(config.get('config_file'))
    
    if args.host:
        node.config['host'] = args.host
    if args.port:
        node.config['port'] = args.port
    if args.mining:
        node.config['mining_enabled'] = True
    if args.validator:
        node.config['validator_address'] = args.validator
    if args.peers:
        node.config['initial_peers'] = args.peers
    
    await node.start()

if __name__ == '__main__':
    asyncio.run(main())