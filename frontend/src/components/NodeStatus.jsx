import React, { useState } from 'react'
import { useQuery, useMutation } from 'react-query'
import { FiServer, FiWifi, FiCpu, FiHardDrive, FiRefreshCw, FiPlay, FiPause } from 'react-icons/fi'
import { nodeAPI, miningAPI } from '../services/api'
import toast from 'react-hot-toast'

function NodeStatus() {
  const [selectedNode, setSelectedNode] = useState(0)
  const nodes = [
    { name: 'Node 1', port: 11080, type: 'node', validator: 'validator1_address' },
    { name: 'Node 2', port: 11081, type: 'node', validator: 'validator2_address' },
    { name: 'Node 3', port: 11082, type: 'node', validator: 'validator3_address' },
    { name: 'Node 4', port: 11084, type: 'node', validator: 'validator4_address' },
    { name: 'Node 5', port: 11085, type: 'node', validator: 'validator5_address' },
    { name: 'Node 6', port: 11086, type: 'node', validator: 'validator6_address' },
    { name: 'Validator 1', port: 11083, type: 'validator', validator: 'primary_validator_address' },
    { name: 'Validator 2', port: 11087, type: 'validator', validator: 'validator7_address' },
  ]

  const { data: status, isLoading, refetch } = useQuery(
    ['nodeStatus', selectedNode],
    () => nodeAPI.getStatus(selectedNode),
    { refetchInterval: 5000 }
  )

  const { data: health } = useQuery(
    ['nodeHealth', selectedNode],
    () => nodeAPI.getHealth(selectedNode),
    { refetchInterval: 5000 }
  )

  const { data: peers } = useQuery(
    ['nodePeers', selectedNode],
    () => nodeAPI.getPeers(selectedNode),
    { refetchInterval: 10000 }
  )

  const miningMutation = useMutation(
    (action) => miningAPI[action === 'start' ? 'startMining' : 'stopMining'](selectedNode),
    {
      onSuccess: () => {
        toast.success(`Mining ${status?.is_mining ? 'stopped' : 'started'}`)
        refetch()
      },
      onError: () => {
        toast.error('Failed to change mining status')
      }
    }
  )

  const toggleMining = () => {
    miningMutation.mutate(status?.is_mining ? 'stop' : 'start')
  }

  const getStatusColor = (isHealthy) => {
    return isHealthy ? 'text-green-500' : 'text-red-500'
  }

  const getStatusBadge = (isHealthy) => {
    return isHealthy ? 'badge-success' : 'badge-error'
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Node Status</h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Monitor and manage blockchain nodes
        </p>
      </div>

      {/* Node Selector */}
      <div className="card">
        <div className="flex flex-wrap gap-2">
          {nodes.map((node, index) => (
            <button
              key={index}
              onClick={() => setSelectedNode(index)}
              className={`px-3 py-2 rounded-lg font-medium transition-colors flex items-center gap-1 ${
                selectedNode === index
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              {node.type === 'validator' && (
                <span className="text-yellow-400">⭐</span>
              )}
              {node.name}
              <span className="text-xs opacity-60">
                :{node.port}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Node Info Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Status</p>
              <p className="mt-2">
                <span className={`badge ${health?.status === 'healthy' ? 'badge-success' : 'badge-error'}`}>
                  {health?.status || 'Unknown'}
                </span>
              </p>
            </div>
            <FiServer className={`h-8 w-8 ${getStatusColor(health?.status === 'healthy')}`} />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Chain Height</p>
              <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
                {isLoading ? '...' : status?.chain_height || 0}
              </p>
            </div>
            <FiHardDrive className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Connected Peers</p>
              <p className="mt-2 text-2xl font-bold text-gray-900 dark:text-white">
                {isLoading ? '...' : status?.connected_peers || 0}
              </p>
            </div>
            <FiWifi className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Mining</p>
              <p className="mt-2">
                <span className={`badge ${status?.is_mining ? 'badge-success' : 'badge-warning'}`}>
                  {status?.is_mining ? 'Active' : 'Inactive'}
                </span>
              </p>
            </div>
            <FiCpu className={`h-8 w-8 ${status?.is_mining ? 'text-green-500' : 'text-gray-400'}`} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Node Details */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Node Information
            </h3>
            <button
              onClick={() => refetch()}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            >
              <FiRefreshCw className="h-4 w-4" />
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Node ID</p>
              <p className="font-mono text-sm text-gray-900 dark:text-white">
                {status?.node_id || 'Unknown'}
              </p>
            </div>

            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Node Type</p>
              <p className="text-gray-900 dark:text-white">
                {nodes[selectedNode]?.type === 'validator' ? (
                  <span className="badge badge-primary">⭐ Validator</span>
                ) : (
                  <span className="badge badge-info">Mining Node</span>
                )}
              </p>
            </div>

            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Validator Address</p>
              <p className="font-mono text-xs text-gray-900 dark:text-white break-all">
                {nodes[selectedNode]?.validator || 'None'}
              </p>
            </div>

            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Version</p>
              <p className="text-gray-900 dark:text-white">{status?.version || '1.0.0'}</p>
            </div>

            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Uptime</p>
              <p className="text-gray-900 dark:text-white">
                {status?.uptime ? `${Math.floor(status.uptime / 60)} minutes` : 'Unknown'}
              </p>
            </div>

            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Difficulty</p>
              <p className="text-gray-900 dark:text-white">{status?.difficulty || 0}</p>
            </div>

            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Pending Transactions</p>
              <p className="text-gray-900 dark:text-white">{status?.pending_transactions || 0}</p>
            </div>

            <div className="pt-4">
              <button
                onClick={toggleMining}
                disabled={miningMutation.isLoading}
                className={`w-full flex items-center justify-center gap-2 ${
                  status?.is_mining ? 'btn-secondary' : 'btn-primary'
                }`}
              >
                {status?.is_mining ? (
                  <>
                    <FiPause /> Stop Mining
                  </>
                ) : (
                  <>
                    <FiPlay /> Start Mining
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Peer List */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Connected Peers ({peers?.length || 0})
          </h3>

          <div className="space-y-2 max-h-96 overflow-y-auto scrollbar-thin">
            {peers && peers.length > 0 ? (
              peers.map((peer, index) => {
                // Handle both object and string formats
                const isObject = typeof peer === 'object' && peer !== null;

                // Determine display values
                let displayName = 'Peer';
                let displayAddress = '';
                let displayVersion = '';
                let lastSeen = '';

                if (isObject) {
                  // Map IP addresses to node names based on Docker network
                  // 172.28.0.2 = node1, .3 = node2, .4 = node3, .5 = validator
                  if (peer.address === '172.28.0.2') displayName = 'Node 1';
                  else if (peer.address === '172.28.0.3') displayName = 'Node 2';
                  else if (peer.address === '172.28.0.4') displayName = 'Node 3';
                  else if (peer.address === '172.28.0.5') displayName = 'Validator';
                  else if (peer.node_id) displayName = peer.node_id;
                  else displayName = `Peer (${peer.address})`;

                  displayAddress = `${peer.address}:${peer.port}`;
                  displayVersion = peer.version || '1.0.0';

                  if (peer.last_seen) {
                    const date = new Date(peer.last_seen);
                    const now = new Date();
                    const diffMs = now - date;
                    const diffSecs = Math.floor(diffMs / 1000);
                    if (diffSecs < 60) {
                      lastSeen = `${diffSecs}s ago`;
                    } else if (diffSecs < 3600) {
                      lastSeen = `${Math.floor(diffSecs / 60)}m ago`;
                    } else {
                      lastSeen = `${Math.floor(diffSecs / 3600)}h ago`;
                    }
                  }
                } else {
                  // String format
                  displayName = peer;
                  displayAddress = peer;
                }

                return (
                  <div key={index} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-gray-900 dark:text-white">
                            {displayName}
                          </p>
                          {displayVersion && (
                            <span className="text-xs px-2 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">
                              v{displayVersion}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {displayAddress}
                        </p>
                        {lastSeen && (
                          <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
                            Last seen: {lastSeen}
                          </p>
                        )}
                      </div>
                      <span className="badge badge-success">Connected</span>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No peers connected
              </div>
            )}
          </div>

          {/* Network Stats */}
          <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
              Network Statistics
            </p>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <p className="text-gray-500 dark:text-gray-400">Total Nodes</p>
                <p className="font-semibold text-gray-900 dark:text-white">8</p>
              </div>
              <div>
                <p className="text-gray-500 dark:text-gray-400">Active Miners</p>
                <p className="font-semibold text-gray-900 dark:text-white">
                  {status?.is_mining ? '1+' : '0'}
                </p>
              </div>
              <div>
                <p className="text-gray-500 dark:text-gray-400">Network Hash Rate</p>
                <p className="font-semibold text-gray-900 dark:text-white">
                  {status?.difficulty || 0} H/s
                </p>
              </div>
              <div>
                <p className="text-gray-500 dark:text-gray-400">Consensus</p>
                <p className="font-semibold text-gray-900 dark:text-white">PoW/PoS</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NodeStatus