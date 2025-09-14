import React from 'react'
import { useQuery } from 'react-query'
import { FiBox, FiActivity, FiUsers, FiCpu } from 'react-icons/fi'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { nodeAPI, blockchainAPI, statsAPI } from '../services/api'

function Dashboard() {
  const { data: status, isLoading: statusLoading } = useQuery(
    'nodeStatus',
    nodeAPI.getStatus,
    { refetchInterval: 5000 }
  )

  const { data: blockchain, isLoading: blockchainLoading } = useQuery(
    'recentBlocks',
    () => blockchainAPI.getRecentBlocks(100),
    { refetchInterval: 10000 }
  )

  const stats = [
    {
      title: 'Block Height',
      value: status?.chain_height || 0,
      icon: FiBox,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      title: 'Pending Transactions',
      value: status?.pending_transactions || 0,
      icon: FiActivity,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      title: 'Connected Peers',
      value: status?.connected_peers || 0,
      icon: FiUsers,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      title: 'Mining',
      value: status?.is_mining ? 'Active' : 'Inactive',
      icon: FiCpu,
      color: status?.is_mining ? 'text-green-600' : 'text-gray-600',
      bgColor: status?.is_mining ? 'bg-green-100' : 'bg-gray-100',
    },
  ]

  // Generate mock chart data
  const chartData = blockchain?.blocks?.slice(-10).map((block, index) => ({
    name: `Block ${block.index}`,
    transactions: block.transactions?.length || 0,
    difficulty: block.difficulty || 0,
    timestamp: block.timestamp ? new Date(block.timestamp).toLocaleTimeString() : '',
  })) || []

  const blockTimeData = blockchain?.blocks?.slice(-20).map((block, index, array) => {
    if (index === 0) return null
    const prevTime = new Date(array[index - 1].timestamp).getTime()
    const currTime = new Date(block.timestamp).getTime()
    const timeDiff = Math.round((currTime - prevTime) / 1000) // Convert to seconds
    return {
      block: block.index,
      time: timeDiff,
      timestamp: block.timestamp ? new Date(block.timestamp).toLocaleTimeString() : '',
    }
  }).filter(Boolean) || []

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h2>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Real-time overview of the DeCoin blockchain network
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.title} className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">{stat.title}</p>
                <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                  {statusLoading ? (
                    <span className="skeleton h-8 w-20 inline-block"></span>
                  ) : (
                    stat.value
                  )}
                </p>
              </div>
              <div className={`p-3 rounded-full ${stat.bgColor}`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Transactions per Block */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Transactions per Block
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '8px',
                }}
              />
              <Area
                type="monotone"
                dataKey="transactions"
                stroke="#3B82F6"
                fill="#3B82F6"
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Block Time */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
            Block Time (seconds)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={blockTimeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="block" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '8px',
                }}
              />
              <Line
                type="monotone"
                dataKey="time"
                stroke="#10B981"
                strokeWidth={2}
                dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Blocks */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
          Recent Blocks
        </h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead>
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Index
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Hash
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Transactions
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Miner
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {blockchainLoading ? (
                <tr>
                  <td colSpan="5" className="px-6 py-4 text-center">
                    <div className="skeleton h-4 w-full"></div>
                  </td>
                </tr>
              ) : (
                blockchain?.blocks?.slice(-5).reverse().map((block) => (
                  <tr key={block.index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                      #{block.index}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      <code className="text-xs">
                        {block.hash?.substring(0, 16)}...
                      </code>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {block.transactions?.length || 0}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {block.timestamp ? new Date(block.timestamp).toLocaleString() : 'Unknown'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {block.miner?.substring(0, 8)}...
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default Dashboard