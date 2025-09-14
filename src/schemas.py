"""
Pydantic models for API request/response schemas
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class TransactionType(str, Enum):
    STANDARD = "standard"
    MULTISIG = "multisig"
    TIMELOCKED = "timelocked"
    DATA = "data"
    CONTRACT = "contract"


class TransactionRequest(BaseModel):
    sender: str = Field(..., description="Address of the sender")
    recipient: str = Field(..., description="Address of the recipient")
    amount: float = Field(..., gt=0, description="Amount to transfer")
    transaction_type: TransactionType = Field(default=TransactionType.STANDARD, description="Type of transaction")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional transaction metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sender": "alice",
                "recipient": "bob",
                "amount": 10.5,
                "transaction_type": "standard",
                "metadata": {"note": "Payment for services"}
            }
        }


class TransactionResponse(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction identifier")
    sender: str
    recipient: str
    amount: float
    timestamp: datetime
    transaction_type: str
    metadata: Optional[Dict[str, Any]] = None
    status: str = Field(..., description="Transaction status (pending/confirmed)")
    block_height: Optional[int] = Field(default=None, description="Block number if confirmed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "abc123def456",
                "sender": "alice",
                "recipient": "bob",
                "amount": 10.5,
                "timestamp": "2024-01-01T12:00:00",
                "transaction_type": "standard",
                "status": "pending"
            }
        }


class BlockRequest(BaseModel):
    transactions: List[str] = Field(..., description="List of transaction IDs to include")
    miner: str = Field(..., description="Address of the miner")
    
    class Config:
        json_schema_extra = {
            "example": {
                "transactions": ["tx1", "tx2", "tx3"],
                "miner": "miner1"
            }
        }


class BlockResponse(BaseModel):
    index: int = Field(..., description="Block index/height")
    hash: str = Field(..., description="Block hash")
    previous_hash: str = Field(..., description="Previous block hash")
    timestamp: datetime
    transactions: List[TransactionResponse]
    nonce: int = Field(..., description="Proof of work nonce")
    difficulty: int
    miner: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "index": 1,
                "hash": "0000abc123",
                "previous_hash": "0000def456",
                "timestamp": "2024-01-01T12:00:00",
                "transactions": [],
                "nonce": 12345,
                "difficulty": 4
            }
        }


class NodeStatus(BaseModel):
    node_id: str = Field(..., description="Unique node identifier")
    chain_height: int = Field(..., description="Current blockchain height")
    pending_transactions: int = Field(..., description="Number of pending transactions")
    connected_peers: int = Field(..., description="Number of connected peers")
    is_mining: bool = Field(..., description="Whether node is currently mining")
    difficulty: int = Field(..., description="Current mining difficulty")
    version: str = Field(default="1.0.0", description="Node software version")
    uptime: Optional[float] = Field(default=None, description="Node uptime in seconds")
    blockchain_size: Optional[str] = Field(default=None, description="Total blockchain size")
    
    class Config:
        json_schema_extra = {
            "example": {
                "node_id": "node123",
                "chain_height": 100,
                "pending_transactions": 5,
                "connected_peers": 8,
                "is_mining": True,
                "difficulty": 4,
                "version": "1.0.0"
            }
        }


class PeerInfo(BaseModel):
    address: str = Field(..., description="Peer network address")
    port: int = Field(..., description="Peer port")
    node_id: Optional[str] = Field(default=None, description="Peer node ID")
    last_seen: Optional[datetime] = Field(default=None, description="Last contact time")
    version: Optional[str] = Field(default=None, description="Peer version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "address": "192.168.1.100",
                "port": 8333,
                "node_id": "peer456",
                "last_seen": "2024-01-01T12:00:00"
            }
        }


class ChainInfo(BaseModel):
    height: int = Field(..., description="Blockchain height")
    total_difficulty: int = Field(..., description="Total accumulated difficulty")
    blocks: List[BlockResponse] = Field(..., description="List of blocks")
    is_valid: bool = Field(..., description="Chain validation status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "height": 100,
                "total_difficulty": 400,
                "blocks": [],
                "is_valid": True
            }
        }


class MiningRequest(BaseModel):
    enable: bool = Field(..., description="Enable or disable mining")
    threads: Optional[int] = Field(default=1, ge=1, le=16, description="Number of mining threads")
    
    class Config:
        json_schema_extra = {
            "example": {
                "enable": True,
                "threads": 4
            }
        }


class WalletBalance(BaseModel):
    address: str = Field(..., description="Wallet address")
    balance: float = Field(..., ge=0, description="Current balance")
    pending: float = Field(default=0, ge=0, description="Pending incoming transactions")
    staked: float = Field(default=0, ge=0, description="Amount staked for validation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "address": "alice",
                "balance": 100.5,
                "pending": 10.0,
                "staked": 50.0
            }
        }


class ContractDeployRequest(BaseModel):
    code: str = Field(..., description="Smart contract code")
    initial_state: Dict[str, Any] = Field(default={}, description="Initial contract state")
    deployer: str = Field(..., description="Contract deployer address")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "contract Token { ... }",
                "initial_state": {"total_supply": 1000000},
                "deployer": "alice"
            }
        }


class ContractCallRequest(BaseModel):
    contract_id: str = Field(..., description="Contract address/ID")
    method: str = Field(..., description="Method to call")
    params: Dict[str, Any] = Field(default={}, description="Method parameters")
    caller: str = Field(..., description="Caller address")
    
    class Config:
        json_schema_extra = {
            "example": {
                "contract_id": "contract123",
                "method": "transfer",
                "params": {"to": "bob", "amount": 100},
                "caller": "alice"
            }
        }


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    code: int = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid transaction",
                "code": 400,
                "details": {"reason": "Insufficient balance"}
            }
        }


class SuccessResponse(BaseModel):
    success: bool = Field(default=True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional response data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Transaction submitted successfully",
                "data": {"transaction_id": "abc123"}
            }
        }