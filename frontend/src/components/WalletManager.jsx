import React, { useState } from 'react'
import { useQuery } from 'react-query'
import { FiCreditCard, FiSend, FiDownload, FiCopy, FiCheck } from 'react-icons/fi'
import { walletAPI, transactionAPI } from '../services/api'
import toast from 'react-hot-toast'

function WalletManager() {
  const [walletAddress, setWalletAddress] = useState('')
  const [copiedAddress, setCopiedAddress] = useState(false)

  const { data: balance, isLoading: balanceLoading } = useQuery(
    ['balance', walletAddress],
    () => walletAPI.getBalance(walletAddress),
    {
      enabled: !!walletAddress,
      refetchInterval: 10000,
    }
  )

  const { data: transactions, isLoading: txLoading } = useQuery(
    ['transactions', walletAddress],
    () => transactionAPI.getTransactionHistory(walletAddress),
    {
      enabled: !!walletAddress,
    }
  )

  const handleAddressSubmit = (e) => {
    e.preventDefault()
    const address = e.target.address.value.trim()
    if (address) {
      setWalletAddress(address)
    }
  }

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text)
    setCopiedAddress(true)
    toast.success('Address copied to clipboard')
    setTimeout(() => setCopiedAddress(false), 2000)
  }

  const generateNewWallet = () => {
    // Generate a random wallet address for demo
    const randomAddress = 'DEC' + Math.random().toString(36).substring(2, 15).toUpperCase()
    setWalletAddress(randomAddress)
    toast.success('New wallet generated!')
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Wallet Manager</h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Manage your DeCoin wallet and view transaction history
        </p>
      </div>

      {/* Wallet Input */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          Wallet Address
        </h3>
        <form onSubmit={handleAddressSubmit} className="space-y-4">
          <div className="flex gap-2">
            <input
              type="text"
              name="address"
              placeholder="Enter wallet address or generate new"
              defaultValue={walletAddress}
              className="input flex-1"
            />
            <button type="submit" className="btn-primary">
              Load Wallet
            </button>
            <button type="button" onClick={generateNewWallet} className="btn-secondary">
              Generate New
            </button>
          </div>
        </form>

        {walletAddress && (
          <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Current Address</p>
                <p className="font-mono text-sm text-gray-900 dark:text-white break-all">
                  {walletAddress}
                </p>
              </div>
              <button
                onClick={() => copyToClipboard(walletAddress)}
                className="ml-2 p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                {copiedAddress ? (
                  <FiCheck className="h-4 w-4 text-green-500" />
                ) : (
                  <FiCopy className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {walletAddress && (
        <>
          {/* Balance and Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Balance</p>
                  <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                    {balanceLoading ? (
                      <span className="skeleton h-8 w-24 inline-block"></span>
                    ) : (
                      `${balance?.balance || 0} DEC`
                    )}
                  </p>
                </div>
                <FiCreditCard className="h-8 w-8 text-primary-500" />
              </div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Transactions</p>
                  <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                    {txLoading ? (
                      <span className="skeleton h-8 w-16 inline-block"></span>
                    ) : (
                      transactions?.length || 0
                    )}
                  </p>
                </div>
                <FiSend className="h-8 w-8 text-green-500" />
              </div>
            </div>

            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Pending</p>
                  <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                    {balance?.pending || 0}
                  </p>
                </div>
                <FiDownload className="h-8 w-8 text-yellow-500" />
              </div>
            </div>
          </div>

          {/* Transaction History */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
              Transaction History
            </h3>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead>
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      From/To
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Time
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {txLoading ? (
                    <tr>
                      <td colSpan="5" className="px-6 py-4 text-center">
                        <div className="skeleton h-4 w-full"></div>
                      </td>
                    </tr>
                  ) : transactions?.length > 0 ? (
                    transactions.map((tx, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`badge ${
                            tx.sender === walletAddress ? 'badge-error' : 'badge-success'
                          }`}>
                            {tx.sender === walletAddress ? 'Sent' : 'Received'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          <code className="text-xs">
                            {tx.sender === walletAddress
                              ? tx.recipient.substring(0, 10) + '...'
                              : tx.sender.substring(0, 10) + '...'}
                          </code>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                          {tx.sender === walletAddress ? '-' : '+'}{tx.amount} DEC
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="badge badge-success">Confirmed</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                          {tx.timestamp ? new Date(tx.timestamp).toLocaleString() : 'Unknown'}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="5" className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                        No transactions found for this address
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Wallet Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button className="card hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-gray-900 dark:text-white">Export Private Key</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Backup your wallet credentials
                  </p>
                </div>
                <FiDownload className="h-6 w-6 text-gray-400" />
              </div>
            </button>

            <button className="card hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-gray-900 dark:text-white">Import Wallet</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Restore from private key
                  </p>
                </div>
                <FiCreditCard className="h-6 w-6 text-gray-400" />
              </div>
            </button>
          </div>
        </>
      )}
    </div>
  )
}

export default WalletManager