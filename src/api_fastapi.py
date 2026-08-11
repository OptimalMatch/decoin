"""
FastAPI-based REST API with OpenAPI/Swagger support
"""
from fastapi import FastAPI, HTTPException, Path, Query, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import time
import json
from datetime import datetime

from blockchain import Transaction as ChainTx, TransactionType as ChainTxType
# The API schema and the chain use different enum spellings (e.g. "timelocked"
# vs "time_locked"), so map explicitly when reconstructing a submitted tx.
_SCHEMA_TO_CHAIN_TYPE = {
    "standard": ChainTxType.STANDARD,
    "multisig": ChainTxType.MULTI_SIG,
    "timelocked": ChainTxType.TIME_LOCKED,
    "data": ChainTxType.DATA_STORAGE,
    "contract": ChainTxType.SMART_CONTRACT,
}
from schemas import (
    TransactionRequest, TransactionResponse,
    BlockResponse, NodeStatus, PeerInfo,
    ChainInfo, MiningRequest, WalletBalance,
    ContractDeployRequest, ContractCallRequest,
    ErrorResponse, SuccessResponse
)


class DeCoinAPI:
    def __init__(self, node):
        self.node = node
        self.blockchain = node.blockchain
        self.transaction_builder = node.transaction_builder
        self.start_time = time.time()

        # Faucet rate-limiting state (see the /faucet route). Addresses are free
        # to generate, so a per-address cap alone gates nothing; we also cap the
        # number of grants in a rolling window across ALL addresses.
        self._faucet_last_grant: Dict[str, float] = {}
        self._faucet_grants: List[float] = []
        self.FAUCET_AMOUNT = 100.0
        self.FAUCET_ADDRESS_COOLDOWN = 3600      # seconds between grants per address
        self.FAUCET_WINDOW = 3600                # rolling window for the global cap
        self.FAUCET_MAX_PER_WINDOW = 100         # grants allowed per window, all addresses

        # Create FastAPI app with metadata
        self.app = FastAPI(
            title="DeCoin API",
            description="Decentralized cryptocurrency blockchain API with smart contracts and consensus mechanisms",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json"
        )
        
        # Configure CORS
        # allow_origins=["*"] with allow_credentials=True is rejected by browsers
        # and is unsafe; the correct pairing for an open, credential-free API is
        # a wildcard origin with credentials off.
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all API routes"""
        
        @self.app.get("/", tags=["General"])
        async def root():
            """Root endpoint with API information"""
            return {
                "name": "DeCoin API",
                "version": "1.0.0",
                "docs": "/docs",
                "openapi": "/openapi.json"
            }
        
        @self.app.get("/status", response_model=NodeStatus, tags=["Node"])
        async def get_node_status():
            """Get current node status and statistics"""
            # Calculate blockchain size
            blockchain_bytes = len(json.dumps(self.blockchain.to_dict()).encode())
            if blockchain_bytes < 1024:
                blockchain_size = f"{blockchain_bytes} B"
            elif blockchain_bytes < 1024 * 1024:
                blockchain_size = f"{blockchain_bytes / 1024:.2f} KB"
            elif blockchain_bytes < 1024 * 1024 * 1024:
                blockchain_size = f"{blockchain_bytes / (1024 * 1024):.2f} MB"
            else:
                blockchain_size = f"{blockchain_bytes / (1024 * 1024 * 1024):.2f} GB"

            return NodeStatus(
                node_id=self.node.node.node_id,
                chain_height=len(self.blockchain.chain),
                pending_transactions=len(self.blockchain.pending_transactions),
                connected_peers=len(self.node.node.peers),
                is_mining=self.node.is_mining,
                difficulty=self.blockchain.difficulty,
                version="1.0.0",
                uptime=time.time() - self.start_time,
                blockchain_size=blockchain_size
            )
        
        @self.app.get("/blockchain", response_model=ChainInfo, tags=["Blockchain"])
        async def get_blockchain(
            start: int = Query(0, ge=0, description="Start block index"),
            limit: int = Query(100, ge=1, le=1000, description="Maximum blocks to return")
        ):
            """Get blockchain information and blocks"""
            chain = self.blockchain.chain[start:start+limit]
            blocks = [self._block_to_response(block) for block in chain]

            return ChainInfo(
                height=len(self.blockchain.chain),
                total_difficulty=sum(b.difficulty for b in self.blockchain.chain),
                blocks=blocks,
                is_valid=self.blockchain.validate_chain()
            )
        
        @self.app.get("/block/{index}", response_model=BlockResponse, tags=["Blockchain"])
        async def get_block(
            index: int = Path(..., ge=0, description="Block index/height")
        ):
            """Get a specific block by index"""
            if index >= len(self.blockchain.chain):
                raise HTTPException(status_code=404, detail="Block not found")
            
            block = self.blockchain.chain[index]
            return self._block_to_response(block)
        
        @self.app.get("/block/hash/{block_hash}", response_model=BlockResponse, tags=["Blockchain"])
        async def get_block_by_hash(
            block_hash: str = Path(..., description="Block hash")
        ):
            """Get a specific block by hash"""
            for block in self.blockchain.chain:
                if (block.block_hash or block.calculate_hash()) == block_hash:
                    return self._block_to_response(block)
            
            raise HTTPException(status_code=404, detail="Block not found")
        
        @self.app.post("/transaction", response_model=SuccessResponse, tags=["Transactions"])
        async def submit_transaction(tx_request: TransactionRequest):
            """Submit a new transaction to the network"""
            try:
                # Client-signed path: the client built and signed the transaction
                # locally, so the server must reconstruct it EXACTLY (same
                # timestamp and metadata) or the signature will not verify. We do
                # not re-time or rebuild it through the builder.
                #
                # When signatures are required, the API is a SUBMISSION endpoint,
                # not a transaction factory: it reconstructs the client's fully
                # formed transaction for every type (multisig carries its
                # signatures in metadata, so the trigger cannot be a top-level
                # signature) and lets add_transaction verify it.
                if self.blockchain.require_signatures or (tx_request.signature and tx_request.public_key):
                    if tx_request.timestamp is None:
                        raise HTTPException(
                            status_code=400,
                            detail="A signed transaction must include its timestamp"
                        )
                    chain_type = _SCHEMA_TO_CHAIN_TYPE.get(tx_request.transaction_type.value)
                    if chain_type is None:
                        raise HTTPException(status_code=400, detail="Invalid transaction type")
                    tx = ChainTx(
                        tx_type=chain_type,
                        sender=tx_request.sender,
                        recipient=tx_request.recipient,
                        amount=tx_request.amount,
                        timestamp=tx_request.timestamp,
                        metadata=tx_request.metadata or {},
                        signature=tx_request.signature,
                        public_key=tx_request.public_key,
                    )
                # Create transaction based on type
                elif tx_request.transaction_type == "standard":
                    tx = self.transaction_builder.create_standard_transaction(
                        sender=tx_request.sender,
                        recipient=tx_request.recipient,
                        amount=tx_request.amount,
                        fee=tx_request.metadata.get('fee', 0.001) if tx_request.metadata else 0.001,
                        metadata=tx_request.metadata or {}
                    )
                elif tx_request.transaction_type == "multisig":
                    tx = self.transaction_builder.create_multisig_transaction(
                        senders=tx_request.metadata.get('senders', [tx_request.sender]),
                        recipient=tx_request.recipient,
                        amount=tx_request.amount,
                        required_signatures=tx_request.metadata.get('required_signatures', 2),
                        fee=tx_request.metadata.get('fee', 0.002)
                    )
                elif tx_request.transaction_type == "timelocked":
                    tx = self.transaction_builder.create_time_locked_transaction(
                        sender=tx_request.sender,
                        recipient=tx_request.recipient,
                        amount=tx_request.amount,
                        unlock_time=tx_request.metadata.get('unlock_time', 
                            int((datetime.now().timestamp() + 3600))),
                        fee=tx_request.metadata.get('fee', 0.001)
                    )
                elif tx_request.transaction_type == "data":
                    tx = self.transaction_builder.create_data_storage_transaction(
                        sender=tx_request.sender,
                        data=tx_request.metadata.get('data', {}),
                        fee=tx_request.metadata.get('fee', 0.005)
                    )
                else:
                    raise HTTPException(status_code=400, detail="Invalid transaction type")
                
                # Add to blockchain and broadcast
                if self.blockchain.add_transaction(tx):
                    await self.node.node.broadcast_transaction(tx)
                    return SuccessResponse(
                        message="Transaction submitted successfully",
                        data={"transaction_id": tx.tx_hash, "status": "pending"}
                    )
                else:
                    raise HTTPException(status_code=400, detail="Invalid transaction")
                    
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/transaction/{tx_hash}", response_model=TransactionResponse, tags=["Transactions"])
        async def get_transaction(
            tx_hash: str = Path(..., description="Transaction hash")
        ):
            """Get transaction details by hash"""
            # Search in blockchain
            for block in self.blockchain.chain:
                for tx in block.transactions:
                    if tx.tx_hash == tx_hash:
                        return self._tx_to_response(tx, "confirmed", block.index)
            
            # Search in pending
            for tx in self.blockchain.pending_transactions:
                if tx.tx_hash == tx_hash:
                    return self._tx_to_response(tx, "pending")
            
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        @self.app.get("/mempool", response_model=List[TransactionResponse], tags=["Transactions"])
        async def get_mempool():
            """Get all pending transactions in the mempool"""
            return [
                self._tx_to_response(tx, "pending")
                for tx in self.blockchain.pending_transactions
            ]

        @self.app.get("/transactions/{address}", response_model=List[TransactionResponse], tags=["Transactions"])
        async def get_transaction_history(
            address: str = Path(..., description="Wallet address")
        ):
            """Get transaction history for an address"""
            transactions = []

            # Get confirmed transactions from blockchain
            for block in self.blockchain.chain:
                for tx in block.transactions:
                    if tx.sender == address or tx.recipient == address:
                        transactions.append(self._tx_to_response(tx, "confirmed", block.index))

            # Get pending transactions
            for tx in self.blockchain.pending_transactions:
                if tx.sender == address or tx.recipient == address:
                    transactions.append(self._tx_to_response(tx, "pending"))

            # Sort by timestamp (most recent first)
            transactions.sort(key=lambda x: x.timestamp, reverse=True)

            return transactions

        @self.app.post("/faucet/{address}", response_model=SuccessResponse, tags=["Wallet"])
        async def faucet(
            address: str = Path(..., description="Wallet address to fund")
        ):
            """Get free test coins from faucet (testnet only)"""
            now = time.time()

            # A per-address balance cap alone is not a limit: addresses are free,
            # so anyone can mint unlimited supply by cycling fresh addresses. The
            # real gate a faucet needs is on the *requester* (IP, captcha, or
            # account); lacking that here, we cap grants globally per window and
            # cool down each address. This bounds the damage; it does not remove
            # the underlying point that address-only gating is ungated.
            self._faucet_grants = [t for t in self._faucet_grants
                                   if now - t < self.FAUCET_WINDOW]
            if len(self._faucet_grants) >= self.FAUCET_MAX_PER_WINDOW:
                raise HTTPException(
                    status_code=429,
                    detail="Faucet rate limit reached; try again later"
                )

            last = self._faucet_last_grant.get(address, 0)
            if now - last < self.FAUCET_ADDRESS_COOLDOWN:
                raise HTTPException(
                    status_code=429,
                    detail="This address was funded recently; try again later"
                )

            if self.blockchain.get_balance(address) > self.FAUCET_AMOUNT:
                raise HTTPException(
                    status_code=429,
                    detail="Address already has sufficient balance"
                )

            # Create faucet transaction
            faucet_tx = self.transaction_builder.create_standard_transaction(
                sender="system",
                recipient=address,
                amount=self.FAUCET_AMOUNT,
                fee=0,
                metadata={"type": "faucet", "timestamp": datetime.now().isoformat()}
            )

            if self.blockchain.add_transaction(faucet_tx):
                self._faucet_grants.append(now)
                self._faucet_last_grant[address] = now
                await self.node.node.broadcast_transaction(faucet_tx)
                return SuccessResponse(
                    message="Faucet funds sent successfully",
                    data={"transaction_id": faucet_tx.tx_hash, "amount": self.FAUCET_AMOUNT}
                )
            else:
                raise HTTPException(status_code=500, detail="Failed to send faucet funds")

        @self.app.get("/balance/{address}", response_model=WalletBalance, tags=["Wallet"])
        async def get_balance(
            address: str = Path(..., description="Wallet address")
        ):
            """Get wallet balance for an address"""
            balance = self.blockchain.get_balance(address)
            pending = sum(
                tx.amount for tx in self.blockchain.pending_transactions
                if tx.recipient == address
            )
            
            return WalletBalance(
                address=address,
                balance=balance,
                pending=pending,
                staked=0  # TODO: Implement staking
            )
        
        @self.app.get("/peers", response_model=List[PeerInfo], tags=["Network"])
        async def get_peers():
            """Get list of connected peers"""
            peers = []
            for peer_addr, peer in self.node.node.peers.items():
                host, port = peer_addr.split(':')
                peers.append(PeerInfo(
                    address=host,
                    port=int(port),
                    node_id=getattr(peer, 'node_id', None),
                    last_seen=datetime.fromtimestamp(peer.last_seen) if hasattr(peer, 'last_seen') else None,
                    version=getattr(peer, 'version', None)
                ))
            return peers
        
        @self.app.post("/peers/add", response_model=SuccessResponse, tags=["Network"])
        async def add_peer(peer: PeerInfo):
            """Add a new peer to connect to"""
            peer_address = f"{peer.address}:{peer.port}"
            await self.node.node.connect_to_peer(peer_address)
            return SuccessResponse(
                message=f"Attempting to connect to peer {peer_address}"
            )
        
        @self.app.post("/mining", response_model=SuccessResponse, tags=["Mining"])
        async def control_mining(mining_request: MiningRequest):
            """Start or stop mining"""
            self.node.is_mining = mining_request.enable
            
            if mining_request.enable:
                message = f"Mining enabled with {mining_request.threads} threads"
            else:
                message = "Mining disabled"
            
            return SuccessResponse(message=message)
        
        @self.app.get("/mining/difficulty", response_model=Dict[str, Any], tags=["Mining"])
        async def get_mining_info():
            """Get current mining difficulty and statistics"""
            # Next block reward, computed from the halving schedule rather than
            # hardcoded at 50 (which was wrong after the first halving).
            height = len(self.blockchain.chain)
            halvings = height // 100000
            next_reward = 50.0 / (2 ** halvings)

            # Hashrate is not measured anywhere, so report an ESTIMATE derived
            # from difficulty and target block time (expected hashes to find a
            # block, per second), clearly labelled — not a fabricated 0.
            expected_hashes = 16 ** self.blockchain.difficulty
            hashrate_estimate = expected_hashes / max(self.blockchain.block_time, 1)

            return {
                "difficulty": self.blockchain.difficulty,
                "is_mining": self.node.is_mining,
                "blocks_mined": sum(1 for b in self.blockchain.chain if getattr(b, 'validator', None) == getattr(self.node, 'validator_address', None)),
                "hashrate_estimate": hashrate_estimate,
                "hashrate_measured": None,
                "next_reward": next_reward
            }
        
        @self.app.post("/contract/deploy", response_model=SuccessResponse, tags=["Smart Contracts"])
        async def deploy_contract(contract: ContractDeployRequest):
            """Deploy a new smart contract"""
            try:
                tx = self.transaction_builder.create_contract_transaction(
                    sender=contract.deployer,
                    contract_code=contract.code,
                    initial_state=contract.initial_state,
                    fee=0.01
                )
                
                if self.blockchain.add_transaction(tx):
                    await self.node.node.broadcast_transaction(tx)
                    return SuccessResponse(
                        message="Contract deployment initiated",
                        data={"transaction_id": tx.tx_hash, "contract_id": tx.metadata.get('contract_id')}
                    )
                else:
                    raise HTTPException(status_code=400, detail="Contract deployment failed")
                    
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.post("/contract/call", response_model=SuccessResponse, tags=["Smart Contracts"])
        async def call_contract(call: ContractCallRequest):
            """Call a smart contract method"""
            # TODO: Implement contract calling
            return SuccessResponse(
                message="Contract call feature coming soon",
                data={"contract_id": call.contract_id, "method": call.method}
            )
        
        @self.app.get("/validators", response_model=List[Dict[str, Any]], tags=["Consensus"])
        async def get_validators():
            """Get list of active validators"""
            validators = []
            for address, stake in self.node.consensus_manager.consensus.validators.items():
                validators.append({
                    "address": address,
                    "stake": stake,
                    "active": True,
                    "blocks_validated": 0  # TODO: Track this
                })
            return validators
        
        @self.app.get("/health", tags=["General"])
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    def _block_to_response(self, block) -> BlockResponse:
        """Convert internal block to response model"""
        return BlockResponse(
            index=block.index,
            hash=block.block_hash or block.calculate_hash(),
            previous_hash=block.previous_hash,
            timestamp=datetime.fromtimestamp(block.timestamp),
            transactions=[self._tx_to_response(tx, "confirmed", block.index) for tx in block.transactions],
            nonce=block.nonce,
            difficulty=block.difficulty,
            miner=getattr(block, 'validator', None)
        )
    
    def _tx_to_response(self, tx, status: str, block_height: Optional[int] = None) -> TransactionResponse:
        """Convert internal transaction to response model"""
        return TransactionResponse(
            transaction_id=tx.tx_hash,
            sender=tx.sender,
            recipient=tx.recipient,
            amount=tx.amount,
            timestamp=tx.timestamp if isinstance(tx.timestamp, datetime) else datetime.fromisoformat(tx.timestamp) if isinstance(tx.timestamp, str) else datetime.fromtimestamp(tx.timestamp),
            transaction_type=tx.tx_type.value if hasattr(tx.tx_type, 'value') else str(tx.tx_type),
            metadata=tx.metadata,
            status=status,
            block_height=block_height
        )

# Add monitoring endpoints
def add_monitoring_endpoints(app, blockchain=None, node=None):
    from monitoring import SystemMonitor
    monitor = SystemMonitor(blockchain, node)
    
    @app.get('/monitoring/metrics', tags=['Monitoring'])
    async def get_metrics():
        '''Get system metrics'''
        return monitor.metrics.get_metrics_summary()
    
    @app.get('/monitoring/health', tags=['Monitoring'])
    async def get_health():
        '''Get health status'''
        health = monitor.check_health()
        return health.to_dict()
    
    @app.get('/monitoring/dashboard', tags=['Monitoring'])
    async def get_dashboard():
        '''Get monitoring dashboard data'''
        return monitor.get_dashboard_data()
    
    return monitor

