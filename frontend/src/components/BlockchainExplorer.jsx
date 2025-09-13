import React, { useState } from 'react'
import { useQuery } from 'react-query'
import { FiSearch, FiChevronRight, FiBox, FiHash } from 'react-icons/fi'
import { blockchainAPI } from '../services/api'
import toast from 'react-hot-toast'

function BlockchainExplorer() {
  const [selectedBlock, setSelectedBlock] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')

  const { data: blockchain, isLoading } = useQuery(
    'blockchain',
    blockchainAPI.getBlockchain,
    { refetchInterval: 10000 }
  )

  const handleSearch = (e) => {
    e.preventDefault()
    if (!searchTerm) return

    const searchValue = searchTerm.trim()

    // Search by block index
    if (!isNaN(searchValue)) {
      const blockIndex = parseInt(searchValue)
      const block = blockchain?.blocks?.find(b => b.index === blockIndex)
      if (block) {
        setSelectedBlock(block)
      } else {
        toast.error(`Block #${blockIndex} not found`)
      }
    }
    // Search by hash
    else if (searchValue.length === 64) {
      const block = blockchain?.blocks?.find(b => b.hash === searchValue)
      if (block) {
        setSelectedBlock(block)
      } else {
        toast.error('Block with this hash not found')
      }
    } else {
      toast.error('Please enter a valid block number or hash')
    }
  }

  const formatHash = (hash) => {
    if (!hash) return ''
    return `${hash.substring(0, 6)}...${hash.substring(hash.length - 6)}`
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Blockchain Explorer</h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Explore blocks and transactions on the DeCoin blockchain
        </p>
      </div>

      {/* Search Bar */}
      <div className="card">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="flex-1 relative">
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by block number or hash..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10"
            />
          </div>
          <button type="submit" className="btn-primary">
            Search
          </button>
        </form>
      </div>

      {/* Blockchain Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Blocks</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {blockchain?.blocks?.length || 0}
              </p>
            </div>
            <FiBox className="h-8 w-8 text-primary-500" />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Transactions</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {blockchain?.blocks?.reduce((acc, block) => acc + (block.transactions?.length || 0), 0) || 0}
              </p>
            </div>
            <FiHash className="h-8 w-8 text-green-500" />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Average Block Time</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                ~30s
              </p>
            </div>
            <FiHash className="h-8 w-8 text-purple-500" />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Network Hashrate</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {blockchain?.blocks?.[blockchain.blocks.length - 1]?.difficulty || 0} H/s
              </p>
            </div>
            <FiHash className="h-8 w-8 text-orange-500" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Block List */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Recent Blocks
          </h3>
          <div className="space-y-2 max-h-96 overflow-y-auto scrollbar-thin">
            {isLoading ? (
              <div className="space-y-2">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="skeleton h-16 w-full"></div>
                ))}
              </div>
            ) : (
              blockchain?.blocks?.slice().reverse().slice(0, 10).map((block) => (
                <div
                  key={block.index}
                  onClick={() => setSelectedBlock(block)}
                  className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-semibold text-gray-900 dark:text-white">
                          Block #{block.index}
                        </span>
                        <span className="badge badge-success">
                          {block.transactions?.length || 0} txns
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        Hash: {formatHash(block.hash)}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {block.timestamp ? new Date(block.timestamp).toLocaleString() : 'Unknown'}
                      </p>
                    </div>
                    <FiChevronRight className="text-gray-400" />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Block Details */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Block Details
          </h3>
          {selectedBlock ? (
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Block Number</p>
                <p className="font-mono text-gray-900 dark:text-white">#{selectedBlock.index}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Block Hash</p>
                <p className="font-mono text-xs text-gray-900 dark:text-white break-all">
                  {selectedBlock.hash}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Previous Hash</p>
                <p className="font-mono text-xs text-gray-900 dark:text-white break-all">
                  {selectedBlock.previous_hash}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Timestamp</p>
                <p className="text-gray-900 dark:text-white">
                  {selectedBlock.timestamp ? new Date(selectedBlock.timestamp).toLocaleString() : 'Unknown'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Miner</p>
                <p className="font-mono text-xs text-gray-900 dark:text-white">
                  {selectedBlock.miner || 'Unknown'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Difficulty</p>
                <p className="text-gray-900 dark:text-white">{selectedBlock.difficulty}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">Nonce</p>
                <p className="text-gray-900 dark:text-white">{selectedBlock.nonce}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                  Transactions ({selectedBlock.transactions?.length || 0})
                </p>
                <div className="space-y-2 max-h-40 overflow-y-auto scrollbar-thin">
                  {selectedBlock.transactions?.map((tx, index) => (
                    <div key={index} className="p-2 bg-gray-50 dark:bg-gray-800 rounded text-xs">
                      <p className="text-gray-900 dark:text-white">
                        {tx.sender} → {tx.recipient}
                      </p>
                      <p className="text-gray-500 dark:text-gray-400">
                        Amount: {tx.amount}
                      </p>
                    </div>
                  )) || <p className="text-gray-500 dark:text-gray-400">No transactions</p>}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              Select a block to view details
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default BlockchainExplorer