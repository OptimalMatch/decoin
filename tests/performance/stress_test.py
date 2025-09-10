#!/usr/bin/env python3
"""
DeCoin Stress Testing
Tests system performance under heavy load
"""

import asyncio
import time
import random
import sys
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import json

sys.path.insert(0, 'src')


class StressTest:
    """Stress test the DeCoin network"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.results = {
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'errors': []
        }
    
    def create_random_transaction(self) -> Dict[str, Any]:
        """Create a random transaction"""
        tx_types = ['standard', 'multi_sig', 'time_locked', 'data_storage']
        tx_type = random.choice(tx_types)
        
        if tx_type == 'standard':
            return {
                'type': 'standard',
                'sender': f'user_{random.randint(1, 100)}',
                'recipient': f'user_{random.randint(1, 100)}',
                'amount': round(random.uniform(0.1, 100), 2),
                'fee': 0.001
            }
        elif tx_type == 'multi_sig':
            senders = [f'user_{i}' for i in random.sample(range(1, 100), 3)]
            return {
                'type': 'multi_sig',
                'senders': senders,
                'recipient': f'user_{random.randint(1, 100)}',
                'amount': round(random.uniform(0.1, 100), 2),
                'required_signatures': 2,
                'fee': 0.002
            }
        elif tx_type == 'time_locked':
            return {
                'type': 'time_locked',
                'sender': f'user_{random.randint(1, 100)}',
                'recipient': f'user_{random.randint(1, 100)}',
                'amount': round(random.uniform(0.1, 100), 2),
                'unlock_time': time.time() + random.randint(3600, 86400),
                'fee': 0.001
            }
        else:  # data_storage
            return {
                'type': 'data_storage',
                'sender': f'user_{random.randint(1, 100)}',
                'data': {
                    'message': f'Test data {random.randint(1, 1000)}',
                    'timestamp': time.time(),
                    'random': random.random()
                },
                'fee': 0.005
            }
    
    def send_transaction(self) -> tuple:
        """Send a single transaction and measure response time"""
        tx = self.create_random_transaction()
        
        start = time.perf_counter()
        try:
            response = requests.post(
                f"{self.base_url}/transaction",
                json=tx,
                timeout=5
            )
            end = time.perf_counter()
            
            return (True, end - start, response.status_code)
        except Exception as e:
            end = time.perf_counter()
            return (False, end - start, str(e))
    
    def concurrent_transactions(self, num_transactions: int, max_workers: int = 10):
        """Send multiple transactions concurrently"""
        print(f"\n📤 Sending {num_transactions} concurrent transactions...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.send_transaction) for _ in range(num_transactions)]
            
            for future in as_completed(futures):
                success, response_time, info = future.result()
                
                if success:
                    self.results['successful_requests'] += 1
                    self.results['response_times'].append(response_time)
                else:
                    self.results['failed_requests'] += 1
                    self.results['errors'].append(info)
    
    def burst_test(self, bursts: int = 5, transactions_per_burst: int = 50):
        """Send transactions in bursts"""
        print(f"\n💥 Burst Test: {bursts} bursts of {transactions_per_burst} transactions")
        
        for burst in range(bursts):
            print(f"  Burst {burst + 1}/{bursts}...")
            self.concurrent_transactions(transactions_per_burst, max_workers=20)
            time.sleep(1)  # Brief pause between bursts
    
    def sustained_load_test(self, duration: int = 60, transactions_per_second: int = 10):
        """Sustained load test over time"""
        print(f"\n⏱️  Sustained Load Test: {transactions_per_second} tx/s for {duration} seconds")
        
        start_time = time.time()
        transaction_count = 0
        
        while time.time() - start_time < duration:
            batch_start = time.time()
            
            # Send batch of transactions
            self.concurrent_transactions(transactions_per_second, max_workers=5)
            transaction_count += transactions_per_second
            
            # Maintain rate
            elapsed = time.time() - batch_start
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            
            # Progress update
            progress = int((time.time() - start_time) / duration * 100)
            print(f"  Progress: {progress}% ({transaction_count} transactions sent)", end='\r')
        
        print(f"\n  Total transactions sent: {transaction_count}")
    
    def api_endpoint_test(self):
        """Test all API endpoints under load"""
        print(f"\n🔗 Testing API Endpoints Under Load...")
        
        endpoints = [
            ('GET', '/status'),
            ('GET', '/blockchain'),
            ('GET', '/mempool'),
            ('GET', '/peers'),
            ('GET', '/health'),
            ('GET', '/block/0'),
            ('GET', '/balance/user_1')
        ]
        
        endpoint_results = {}
        
        for method, endpoint in endpoints:
            times = []
            errors = 0
            
            for _ in range(100):  # 100 requests per endpoint
                start = time.perf_counter()
                try:
                    if method == 'GET':
                        response = requests.get(f"{self.base_url}{endpoint}", timeout=2)
                    end = time.perf_counter()
                    times.append(end - start)
                except:
                    errors += 1
            
            if times:
                endpoint_results[endpoint] = {
                    'average_time': statistics.mean(times) * 1000,  # ms
                    'median_time': statistics.median(times) * 1000,
                    'error_rate': errors / 100 * 100  # percentage
                }
        
        return endpoint_results
    
    def network_partition_test(self, nodes: List[str]):
        """Test behavior during network partitions"""
        print(f"\n🔀 Network Partition Test...")
        
        # Send transactions to different nodes
        results_by_node = {}
        
        for node_url in nodes:
            self.base_url = node_url
            self.results = {
                'successful_requests': 0,
                'failed_requests': 0,
                'response_times': [],
                'errors': []
            }
            
            self.concurrent_transactions(50, max_workers=5)
            results_by_node[node_url] = dict(self.results)
        
        return results_by_node
    
    def generate_report(self):
        """Generate stress test report"""
        print("\n" + "=" * 60)
        print("📊 Stress Test Report")
        print("=" * 60)
        
        total_requests = self.results['successful_requests'] + self.results['failed_requests']
        
        if total_requests > 0:
            success_rate = self.results['successful_requests'] / total_requests * 100
            print(f"\n📈 Overall Performance:")
            print(f"  • Total requests: {total_requests}")
            print(f"  • Successful: {self.results['successful_requests']}")
            print(f"  • Failed: {self.results['failed_requests']}")
            print(f"  • Success rate: {success_rate:.2f}%")
        
        if self.results['response_times']:
            print(f"\n⏱️  Response Times:")
            print(f"  • Average: {statistics.mean(self.results['response_times'])*1000:.2f} ms")
            print(f"  • Median: {statistics.median(self.results['response_times'])*1000:.2f} ms")
            print(f"  • Min: {min(self.results['response_times'])*1000:.2f} ms")
            print(f"  • Max: {max(self.results['response_times'])*1000:.2f} ms")
            
            # Calculate percentiles
            sorted_times = sorted(self.results['response_times'])
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
            print(f"  • 95th percentile: {p95*1000:.2f} ms")
            print(f"  • 99th percentile: {p99*1000:.2f} ms")
        
        if self.results['errors']:
            print(f"\n❌ Errors:")
            error_types = {}
            for error in self.results['errors']:
                error_type = str(error).split(':')[0]
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            for error_type, count in error_types.items():
                print(f"  • {error_type}: {count}")
        
        print("\n" + "=" * 60)
        
        return self.results
    
    def run_full_stress_test(self):
        """Run complete stress test suite"""
        print("=" * 60)
        print("🔥 DeCoin Stress Test Suite")
        print("=" * 60)
        
        # 1. Burst test
        self.burst_test(bursts=3, transactions_per_burst=100)
        
        # 2. Sustained load test
        self.sustained_load_test(duration=30, transactions_per_second=20)
        
        # 3. API endpoint test
        endpoint_results = self.api_endpoint_test()
        print("\n📊 API Endpoint Performance:")
        for endpoint, metrics in endpoint_results.items():
            print(f"  {endpoint}:")
            print(f"    • Avg: {metrics['average_time']:.2f} ms")
            print(f"    • Error rate: {metrics['error_rate']:.1f}%")
        
        # 4. Generate final report
        return self.generate_report()


def main():
    """Run stress tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DeCoin Stress Testing')
    parser.add_argument('--url', default='http://localhost:8080', help='Node URL')
    parser.add_argument('--duration', type=int, default=30, help='Test duration in seconds')
    parser.add_argument('--rate', type=int, default=10, help='Transactions per second')
    parser.add_argument('--full', action='store_true', help='Run full test suite')
    
    args = parser.parse_args()
    
    stress_test = StressTest(args.url)
    
    if args.full:
        results = stress_test.run_full_stress_test()
    else:
        stress_test.sustained_load_test(args.duration, args.rate)
        results = stress_test.generate_report()
    
    # Save results
    with open('stress_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n📁 Results saved to stress_test_results.json")


if __name__ == "__main__":
    main()