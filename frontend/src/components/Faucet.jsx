import React, { useState } from 'react'
import { useMutation } from 'react-query'
import { FiDroplet, FiCheck, FiAlertCircle } from 'react-icons/fi'
import toast from 'react-hot-toast'
import axios from 'axios'

function Faucet() {
  const [address, setAddress] = useState('')
  const [lastFaucetTx, setLastFaucetTx] = useState(null)

  const faucetMutation = useMutation(
    async (address) => {
      const response = await axios.post(`/api/faucet/${address}`)
      return response.data
    },
    {
      onSuccess: (data) => {
        toast.success('Test coins sent successfully!')
        setLastFaucetTx(data.data)
        setAddress('')
      },
      onError: (error) => {
        if (error.response?.status === 429) {
          toast.error('Address already has sufficient balance')
        } else {
          toast.error(error.response?.data?.detail || 'Failed to send test coins')
        }
      }
    }
  )

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!address.trim()) {
      toast.error('Please enter a wallet address')
      return
    }
    faucetMutation.mutate(address.trim())
  }

  const generateRandomAddress = () => {
    const randomAddress = 'DEC' + Math.random().toString(36).substring(2, 15).toUpperCase()
    setAddress(randomAddress)
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Test Faucet</h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Get free test coins for development and testing
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Faucet Form */}
        <div className="card">
          <div className="flex items-center mb-4">
            <FiDroplet className="h-6 w-6 text-blue-500 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Request Test Coins
            </h3>
          </div>

          <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              <strong>Faucet Rules:</strong>
            </p>
            <ul className="mt-2 text-sm text-blue-700 dark:text-blue-300 space-y-1">
              <li>• Each address can receive 100 DEC test coins</li>
              <li>• Maximum balance limit: 100 DEC</li>
              <li>• Coins are for testing purposes only</li>
              <li>• No real value - testnet only</li>
            </ul>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Wallet Address</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="Enter your wallet address"
                  className="input flex-1"
                  disabled={faucetMutation.isLoading}
                />
                <button
                  type="button"
                  onClick={generateRandomAddress}
                  className="btn-secondary"
                  disabled={faucetMutation.isLoading}
                >
                  Generate
                </button>
              </div>
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Enter an existing address or generate a new one
              </p>
            </div>

            <button
              type="submit"
              disabled={faucetMutation.isLoading || !address.trim()}
              className="w-full btn-primary flex items-center justify-center gap-2"
            >
              {faucetMutation.isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Requesting coins...
                </>
              ) : (
                <>
                  <FiDroplet />
                  Request 100 Test Coins
                </>
              )}
            </button>
          </form>

          {/* Success Message */}
          {lastFaucetTx && (
            <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="flex items-start">
                <FiCheck className="h-5 w-5 text-green-500 mt-0.5 mr-2 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-800 dark:text-green-200">
                    Success! 100 DEC sent
                  </p>
                  <p className="mt-1 text-xs text-green-700 dark:text-green-300">
                    Transaction ID: {lastFaucetTx.transaction_id?.substring(0, 16)}...
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Info Card */}
        <div className="space-y-4">
          {/* What is a Faucet */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">
              What is a Faucet?
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
              A faucet is a service that provides free test coins for blockchain development
              and testing. These coins have no real value and are used exclusively on the testnet.
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Use these coins to:
            </p>
            <ul className="mt-2 space-y-1 text-sm text-gray-600 dark:text-gray-400">
              <li>• Test transactions and smart contracts</li>
              <li>• Experiment with DeFi features</li>
              <li>• Learn blockchain development</li>
              <li>• Demo applications</li>
            </ul>
          </div>

          {/* Quick Stats */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">
              Faucet Statistics
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Per Request</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">100 DEC</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Max Balance</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">100 DEC</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Network</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">Testnet</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Status</p>
                <p className="text-lg font-semibold text-green-600 dark:text-green-400">Active</p>
              </div>
            </div>
          </div>

          {/* Warning */}
          <div className="card bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800">
            <div className="flex items-start">
              <FiAlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5 mr-2 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  Testnet Only
                </p>
                <p className="mt-1 text-xs text-yellow-700 dark:text-yellow-300">
                  These coins have no monetary value and cannot be exchanged for real currency.
                  They are for testing purposes only on the DeCoin testnet.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Faucet