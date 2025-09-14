import axios from 'axios'

const API_BASE_URL = '/api'

// Node configurations
const NODES = {
  0: { name: 'Node 1', port: 11080, path: '/api' },
  1: { name: 'Node 2', port: 11081, path: '/api2' },
  2: { name: 'Node 3', port: 11082, path: '/api3' },
  3: { name: 'Node 4', port: 11084, path: '/api4' },
  4: { name: 'Node 5', port: 11085, path: '/api5' },
  5: { name: 'Node 6', port: 11086, path: '/api6' },
  6: { name: 'Validator 1', port: 11083, path: '/api-validator' },
  7: { name: 'Validator 2', port: 11087, path: '/api-validator2' },
}

// Create API instance with dynamic base URL
const createApiInstance = (nodeIndex = 0) => {
  const node = NODES[nodeIndex] || NODES[0]
  return axios.create({
    baseURL: node.path,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
  })
}

const api = createApiInstance()

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data)
    } else if (error.request) {
      console.error('Network Error:', error.request)
    } else {
      console.error('Error:', error.message)
    }
    return Promise.reject(error)
  }
)

// Blockchain endpoints
export const blockchainAPI = {
  getBlockchain: (start = 0, limit = 100) => {
    // If no parameters provided, fetch the most recent blocks
    if (start === 0 && limit === 100) {
      // Fetch all blocks to get the latest ones
      return api.get('/blockchain', { params: { start: 0, limit: 1000 } })
    }
    return api.get('/blockchain', { params: { start, limit } })
  },
  getBlock: (index) => api.get(`/block/${index}`),
  getLatestBlock: () => api.get('/blockchain/latest'),
  getBlockByHash: (hash) => api.get(`/block/hash/${hash}`),
  getRecentBlocks: async (count = 100) => {
    // First get the chain height
    const status = await api.get('/status')
    const chainHeight = status.data.chain_height
    // Calculate start index to get the most recent blocks
    const start = Math.max(0, chainHeight - count)
    console.log(`Fetching blocks from ${start} to ${start + count - 1} (chain height: ${chainHeight})`)
    return api.get('/blockchain', { params: { start, limit: count } })
  },
}

// Transaction endpoints
export const transactionAPI = {
  sendTransaction: (data) => api.post('/transaction', data),
  getTransaction: (id) => api.get(`/transaction/${id}`),
  getMempool: () => api.get('/mempool'),
  getTransactionHistory: (address) => api.get(`/transactions/${address}`),
}

// Node endpoints with dynamic node selection
export const nodeAPI = {
  getStatus: (nodeIndex = 0) => {
    const apiInstance = createApiInstance(nodeIndex)
    apiInstance.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )
    apiInstance.interceptors.response.use(
      (response) => response.data,
      (error) => {
        if (error.response) {
          console.error('API Error:', error.response.data)
        } else if (error.request) {
          console.error('Network Error:', error.request)
        } else {
          console.error('Error:', error.message)
        }
        return Promise.reject(error)
      }
    )
    return apiInstance.get('/status')
  },
  getHealth: (nodeIndex = 0) => {
    const apiInstance = createApiInstance(nodeIndex)
    apiInstance.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )
    apiInstance.interceptors.response.use(
      (response) => response.data,
      (error) => {
        if (error.response) {
          console.error('API Error:', error.response.data)
        } else if (error.request) {
          console.error('Network Error:', error.request)
        } else {
          console.error('Error:', error.message)
        }
        return Promise.reject(error)
      }
    )
    return apiInstance.get('/health')
  },
  getPeers: (nodeIndex = 0) => {
    const apiInstance = createApiInstance(nodeIndex)
    apiInstance.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )
    apiInstance.interceptors.response.use(
      (response) => response.data,
      (error) => {
        if (error.response) {
          console.error('API Error:', error.response.data)
        } else if (error.request) {
          console.error('Network Error:', error.request)
        } else {
          console.error('Error:', error.message)
        }
        return Promise.reject(error)
      }
    )
    return apiInstance.get('/peers')
  },
  addPeer: (peer, nodeIndex = 0) => {
    const apiInstance = createApiInstance(nodeIndex)
    apiInstance.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )
    apiInstance.interceptors.response.use(
      (response) => response.data,
      (error) => {
        if (error.response) {
          console.error('API Error:', error.response.data)
        } else if (error.request) {
          console.error('Network Error:', error.request)
        } else {
          console.error('Error:', error.message)
        }
        return Promise.reject(error)
      }
    )
    return apiInstance.post('/peers', { peer })
  },
  removePeer: (peer, nodeIndex = 0) => {
    const apiInstance = createApiInstance(nodeIndex)
    apiInstance.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )
    apiInstance.interceptors.response.use(
      (response) => response.data,
      (error) => {
        if (error.response) {
          console.error('API Error:', error.response.data)
        } else if (error.request) {
          console.error('Network Error:', error.request)
        } else {
          console.error('Error:', error.message)
        }
        return Promise.reject(error)
      }
    )
    return apiInstance.delete(`/peers/${peer}`)
  },
}

// Mining endpoints with dynamic node selection
export const miningAPI = {
  startMining: (nodeIndex = 0) => {
    const apiInstance = createApiInstance(nodeIndex)
    apiInstance.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )
    apiInstance.interceptors.response.use(
      (response) => response.data,
      (error) => {
        if (error.response) {
          console.error('API Error:', error.response.data)
        } else if (error.request) {
          console.error('Network Error:', error.request)
        } else {
          console.error('Error:', error.message)
        }
        return Promise.reject(error)
      }
    )
    return apiInstance.post('/mine', { action: 'start' })
  },
  stopMining: (nodeIndex = 0) => {
    const apiInstance = createApiInstance(nodeIndex)
    apiInstance.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )
    apiInstance.interceptors.response.use(
      (response) => response.data,
      (error) => {
        if (error.response) {
          console.error('API Error:', error.response.data)
        } else if (error.request) {
          console.error('Network Error:', error.request)
        } else {
          console.error('Error:', error.message)
        }
        return Promise.reject(error)
      }
    )
    return apiInstance.post('/mine', { action: 'stop' })
  },
  getMiningStatus: (nodeIndex = 0) => {
    const apiInstance = createApiInstance(nodeIndex)
    apiInstance.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )
    apiInstance.interceptors.response.use(
      (response) => response.data,
      (error) => {
        if (error.response) {
          console.error('API Error:', error.response.data)
        } else if (error.request) {
          console.error('Network Error:', error.request)
        } else {
          console.error('Error:', error.message)
        }
        return Promise.reject(error)
      }
    )
    return apiInstance.get('/mining/status')
  },
}

// Wallet endpoints
export const walletAPI = {
  getBalance: (address) => api.get(`/balance/${address}`),
  createWallet: () => api.post('/wallet/create'),
  getWalletInfo: (address) => api.get(`/wallet/${address}`),
}

// Statistics endpoints
export const statsAPI = {
  getNetworkStats: () => api.get('/stats/network'),
  getBlockchainInfo: () => api.get('/stats/blockchain'),
  getPerformanceMetrics: () => api.get('/stats/performance'),
}

export default api