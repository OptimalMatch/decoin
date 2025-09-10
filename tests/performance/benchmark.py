#!/usr/bin/env python3
"""
DeCoin Performance Benchmarks
Measures performance of key blockchain operations
"""

import time
import sys
import statistics
from typing import List, Dict, Any
sys.path.insert(0, 'src')

from blockchain import Blockchain, Transaction, TransactionType
from transactions import TransactionBuilder
from consensus import HybridConsensus


class BlockchainBenchmark:
    """Benchmark blockchain operations"""
    
    def __init__(self):
        self.blockchain = Blockchain()
        self.builder = TransactionBuilder()
        self.results = {}
    
    def benchmark_transaction_creation(self, iterations: int = 1000) -> Dict[str, float]:
        """Benchmark transaction creation speed"""
        print(f"\n📊 Benchmarking Transaction Creation ({iterations} iterations)...")
        
        times = []
        for i in range(iterations):
            start = time.perf_counter()
            tx = self.builder.create_standard_transaction(
                sender=f"user_{i}",
                recipient=f"user_{i+1}",
                amount=10.0 + i * 0.1
            )
            end = time.perf_counter()
            times.append(end - start)
        
        return {
            'total_time': sum(times),
            'average_time': statistics.mean(times),
            'median_time': statistics.median(times),
            'min_time': min(times),
            'max_time': max(times),
            'transactions_per_second': iterations / sum(times)
        }
    
    def benchmark_block_mining(self, difficulty: int = 3, blocks: int = 5) -> Dict[str, float]:
        """Benchmark block mining speed"""
        print(f"\n⛏️  Benchmarking Block Mining (difficulty={difficulty}, blocks={blocks})...")
        
        self.blockchain.difficulty = difficulty
        times = []
        
        for i in range(blocks):
            # Add some transactions
            for j in range(10):
                tx = self.builder.create_standard_transaction(
                    sender=f"miner_{i}",
                    recipient=f"user_{j}",
                    amount=1.0
                )
                self.blockchain.add_transaction(tx)
            
            # Mine block
            start = time.perf_counter()
            block = self.blockchain.create_block(f"miner_{i}")
            block.mine_block(difficulty)
            end = time.perf_counter()
            
            times.append(end - start)
            self.blockchain.add_block(block)
            print(f"  Block {i+1}/{blocks} mined in {end-start:.2f}s")
        
        return {
            'total_time': sum(times),
            'average_time': statistics.mean(times),
            'median_time': statistics.median(times),
            'min_time': min(times),
            'max_time': max(times),
            'blocks_per_minute': 60 / statistics.mean(times) if times else 0
        }
    
    def benchmark_chain_validation(self) -> Dict[str, float]:
        """Benchmark blockchain validation speed"""
        print(f"\n✅ Benchmarking Chain Validation...")
        
        # Build a chain with some blocks
        for i in range(10):
            for j in range(5):
                tx = self.builder.create_standard_transaction(
                    sender=f"user_{i}",
                    recipient=f"user_{j}",
                    amount=1.0
                )
                self.blockchain.add_transaction(tx)
            
            block = self.blockchain.create_block(f"miner_{i}")
            block.mine_block(2)  # Low difficulty for speed
            self.blockchain.add_block(block)
        
        # Benchmark validation
        times = []
        for _ in range(100):
            start = time.perf_counter()
            is_valid = self.blockchain.validate_chain()
            end = time.perf_counter()
            times.append(end - start)
        
        return {
            'chain_length': len(self.blockchain.chain),
            'total_transactions': sum(len(b.transactions) for b in self.blockchain.chain),
            'average_validation_time': statistics.mean(times),
            'median_validation_time': statistics.median(times),
            'validations_per_second': 100 / sum(times)
        }
    
    def benchmark_balance_calculation(self, addresses: int = 100) -> Dict[str, float]:
        """Benchmark balance calculation speed"""
        print(f"\n💰 Benchmarking Balance Calculation ({addresses} addresses)...")
        
        # Create transactions for many addresses
        for i in range(addresses):
            tx = self.builder.create_standard_transaction(
                sender="genesis",
                recipient=f"user_{i}",
                amount=100.0
            )
            self.blockchain.add_transaction(tx)
        
        block = self.blockchain.create_block("miner")
        block.mine_block(2)
        self.blockchain.add_block(block)
        
        # Benchmark balance calculations
        times = []
        for i in range(addresses):
            start = time.perf_counter()
            balance = self.blockchain.get_balance(f"user_{i}")
            end = time.perf_counter()
            times.append(end - start)
        
        return {
            'addresses_checked': addresses,
            'average_time': statistics.mean(times),
            'median_time': statistics.median(times),
            'total_time': sum(times),
            'lookups_per_second': addresses / sum(times)
        }
    
    def benchmark_transaction_types(self) -> Dict[str, Any]:
        """Benchmark different transaction types"""
        print(f"\n🔀 Benchmarking Transaction Types...")
        
        results = {}
        iterations = 100
        
        # Standard transactions
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            tx = self.builder.create_standard_transaction("alice", "bob", 10)
            self.blockchain.validate_transaction(tx)
            end = time.perf_counter()
            times.append(end - start)
        results['standard'] = statistics.mean(times) * 1000  # Convert to ms
        
        # MultiSig transactions
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            tx = self.builder.create_multisig_transaction(
                ["alice", "bob", "charlie"], "dave", 10, 2
            )
            self.blockchain.validate_transaction(tx)
            end = time.perf_counter()
            times.append(end - start)
        results['multisig'] = statistics.mean(times) * 1000
        
        # Time-locked transactions
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            tx = self.builder.create_time_locked_transaction(
                "alice", "bob", 10, time.time() + 3600
            )
            self.blockchain.validate_transaction(tx)
            end = time.perf_counter()
            times.append(end - start)
        results['timelocked'] = statistics.mean(times) * 1000
        
        # Data storage transactions
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            tx = self.builder.create_data_storage_transaction(
                "alice", {"data": "test", "id": _}
            )
            self.blockchain.validate_transaction(tx)
            end = time.perf_counter()
            times.append(end - start)
        results['data_storage'] = statistics.mean(times) * 1000
        
        return results
    
    def run_all_benchmarks(self):
        """Run all benchmarks and display results"""
        print("=" * 60)
        print("🚀 DeCoin Performance Benchmarks")
        print("=" * 60)
        
        # Transaction creation
        tx_results = self.benchmark_transaction_creation()
        print(f"\n📊 Transaction Creation Results:")
        print(f"  • Average time: {tx_results['average_time']*1000:.3f} ms")
        print(f"  • Transactions/second: {tx_results['transactions_per_second']:.0f}")
        
        # Block mining
        mining_results = self.benchmark_block_mining()
        print(f"\n⛏️  Block Mining Results:")
        print(f"  • Average time: {mining_results['average_time']:.2f} seconds")
        print(f"  • Blocks/minute: {mining_results['blocks_per_minute']:.2f}")
        
        # Chain validation
        validation_results = self.benchmark_chain_validation()
        print(f"\n✅ Chain Validation Results:")
        print(f"  • Chain length: {validation_results['chain_length']} blocks")
        print(f"  • Average validation: {validation_results['average_validation_time']*1000:.3f} ms")
        print(f"  • Validations/second: {validation_results['validations_per_second']:.0f}")
        
        # Balance calculation
        balance_results = self.benchmark_balance_calculation()
        print(f"\n💰 Balance Calculation Results:")
        print(f"  • Average lookup: {balance_results['average_time']*1000:.3f} ms")
        print(f"  • Lookups/second: {balance_results['lookups_per_second']:.0f}")
        
        # Transaction types
        tx_type_results = self.benchmark_transaction_types()
        print(f"\n🔀 Transaction Type Performance (avg ms):")
        for tx_type, avg_time in tx_type_results.items():
            print(f"  • {tx_type.capitalize()}: {avg_time:.3f} ms")
        
        print("\n" + "=" * 60)
        print("✅ Benchmarks Complete!")
        print("=" * 60)
        
        return {
            'transaction_creation': tx_results,
            'block_mining': mining_results,
            'chain_validation': validation_results,
            'balance_calculation': balance_results,
            'transaction_types': tx_type_results
        }


def main():
    """Run performance benchmarks"""
    benchmark = BlockchainBenchmark()
    results = benchmark.run_all_benchmarks()
    
    # Save results to file
    import json
    with open('benchmark_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📁 Results saved to benchmark_results.json")


if __name__ == "__main__":
    main()