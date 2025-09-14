import concurrent.futures
from typing import List, Tuple, Any, Dict
import json
import time

class ParallelTransactionValidator:
    def __init__(self, blockchain, max_workers=4):
        self.blockchain = blockchain
        self.max_workers = max_workers

    def validate_batch(self, transactions: List[Any]) -> List[Tuple[Any, bool]]:
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for tx in transactions:
                future = executor.submit(self._validate_single, tx)
                futures.append((tx, future))

            results = []
            for tx, future in futures:
                try:
                    is_valid = future.result(timeout=1)
                    results.append((tx, is_valid))
                except Exception:
                    results.append((tx, False))

            return results

    def _validate_single(self, tx: Any) -> bool:
        # Import here to avoid circular dependency
        from blockchain import TransactionType

        if tx.amount < 0:
            return False

        if len(json.dumps(tx.metadata)) > 1024:
            return False

        if tx.sender not in ['genesis', 'mining_reward', 'system', 'coinbase']:
            sender_balance = self.blockchain.get_balance(tx.sender, include_pending=False)
            total_required = tx.amount + tx.metadata.get('fee', 0.001)
            if sender_balance < total_required:
                return False

        if tx.tx_type == TransactionType.TIME_LOCKED:
            if 'unlock_time' not in tx.metadata:
                return False
            if tx.metadata['unlock_time'] <= time.time():
                return False

        return True