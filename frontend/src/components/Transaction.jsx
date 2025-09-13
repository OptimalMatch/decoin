import React, { useState } from 'react'
import { useMutation, useQuery } from 'react-query'
import { FiSend, FiLock, FiClock, FiDatabase } from 'react-icons/fi'
import { transactionAPI, walletAPI } from '../services/api'
import toast from 'react-hot-toast'

function Transaction() {
  const [txType, setTxType] = useState('standard')
  const [formData, setFormData] = useState({
    sender: '',
    recipient: '',
    amount: '',
    data: '',
    unlock_time: '',
    signers: [''],
    required_signatures: 1,
  })

  const { data: mempool } = useQuery('mempool', transactionAPI.getMempool, {
    refetchInterval: 5000,
  })

  const sendTransactionMutation = useMutation(transactionAPI.sendTransaction, {
    onSuccess: (data) => {
      toast.success('Transaction submitted successfully!')
      resetForm()
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to send transaction')
    },
  })

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSignerChange = (index, value) => {
    const newSigners = [...formData.signers]
    newSigners[index] = value
    setFormData(prev => ({ ...prev, signers: newSigners }))
  }

  const addSigner = () => {
    setFormData(prev => ({ ...prev, signers: [...prev.signers, ''] }))
  }

  const removeSigner = (index) => {
    const newSigners = formData.signers.filter((_, i) => i !== index)
    setFormData(prev => ({ ...prev, signers: newSigners }))
  }

  const resetForm = () => {
    setFormData({
      sender: '',
      recipient: '',
      amount: '',
      data: '',
      unlock_time: '',
      signers: [''],
      required_signatures: 1,
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    const transaction = {
      sender: formData.sender,
      recipient: formData.recipient,
      amount: parseFloat(formData.amount),
      transaction_type: txType,
    }

    // Add type-specific fields
    if (txType === 'data_storage') {
      transaction.data = formData.data
    } else if (txType === 'timelocked') {
      transaction.unlock_time = Math.floor(new Date(formData.unlock_time).getTime() / 1000)
    } else if (txType === 'multisig') {
      transaction.signers = formData.signers.filter(s => s.trim())
      transaction.required_signatures = parseInt(formData.required_signatures)
    }

    sendTransactionMutation.mutate(transaction)
  }

  const txTypes = [
    { value: 'standard', label: 'Standard', icon: FiSend, description: 'Simple transfer' },
    { value: 'multisig', label: 'Multi-Signature', icon: FiLock, description: 'Requires multiple signatures' },
    { value: 'timelocked', label: 'Time-Locked', icon: FiClock, description: 'Locked until specific time' },
    { value: 'data_storage', label: 'Data Storage', icon: FiDatabase, description: 'Store data on chain' },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Send Transaction</h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Create and broadcast a new transaction to the network
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Transaction Form */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Transaction Details
          </h3>

          {/* Transaction Type Selector */}
          <div className="mb-6">
            <label className="label">Transaction Type</label>
            <div className="grid grid-cols-2 gap-2">
              {txTypes.map((type) => (
                <button
                  key={type.value}
                  onClick={() => setTxType(type.value)}
                  className={`p-3 rounded-lg border-2 transition-all ${
                    txType === type.value
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <type.icon className={txType === type.value ? 'text-primary-600' : 'text-gray-500'} />
                    <div className="text-left">
                      <p className={`font-medium ${
                        txType === type.value ? 'text-primary-600' : 'text-gray-900 dark:text-white'
                      }`}>
                        {type.label}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{type.description}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Common Fields */}
            <div>
              <label className="label">Sender Address</label>
              <input
                type="text"
                name="sender"
                value={formData.sender}
                onChange={handleInputChange}
                className="input"
                placeholder="Enter sender address"
                required
              />
            </div>

            <div>
              <label className="label">Recipient Address</label>
              <input
                type="text"
                name="recipient"
                value={formData.recipient}
                onChange={handleInputChange}
                className="input"
                placeholder="Enter recipient address"
                required
              />
            </div>

            <div>
              <label className="label">Amount</label>
              <input
                type="number"
                name="amount"
                value={formData.amount}
                onChange={handleInputChange}
                className="input"
                placeholder="0.00"
                step="0.01"
                min="0"
                required
              />
            </div>

            {/* Type-specific Fields */}
            {txType === 'data_storage' && (
              <div>
                <label className="label">Data</label>
                <textarea
                  name="data"
                  value={formData.data}
                  onChange={handleInputChange}
                  className="input"
                  rows="3"
                  placeholder="Enter data to store on blockchain"
                  required
                />
              </div>
            )}

            {txType === 'timelocked' && (
              <div>
                <label className="label">Unlock Time</label>
                <input
                  type="datetime-local"
                  name="unlock_time"
                  value={formData.unlock_time}
                  onChange={handleInputChange}
                  className="input"
                  required
                />
              </div>
            )}

            {txType === 'multisig' && (
              <>
                <div>
                  <label className="label">Required Signatures</label>
                  <input
                    type="number"
                    name="required_signatures"
                    value={formData.required_signatures}
                    onChange={handleInputChange}
                    className="input"
                    min="1"
                    max={formData.signers.length}
                    required
                  />
                </div>
                <div>
                  <label className="label">Signers</label>
                  {formData.signers.map((signer, index) => (
                    <div key={index} className="flex gap-2 mb-2">
                      <input
                        type="text"
                        value={signer}
                        onChange={(e) => handleSignerChange(index, e.target.value)}
                        className="input"
                        placeholder="Signer address"
                        required
                      />
                      {formData.signers.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeSigner(index)}
                          className="btn-secondary px-3"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={addSigner}
                    className="btn-secondary text-sm"
                  >
                    Add Signer
                  </button>
                </div>
              </>
            )}

            <div className="flex gap-2 pt-4">
              <button
                type="submit"
                disabled={sendTransactionMutation.isLoading}
                className="btn-primary flex-1"
              >
                {sendTransactionMutation.isLoading ? 'Sending...' : 'Send Transaction'}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="btn-secondary"
              >
                Reset
              </button>
            </div>
          </form>
        </div>

        {/* Mempool */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Mempool ({mempool?.length || 0} pending)
          </h3>
          <div className="space-y-2 max-h-96 overflow-y-auto scrollbar-thin">
            {mempool?.length > 0 ? (
              mempool.map((tx, index) => (
                <div key={index} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="flex items-center justify-between mb-1">
                    <span className="badge badge-warning">{tx.transaction_type}</span>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {tx.timestamp ? new Date(tx.timestamp).toLocaleTimeString() : 'Pending'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {tx.sender.substring(0, 8)}... → {tx.recipient.substring(0, 8)}...
                  </p>
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">
                    Amount: {tx.amount}
                  </p>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No pending transactions
              </div>
            )}
          </div>

          {/* Fee Estimation */}
          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-sm font-medium text-blue-900 dark:text-blue-300">
              Estimated Fee
            </p>
            <p className="text-lg font-bold text-blue-900 dark:text-blue-300">
              0.001 DEC
            </p>
            <p className="text-xs text-blue-700 dark:text-blue-400 mt-1">
              ~30 seconds confirmation time
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Transaction