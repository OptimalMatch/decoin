"""
Parallel mining implementation for increased hashrate
"""
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import time
from typing import Optional, Tuple

class ParallelMiner:
    def __init__(self, num_threads: int = None):
        """Initialize parallel miner with specified threads"""
        self.num_threads = num_threads or mp.cpu_count()
        print(f"Initializing parallel miner with {self.num_threads} threads")

    def mine_block_parallel(self, block_data: dict, difficulty: int) -> Tuple[int, str]:
        """
        Mine a block using multiple threads
        Each thread tries different nonce ranges
        """
        target = '0' * difficulty
        nonce_range = 1000000  # Each thread tries 1M nonces

        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = []

            for thread_id in range(self.num_threads):
                start_nonce = thread_id * nonce_range
                future = executor.submit(
                    self._mine_range,
                    block_data,
                    start_nonce,
                    nonce_range,
                    target
                )
                futures.append(future)

            # Return first successful result
            for future in as_completed(futures):
                result = future.result()
                if result:
                    # Cancel other threads
                    for f in futures:
                        f.cancel()
                    return result

        return None, None

    def _mine_range(self, block_data: dict, start_nonce: int, range_size: int, target: str) -> Optional[Tuple[int, str]]:
        """Mine a specific nonce range"""
        for nonce in range(start_nonce, start_nonce + range_size):
            block_data['nonce'] = nonce
            block_hash = hashlib.sha256(
                str(block_data).encode()
            ).hexdigest()

            if block_hash.startswith(target):
                return nonce, block_hash

        return None

    def calculate_hashrate(self, block_data: dict, duration: float = 1.0) -> float:
        """Calculate hashrate (hashes per second)"""
        start_time = time.time()
        hash_count = 0

        while time.time() - start_time < duration:
            for _ in range(1000):
                hashlib.sha256(str(block_data).encode()).hexdigest()
                hash_count += 1

        elapsed = time.time() - start_time
        hashrate = hash_count / elapsed

        # Multiply by thread count for parallel hashrate
        return hashrate * self.num_threads