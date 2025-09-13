import React from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import { FiHome, FiBox, FiSend, FiCreditCard, FiServer, FiDroplet } from 'react-icons/fi'
import Dashboard from './components/Dashboard'
import BlockchainExplorer from './components/BlockchainExplorer'
import Transaction from './components/Transaction'
import NodeStatus from './components/NodeStatus'
import WalletManager from './components/WalletManager'
import Faucet from './components/Faucet'

function App() {
  const navItems = [
    { path: '/', icon: FiHome, label: 'Dashboard' },
    { path: '/blockchain', icon: FiBox, label: 'Blockchain' },
    { path: '/transaction', icon: FiSend, label: 'Send' },
    { path: '/wallet', icon: FiCreditCard, label: 'Wallet' },
    { path: '/nodes', icon: FiServer, label: 'Nodes' },
    { path: '/faucet', icon: FiDroplet, label: 'Faucet' },
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-200">
      {/* Header */}
      <header className="bg-white dark:bg-dark-100 shadow-sm border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-2xl font-bold text-primary-600">DeCoin</h1>
              </div>
              <nav className="ml-10">
                <div className="flex space-x-4">
                  {navItems.map((item) => (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      className={({ isActive }) =>
                        `flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                          isActive
                            ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
                            : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
                        }`
                      }
                    >
                      <item.icon className="mr-2" size={18} />
                      {item.label}
                    </NavLink>
                  ))}
                </div>
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <span className="text-sm text-gray-500 dark:text-gray-400 mr-2">Network:</span>
                <span className="badge badge-success">Connected</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/blockchain" element={<BlockchainExplorer />} />
          <Route path="/transaction" element={<Transaction />} />
          <Route path="/wallet" element={<WalletManager />} />
          <Route path="/nodes" element={<NodeStatus />} />
          <Route path="/faucet" element={<Faucet />} />
        </Routes>
      </main>
    </div>
  )
}

export default App