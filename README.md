# DeCoin - Enhanced Bitcoin-Compatible Blockchain

DeCoin is a next-generation blockchain system that maintains compatibility with the Bitcoin network while introducing significant improvements:

## Key Features

1. **Faster Transactions**: Block time reduced to 30 seconds with optimized validation
2. **Reduced Mining Requirements**: Hybrid Proof-of-Stake/Proof-of-Work consensus
3. **Enhanced Metadata**: Transactions support up to 1KB of arbitrary metadata
4. **Advanced Transaction Types**: 
   - Smart contracts
   - Multi-signature transactions
   - Time-locked transactions
   - Atomic swaps
   - Data storage transactions

## Architecture Overview

### Core Components
- **Blockchain Core**: Modified Bitcoin-compatible blockchain with enhanced block structure
- **Consensus Engine**: Hybrid PoS/PoW with 70% stake, 30% work weighting
- **Transaction Processor**: Extended UTXO model with metadata and script support
- **Network Layer**: P2P protocol compatible with Bitcoin's wire protocol
- **RPC Interface**: Bitcoin-compatible RPC with extended methods

## Technical Specifications

- **Block Time**: 30 seconds
- **Block Size**: 4MB base, 8MB with witness data
- **Transaction Throughput**: ~500 TPS
- **Consensus**: Hybrid PoS/PoW
- **Metadata Size**: Up to 1KB per transaction
- **Script Language**: Extended Bitcoin Script with additional opcodes

## Compatibility

DeCoin maintains compatibility with Bitcoin through:
- Support for Bitcoin transaction formats
- Compatible address formats (with extensions)
- Interoperability bridges for cross-chain transactions
- Bitcoin RPC compatibility layer