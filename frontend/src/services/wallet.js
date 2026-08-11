// DeCoin browser wallet — real ECDSA over secp256k1, matching src/wallet.py.
//
// The node enforces signatures, so the frontend must sign transactions with a
// real key, not invent an address as 'DEC' + Math.random(). This produces the
// SAME addresses, canonical bytes, and (deterministic) signatures the Python
// node verifies — cross-checked byte-for-byte in frontend/test/wallet.test.mjs.
import { secp256k1 } from '@noble/curves/secp256k1.js'
import { sha256 } from '@noble/hashes/sha2.js'
import { ripemd160 } from '@noble/hashes/legacy.js'
import { bytesToHex, hexToBytes, utf8ToBytes } from '@noble/hashes/utils.js'

const ADDRESS_PREFIX = 'DEC'

// Public keys are the 64-byte x||y form (no 0x04 prefix), matching Python's
// VerifyingKey.to_string().
export function addressFromPublicKeyHex(publicKeyHex) {
  const pub = hexToBytes(publicKeyHex)
  return ADDRESS_PREFIX + bytesToHex(ripemd160(sha256(pub)))
}

// Canonical JSON identical to Python's json.dumps(obj, sort_keys=True):
// keys sorted (recursively), ", " between items and ": " between key and value.
// Data is ASCII (addresses, integer amounts) so escaping matches on both sides.
export function canonicalJson(value) {
  if (value === null) return 'null'
  const t = typeof value
  if (t === 'number') {
    if (!Number.isInteger(value)) throw new Error('canonicalJson: only integers are allowed')
    return String(value)
  }
  if (t === 'boolean') return value ? 'true' : 'false'
  if (t === 'string') return JSON.stringify(value)
  if (Array.isArray(value)) return '[' + value.map(canonicalJson).join(', ') + ']'
  const keys = Object.keys(value).sort()
  return '{' + keys.map((k) => JSON.stringify(k) + ': ' + canonicalJson(value[k])).join(', ') + '}'
}

// Metadata keys that carry signatures rather than signed content (multisig).
const UNSIGNED_META_KEYS = new Set(['signatures', 'public_keys'])

// The exact bytes a signature commits to — mirrors Transaction.signing_bytes.
// The timestamp is signed as an INTEGER (whole seconds) so the encoding matches
// Python's (a float would serialize as "170...0.0" here vs "170...0" in JS).
export function signingBytes(tx) {
  const meta = {}
  for (const [k, v] of Object.entries(tx.metadata || {})) {
    if (!UNSIGNED_META_KEYS.has(k)) meta[k] = v
  }
  const data = {
    type: tx.type,
    sender: tx.sender,
    recipient: tx.recipient,
    amount: tx.amount,
    timestamp: Math.trunc(tx.timestamp),
    nonce: tx.nonce ?? 0,
    metadata: meta,
  }
  return utf8ToBytes(canonicalJson(data))
}

// Verify a signature the way the node does (prehash SHA-256). The stored public
// key is 64-byte x||y; noble wants the 0x04-prefixed uncompressed form.
export function verifySignature(publicKeyHex, signatureHex, messageBytes) {
  try {
    const pub = new Uint8Array([4, ...hexToBytes(publicKeyHex)])
    // lowS:false accepts non-normalised signatures, matching python-ecdsa.
    return secp256k1.verify(hexToBytes(signatureHex), messageBytes, pub, { prehash: true, lowS: false })
  } catch {
    return false
  }
}

// Build a signed standard transaction as the object POST /transaction expects.
// Amount, fee, and nonce are integers; the timestamp is whole seconds.
export function createSignedTransaction(wallet, { recipient, amount, nonce = 0, fee = 0, note } = {}) {
  const metadata = { fee }
  if (note) metadata.note = note
  const tx = {
    type: 'standard', // chain type value, used inside signing_bytes
    sender: wallet.address,
    recipient,
    amount,
    timestamp: Math.floor(Date.now() / 1000),
    nonce,
    metadata,
  }
  wallet.signTransaction(tx)
  return {
    sender: tx.sender,
    recipient: tx.recipient,
    amount: tx.amount,
    transaction_type: 'standard', // schema type value
    metadata: tx.metadata,
    nonce: tx.nonce,
    timestamp: tx.timestamp,
    signature: tx.signature,
    public_key: tx.public_key,
  }
}


export class Wallet {
  constructor(privateKeyHex) {
    this._priv = hexToBytes(privateKeyHex)
  }

  static generate() {
    return new Wallet(bytesToHex(secp256k1.utils.randomSecretKey()))
  }

  static fromPrivateKeyHex(hex) {
    return new Wallet(hex)
  }

  get privateKeyHex() {
    return bytesToHex(this._priv)
  }

  get publicKeyHex() {
    // 0x04 || x || y, then drop the prefix byte to match Python's 64-byte form.
    return bytesToHex(secp256k1.getPublicKey(this._priv, false).slice(1))
  }

  get address() {
    return addressFromPublicKeyHex(this.publicKeyHex)
  }

  // Deterministic (RFC 6979) signature over SHA-256, raw r||s hex. lowS:false so
  // it matches Python's ecdsa (which does not low-s normalise).
  sign(messageBytes) {
    // prehash:true lets noble hash the message with SHA-256 internally, which
    // reproduces python-ecdsa's sign_deterministic(hashfunc=sha256) byte for
    // byte (hashing first and passing the digest takes a different RFC 6979
    // path). lowS:false because python-ecdsa does not low-s normalise. Returns
    // the compact 64-byte r||s signature.
    return bytesToHex(secp256k1.sign(messageBytes, this._priv, { lowS: false, prehash: true }))
  }

  // Sign a plain transaction object in place, attaching public_key + signature.
  signTransaction(tx) {
    tx.public_key = this.publicKeyHex
    tx.signature = this.sign(signingBytes(tx))
    return tx
  }
}
