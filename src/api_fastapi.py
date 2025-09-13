"""
FastAPI-based REST API with OpenAPI/Swagger support
"""
from fastapi import FastAPI, HTTPException, Path, Query, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import time
from datetime import datetime

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
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
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
            return NodeStatus(
                node_id=self.node.node.node_id,
                chain_height=len(self.blockchain.chain),
                pending_transactions=len(self.blockchain.pending_transactions),
                connected_peers=len(self.node.node.peers),
                is_mining=self.node.is_mining,
                difficulty=self.blockchain.difficulty,
                version="1.0.0",
                uptime=time.time() - self.start_time
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
                # Create transaction based on type
                if tx_request.transaction_type == "standard":
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
        
        @self.app.post("/faucet/{address}", response_model=SuccessResponse, tags=["Wallet"])
        async def faucet(
            address: str = Path(..., description="Wallet address to fund")
        ):
            """Get free test coins from faucet (testnet only)"""
            # Check if address has already received faucet funds recently
            current_balance = self.blockchain.get_balance(address)
            if current_balance > 100:
                raise HTTPException(
                    status_code=429,
                    detail="Address already has sufficient balance"
                )

            # Create faucet transaction
            faucet_tx = self.transaction_builder.create_standard_transaction(
                sender="system",
                recipient=address,
                amount=100.0,  # Give 100 test coins
                fee=0,
                metadata={"type": "faucet", "timestamp": datetime.now().isoformat()}
            )

            if self.blockchain.add_transaction(faucet_tx):
                await self.node.node.broadcast_transaction(faucet_tx)
                return SuccessResponse(
                    message="Faucet funds sent successfully",
                    data={"transaction_id": faucet_tx.tx_hash, "amount": 100.0}
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
            return {
                "difficulty": self.blockchain.difficulty,
                "is_mining": self.node.is_mining,
                "blocks_mined": sum(1 for b in self.blockchain.chain if getattr(b, 'validator', None) == getattr(self.node, 'validator_address', None)),
                "hashrate": 0,  # TODO: Calculate hashrate
                "next_reward": 50.0
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

