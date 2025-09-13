import asyncio
import json
import hashlib
import time
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
from blockchain import Block, Transaction, Blockchain
from consensus import ConsensusManager
from transactions import TransactionValidator, TransactionPool

class MessageType(Enum):
    PING = "ping"
    PONG = "pong"
    GET_PEERS = "get_peers"
    PEERS = "peers"
    GET_BLOCKS = "get_blocks"
    BLOCKS = "blocks"
    NEW_BLOCK = "new_block"
    NEW_TRANSACTION = "new_transaction"
    GET_CHAIN = "get_chain"
    CHAIN = "chain"
    GET_MEMPOOL = "get_mempool"
    MEMPOOL = "mempool"
    VERSION = "version"
    VERACK = "verack"
    REGISTER_VALIDATOR = "register_validator"
    VALIDATOR_LIST = "validator_list"
    GET_VALIDATORS = "get_validators"

@dataclass
class Message:
    type: MessageType
    data: Any
    timestamp: float = None
    sender: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_json(self) -> str:
        return json.dumps({
            'type': self.type.value,
            'data': self.data,
            'timestamp': self.timestamp,
            'sender': self.sender
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        data = json.loads(json_str)
        return cls(
            type=MessageType(data['type']),
            data=data['data'],
            timestamp=data.get('timestamp'),
            sender=data.get('sender')
        )

class PeerConnection:
    def __init__(self, websocket, address: str):
        self.websocket = websocket
        self.address = address
        self.version = None
        self.last_seen = time.time()
        self.is_alive = True
        
    async def send_message(self, message: Message) -> None:
        try:
            await self.websocket.send(message.to_json())
        except Exception as e:
            print(f"Error sending message to {self.address}: {e}")
            self.is_alive = False
    
    async def receive_message(self) -> Optional[Message]:
        try:
            data = await self.websocket.recv()
            return Message.from_json(data)
        except Exception as e:
            print(f"Error receiving message from {self.address}: {e}")
            self.is_alive = False
            return None

class P2PNode:
    def __init__(self, host: str, port: int, blockchain: Blockchain):
        self.host = host
        self.port = port
        self.blockchain = blockchain
        self.consensus_manager = ConsensusManager(blockchain)
        self.transaction_validator = TransactionValidator(blockchain)
        self.transaction_pool = TransactionPool()
        self.peers: Dict[str, PeerConnection] = {}
        self.known_peers: Set[str] = set()
        self.node_id = hashlib.sha256(f"{host}:{port}".encode()).hexdigest()[:16]
        self.version = "1.0.0"
        self.server = None
        
    async def start(self):
        self.server = await websockets.serve(
            self.handle_connection,
            self.host,
            self.port
        )
        print(f"Node {self.node_id} listening on {self.host}:{self.port}")
        
        asyncio.create_task(self.peer_discovery())
        asyncio.create_task(self.heartbeat())
        
    async def handle_connection(self, websocket):
        peer_address = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        peer = PeerConnection(websocket, peer_address)
        self.peers[peer_address] = peer
        
        try:
            await self.send_version(peer)
            
            async for message in websocket:
                await self.handle_message(Message.from_json(message), peer)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            if peer_address in self.peers:
                del self.peers[peer_address]
    
    async def handle_message(self, message: Message, peer: PeerConnection):
        handlers = {
            MessageType.PING: self.handle_ping,
            MessageType.PONG: self.handle_pong,
            MessageType.GET_PEERS: self.handle_get_peers,
            MessageType.PEERS: self.handle_peers,
            MessageType.GET_BLOCKS: self.handle_get_blocks,
            MessageType.BLOCKS: self.handle_blocks,
            MessageType.NEW_BLOCK: self.handle_new_block,
            MessageType.NEW_TRANSACTION: self.handle_new_transaction,
            MessageType.GET_CHAIN: self.handle_get_chain,
            MessageType.CHAIN: self.handle_chain,
            MessageType.GET_MEMPOOL: self.handle_get_mempool,
            MessageType.MEMPOOL: self.handle_mempool,
            MessageType.VERSION: self.handle_version,
            MessageType.VERACK: self.handle_verack,
            MessageType.REGISTER_VALIDATOR: self.handle_register_validator,
            MessageType.VALIDATOR_LIST: self.handle_validator_list,
            MessageType.GET_VALIDATORS: self.handle_get_validators
        }
        
        handler = handlers.get(message.type)
        if handler:
            await handler(message, peer)
    
    async def send_version(self, peer: PeerConnection):
        message = Message(
            type=MessageType.VERSION,
            data={
                'version': self.version,
                'node_id': self.node_id,
                'chain_height': len(self.blockchain.chain),
                'services': ['full_node', 'mining']
            },
            sender=self.node_id
        )
        await peer.send_message(message)
    
    async def handle_version(self, message: Message, peer: PeerConnection):
        peer.version = message.data.get('version')
        
        verack = Message(
            type=MessageType.VERACK,
            data={'accepted': True},
            sender=self.node_id
        )
        await peer.send_message(verack)
        
        await self.sync_blockchain(peer)
    
    async def handle_verack(self, message: Message, peer: PeerConnection):
        if message.data.get('accepted'):
            print(f"Handshake completed with {peer.address}")
            # Request validator list from peer
            get_validators = Message(
                type=MessageType.GET_VALIDATORS,
                data={},
                sender=self.node_id
            )
            await peer.send_message(get_validators)
    
    async def handle_ping(self, message: Message, peer: PeerConnection):
        pong = Message(
            type=MessageType.PONG,
            data={'nonce': message.data.get('nonce')},
            sender=self.node_id
        )
        await peer.send_message(pong)
    
    async def handle_pong(self, message: Message, peer: PeerConnection):
        peer.last_seen = time.time()
    
    async def handle_get_peers(self, message: Message, peer: PeerConnection):
        peers_list = list(self.known_peers)[:50]
        response = Message(
            type=MessageType.PEERS,
            data={'peers': peers_list},
            sender=self.node_id
        )
        await peer.send_message(response)
    
    async def handle_peers(self, message: Message, peer: PeerConnection):
        new_peers = message.data.get('peers', [])
        for peer_addr in new_peers:
            if peer_addr not in self.known_peers:
                self.known_peers.add(peer_addr)
                asyncio.create_task(self.connect_to_peer(peer_addr))
    
    async def handle_get_blocks(self, message: Message, peer: PeerConnection):
        start_index = message.data.get('start_index', 0)
        count = min(message.data.get('count', 10), 100)
        
        blocks = []
        for i in range(start_index, min(start_index + count, len(self.blockchain.chain))):
            blocks.append(self.blockchain.chain[i].to_dict())
        
        response = Message(
            type=MessageType.BLOCKS,
            data={'blocks': blocks},
            sender=self.node_id
        )
        await peer.send_message(response)
    
    async def handle_blocks(self, message: Message, peer: PeerConnection):
        blocks_data = message.data.get('blocks', [])
        
        for block_data in blocks_data:
            block = self.deserialize_block(block_data)
            if block and self.blockchain.validate_block(block):
                self.blockchain.add_block(block)
    
    async def handle_new_block(self, message: Message, peer: PeerConnection):
        block_data = message.data.get('block')
        if not block_data:
            return
        
        block = self.deserialize_block(block_data)
        if block and self.blockchain.validate_block(block):
            if self.blockchain.add_block(block):
                await self.broadcast_block(block, exclude=peer.address)
    
    async def handle_new_transaction(self, message: Message, peer: PeerConnection):
        tx_data = message.data.get('transaction')
        if not tx_data:
            return

        tx = self.deserialize_transaction(tx_data)
        if tx and self.transaction_validator.validate_transaction(tx):
            if self.transaction_pool.add_transaction(tx):
                self.blockchain.add_transaction(tx)
                await self.broadcast_transaction(tx, exclude=peer.address)
                print(f"Received transaction {tx.tx_hash[:8]} from {peer.address}")
    
    async def handle_get_chain(self, message: Message, peer: PeerConnection):
        chain_data = self.blockchain.to_dict()
        response = Message(
            type=MessageType.CHAIN,
            data={'chain': chain_data},
            sender=self.node_id
        )
        await peer.send_message(response)
    
    async def handle_chain(self, message: Message, peer: PeerConnection):
        chain_data = message.data.get('chain')
        if not chain_data:
            return
        
        new_chain = self.deserialize_chain(chain_data)
        if new_chain and len(new_chain) > len(self.blockchain.chain):
            if self.validate_chain(new_chain):
                self.blockchain.chain = new_chain
                print(f"Blockchain updated from peer {peer.address}")
    
    async def handle_get_mempool(self, message: Message, peer: PeerConnection):
        transactions = [tx.to_dict() for tx in self.transaction_pool.transactions[:100]]
        response = Message(
            type=MessageType.MEMPOOL,
            data={'transactions': transactions},
            sender=self.node_id
        )
        await peer.send_message(response)
    
    async def handle_mempool(self, message: Message, peer: PeerConnection):
        transactions_data = message.data.get('transactions', [])
        
        for tx_data in transactions_data:
            tx = self.deserialize_transaction(tx_data)
            if tx and self.transaction_validator.validate_transaction(tx):
                self.transaction_pool.add_transaction(tx)
    
    async def broadcast_block(self, block: Block, exclude: str = None):
        message = Message(
            type=MessageType.NEW_BLOCK,
            data={'block': block.to_dict()},
            sender=self.node_id
        )
        
        for peer_addr, peer in self.peers.items():
            if peer_addr != exclude and peer.is_alive:
                await peer.send_message(message)
    
    async def broadcast_transaction(self, tx: Transaction, exclude: str = None):
        message = Message(
            type=MessageType.NEW_TRANSACTION,
            data={'transaction': tx.to_dict()},
            sender=self.node_id
        )
        
        for peer_addr, peer in self.peers.items():
            if peer_addr != exclude and peer.is_alive:
                await peer.send_message(message)
    
    async def sync_blockchain(self, peer: PeerConnection):
        message = Message(
            type=MessageType.GET_CHAIN,
            data={},
            sender=self.node_id
        )
        await peer.send_message(message)
    
    async def connect_to_peer(self, peer_address: str):
        try:
            host, port = peer_address.split(':')
            uri = f"ws://{host}:{port}"
            
            async with websockets.connect(uri) as websocket:
                peer = PeerConnection(websocket, peer_address)
                self.peers[peer_address] = peer
                
                await self.send_version(peer)
                
                async for message in websocket:
                    await self.handle_message(Message.from_json(message), peer)
        except Exception as e:
            print(f"Failed to connect to peer {peer_address}: {e}")
    
    async def peer_discovery(self):
        while True:
            for peer in list(self.peers.values()):
                if peer.is_alive:
                    message = Message(
                        type=MessageType.GET_PEERS,
                        data={},
                        sender=self.node_id
                    )
                    await peer.send_message(message)
            
            await asyncio.sleep(30)
    
    async def heartbeat(self):
        while True:
            for peer in list(self.peers.values()):
                if peer.is_alive:
                    message = Message(
                        type=MessageType.PING,
                        data={'nonce': time.time()},
                        sender=self.node_id
                    )
                    await peer.send_message(message)
                    
                    if time.time() - peer.last_seen > 120:
                        peer.is_alive = False

            await asyncio.sleep(30)

    async def handle_register_validator(self, message: Message, peer: PeerConnection):
        validator_data = message.data.get('validator')
        if not validator_data:
            return

        address = validator_data.get('address')
        stake = validator_data.get('stake')

        if address and stake:
            # Register validator in consensus
            success = self.consensus_manager.consensus.register_validator(address, stake)
            if success:
                print(f"Registered validator {address} from network with stake {stake}")
                # Broadcast to other peers
                await self.broadcast_validator_registration(validator_data, exclude=peer.address)

    async def handle_validator_list(self, message: Message, peer: PeerConnection):
        validators = message.data.get('validators', [])

        for validator_data in validators:
            address = validator_data.get('address')
            stake = validator_data.get('stake')
            if address and stake:
                # Only register if not already registered
                if address not in self.consensus_manager.consensus.validators:
                    self.consensus_manager.consensus.register_validator(address, stake)
                    print(f"Synced validator {address} with stake {stake}")

    async def handle_get_validators(self, message: Message, peer: PeerConnection):
        validators = []
        for address, validator in self.consensus_manager.consensus.validators.items():
            validators.append({
                'address': address,
                'stake': validator.stake,
                'reputation': validator.reputation,
                'blocks_validated': validator.blocks_validated
            })

        response = Message(
            type=MessageType.VALIDATOR_LIST,
            data={'validators': validators},
            sender=self.node_id
        )
        await peer.send_message(response)

    async def broadcast_validator_registration(self, validator_data: Dict, exclude: str = None):
        message = Message(
            type=MessageType.REGISTER_VALIDATOR,
            data={'validator': validator_data},
            sender=self.node_id
        )

        for peer_addr, peer in self.peers.items():
            if peer_addr != exclude and peer.is_alive:
                await peer.send_message(message)

    def deserialize_block(self, block_data: Dict) -> Optional[Block]:
        try:
            from blockchain import Block, Transaction, TransactionType
            
            transactions = []
            for tx_data in block_data.get('transactions', []):
                tx = self.deserialize_transaction(tx_data)
                if tx:
                    transactions.append(tx)
            
            return Block(
                index=block_data['index'],
                timestamp=block_data['timestamp'],
                transactions=transactions,
                previous_hash=block_data['previous_hash'],
                nonce=block_data['nonce'],
                difficulty=block_data['difficulty'],
                merkle_root=block_data.get('merkle_root'),
                validator=block_data.get('validator'),
                stake_weight=block_data.get('stake_weight', 0),
                work_weight=block_data.get('work_weight', 0),
                block_hash=block_data.get('block_hash')
            )
        except Exception as e:
            print(f"Error deserializing block: {e}")
            return None
    
    def deserialize_transaction(self, tx_data: Dict) -> Optional[Transaction]:
        try:
            from blockchain import Transaction, TransactionType
            
            return Transaction(
                tx_type=TransactionType(tx_data['type']),
                sender=tx_data['sender'],
                recipient=tx_data['recipient'],
                amount=tx_data['amount'],
                timestamp=tx_data['timestamp'],
                metadata=tx_data.get('metadata', {}),
                signature=tx_data.get('signature'),
                tx_hash=tx_data.get('tx_hash')
            )
        except Exception as e:
            print(f"Error deserializing transaction: {e}")
            return None
    
    def deserialize_chain(self, chain_data: Dict) -> Optional[List[Block]]:
        try:
            chain = []
            for block_data in chain_data.get('chain', []):
                block = self.deserialize_block(block_data)
                if block:
                    chain.append(block)
            return chain
        except Exception as e:
            print(f"Error deserializing chain: {e}")
            return None
    
    def validate_chain(self, chain: List[Block]) -> bool:
        for i in range(1, len(chain)):
            if chain[i].previous_hash != chain[i-1].block_hash:
                return False
            if chain[i].block_hash != chain[i].calculate_hash():
                return False
        return True