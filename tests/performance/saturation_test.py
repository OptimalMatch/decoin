#!/usr/bin/env python3
"""Saturation throughput: how fast DeCoin actually SETTLES transactions when the
mempool is kept full — the number the 8-node load test never reached because it
only offered ~15 tx/s (mempools drained to 0).

This drives the real settlement pipeline in one process, signatures ON:
  build -> sign (ECDSA/secp256k1) -> validate (sig + nonce + balance)
        -> mempool -> mine a 500-tx block (PoW at the chain's difficulty)
        -> validate_block (re-verify every sig, nonce, Merkle root, work)
        -> append to the chain.

It excludes only P2P propagation (gossip across local nodes is not the limiter).
The headline it reports is the per-block clear time, which — set against the
node's block_time — is what bounds a saturated network.
"""
import sys, os, time, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from blockchain import Blockchain, Transaction, TransactionType
from wallet import Wallet

SENDERS = 40
TX_PER_SENDER = 500          # 20,000 signed transactions total
BLOCK_CAP = 2000             # blockchain.MAX_BLOCK_TRANSACTIONS

def main():
    bc = Blockchain()
    print(f"config: difficulty={bc.difficulty}, block_time={bc.block_time}s, "
          f"require_signatures={bc.require_signatures}, block cap={BLOCK_CAP} tx")

    # --- fund senders: 'system' is a minter (exempt from sig/balance/nonce) ----
    wallets = [Wallet.generate() for _ in range(SENDERS)]
    fund = TX_PER_SENDER * 10
    for w in wallets:
        bc.pending_transactions.append(Transaction(
            tx_type=TransactionType.STANDARD, sender="system",
            recipient=w.address, amount=fund, timestamp=time.time()))
    # mine the funding into the chain so balances are confirmed
    fb = bc.create_block("bootstrap"); fb.mine_block(bc.difficulty); bc.add_block(fb)
    print(f"funded {SENDERS} senders with {fund} each (block height {len(bc.chain)-1})")

    # --- pre-sign the workload (signing cost measured separately) --------------
    t = time.time()
    signed = []
    for w in wallets:
        for n in range(TX_PER_SENDER):
            tx = Transaction(tx_type=TransactionType.STANDARD, sender=w.address,
                             recipient=random.choice(wallets).address, amount=1,
                             timestamp=time.time(), nonce=n)
            tx.sign_with(w)
            signed.append(tx)
    total = len(signed)
    sign_s = time.time() - t
    print(f"\nsigned {total} tx in {sign_s:.2f}s -> {total/sign_s:,.0f} sign/s")

    # --- submit to mempool: validate_transaction (sig + nonce + balance) -------
    t = time.time()
    accepted = sum(1 for tx in signed if bc.add_transaction(tx))
    submit_s = time.time() - t
    print(f"validated+admitted {accepted}/{total} tx in {submit_s:.2f}s "
          f"-> {accepted/submit_s:,.0f} validate/s")

    # --- SETTLE: mine full blocks back-to-back until the mempool drains --------
    t = time.time()
    settled, blocks, per_block = 0, 0, []
    while bc.pending_transactions:
        bt = time.time()
        blk = bc.create_block(f"validator{blocks%2}")
        blk.mine_block(bc.difficulty)
        if not bc.add_block(blk):
            print("!! a block failed validation"); break
        dt = time.time() - bt
        per_block.append((len(blk.transactions) - 1, dt))   # minus coinbase
        settled += len(blk.transactions) - 1
        blocks += 1
    settle_s = time.time() - t

    full = [d for n, d in per_block if n >= BLOCK_CAP]
    avg_full = sum(full) / max(1, len(full))
    print(f"\nSETTLED {settled} tx across {blocks} blocks in {settle_s:.2f}s")
    print(f"  raw settlement rate (no inter-block wait): {settled/settle_s:,.0f} tx/s")
    print(f"  full {BLOCK_CAP}-tx block: mine+validate+append in {avg_full*1000:.0f} ms "
          f"(range {min(full)*1000:.0f}-{max(full)*1000:.0f} ms; flat => no quadratic)")
    print(f"  => a node mines 1 block / block_time, so a SATURATED network sustains")
    print(f"     ~{bc.MAX_BLOCK_TRANSACTIONS // bc.block_time:,} tx/s "
          f"({bc.MAX_BLOCK_TRANSACTIONS} tx / {bc.block_time}s block) — and the block "
          f"clears in {avg_full*1000:.0f} ms of that {bc.block_time*1000:.0f} ms window,")
    print(f"     so the ceiling is a policy choice (cap x 1/block_time), not the engine.")

if __name__ == "__main__":
    main()
