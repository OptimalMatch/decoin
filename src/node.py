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
        while self.is_mining:
            if len(self.blockchain.pending_transactions) >= 5:
                selected = self.consensus_manager.consensus.select_validator()
                
                if selected == self.validator_address:
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
            
            await asyncio.sleep(1)
    
    async def start_api(self):
        from aiohttp import web
        
        app = web.Application()
        app.router.add_get('/status', self.handle_status)
        app.router.add_get('/blockchain', self.handle_get_blockchain)
        app.router.add_post('/transaction', self.handle_new_transaction)
        app.router.add_get('/balance/{address}', self.handle_get_balance)
        app.router.add_get('/block/{index}', self.handle_get_block)
        app.router.add_get('/transaction/{tx_hash}', self.handle_get_transaction)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.config['api_port'])
        await site.start()
        print(f"API server started on port {self.config['api_port']}")
    
    async def handle_status(self, request):
        from aiohttp import web
        
        status = {
            'node_id': self.node.node_id,
            'chain_height': len(self.blockchain.chain),
            'pending_transactions': len(self.blockchain.pending_transactions),
            'connected_peers': len(self.node.peers),
            'is_mining': self.is_mining,
            'difficulty': self.blockchain.difficulty
        }
        return web.json_response(status)
    
    async def handle_get_blockchain(self, request):
        from aiohttp import web
        
        return web.json_response(self.blockchain.to_dict())
    
    async def handle_new_transaction(self, request):
        from aiohttp import web
        
        try:
            data = await request.json()
            
            tx_type = data.get('type', 'standard')
            
            if tx_type == 'standard':
                tx = self.transaction_builder.create_standard_transaction(
                    sender=data['sender'],
                    recipient=data['recipient'],
                    amount=data['amount'],
                    fee=data.get('fee', 0.001),
                    metadata=data.get('metadata', {})
                )
            elif tx_type == 'multisig':
                tx = self.transaction_builder.create_multisig_transaction(
                    senders=data['senders'],
                    recipient=data['recipient'],
                    amount=data['amount'],
                    required_signatures=data['required_signatures'],
                    fee=data.get('fee', 0.002)
                )
            elif tx_type == 'time_locked':
                tx = self.transaction_builder.create_time_locked_transaction(
                    sender=data['sender'],
                    recipient=data['recipient'],
                    amount=data['amount'],
                    unlock_time=data['unlock_time'],
                    fee=data.get('fee', 0.001)
                )
            elif tx_type == 'data_storage':
                tx = self.transaction_builder.create_data_storage_transaction(
                    sender=data['sender'],
                    data=data['data'],
                    fee=data.get('fee', 0.005)
                )
            else:
                return web.json_response({'error': 'Invalid transaction type'}, status=400)
            
            if self.blockchain.add_transaction(tx):
                await self.node.broadcast_transaction(tx)
                return web.json_response({'tx_hash': tx.tx_hash, 'status': 'pending'})
            else:
                return web.json_response({'error': 'Invalid transaction'}, status=400)
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=400)
    
    async def handle_get_balance(self, request):
        from aiohttp import web
        
        address = request.match_info['address']
        balance = self.blockchain.get_balance(address)
        return web.json_response({'address': address, 'balance': balance})
    
    async def handle_get_block(self, request):
        from aiohttp import web
        
        try:
            index = int(request.match_info['index'])
            if 0 <= index < len(self.blockchain.chain):
                block = self.blockchain.chain[index]
                return web.json_response(block.to_dict())
            else:
                return web.json_response({'error': 'Block not found'}, status=404)
        except ValueError:
            return web.json_response({'error': 'Invalid block index'}, status=400)
    
    async def handle_get_transaction(self, request):
        from aiohttp import web
        
        tx_hash = request.match_info['tx_hash']
        
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if tx.tx_hash == tx_hash:
                    return web.json_response({
                        'transaction': tx.to_dict(),
                        'block_index': block.index,
                        'confirmations': len(self.blockchain.chain) - block.index
                    })
        
        for tx in self.blockchain.pending_transactions:
            if tx.tx_hash == tx_hash:
                return web.json_response({
                    'transaction': tx.to_dict(),
                    'status': 'pending'
                })
        
        return web.json_response({'error': 'Transaction not found'}, status=404)

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