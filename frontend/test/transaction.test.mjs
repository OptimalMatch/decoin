// A freshly generated wallet signs a transaction that verifies, and the built
// POST body carries the fields the node needs. Run: `node --test`.
import test from 'node:test'
import assert from 'node:assert/strict'

import {
  Wallet,
  createSignedTransaction,
  verifySignature,
  signingBytes,
  addressFromPublicKeyHex,
} from '../src/services/wallet.js'

test('generate() produces distinct real keypairs and addresses', () => {
  const a = Wallet.generate()
  const b = Wallet.generate()
  assert.notEqual(a.privateKeyHex, b.privateKeyHex)
  assert.notEqual(a.address, b.address)
  assert.match(a.address, /^DEC[0-9a-f]{40}$/)
  assert.equal(addressFromPublicKeyHex(a.publicKeyHex), a.address)
})

test('createSignedTransaction yields a body whose signature verifies', () => {
  const w = Wallet.generate()
  const body = createSignedTransaction(w, { recipient: 'DECbob', amount: 25, nonce: 0, fee: 1 })

  assert.equal(body.sender, w.address)
  assert.equal(body.transaction_type, 'standard')
  assert.equal(body.public_key, w.publicKeyHex)
  assert.equal(typeof body.timestamp, 'number')
  assert.ok(Number.isInteger(body.timestamp))

  // Re-derive the signed bytes from the body and verify the signature.
  const bytes = signingBytes({
    type: 'standard', sender: body.sender, recipient: body.recipient,
    amount: body.amount, timestamp: body.timestamp, nonce: body.nonce,
    metadata: body.metadata,
  })
  assert.equal(verifySignature(body.public_key, body.signature, bytes), true)
})

test('a tampered amount fails verification', () => {
  const w = Wallet.generate()
  const body = createSignedTransaction(w, { recipient: 'DECbob', amount: 25 })
  const bytes = signingBytes({
    type: 'standard', sender: body.sender, recipient: body.recipient,
    amount: 999999, timestamp: body.timestamp, nonce: body.nonce, metadata: body.metadata,
  })
  assert.equal(verifySignature(body.public_key, body.signature, bytes), false)
})
