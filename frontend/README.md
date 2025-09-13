# DeCoin Frontend

A modern React-based web interface for the DeCoin blockchain network.

## Features

- **Dashboard**: Real-time overview of blockchain metrics and network status
- **Blockchain Explorer**: Browse blocks and transactions
- **Transaction Manager**: Send various types of transactions (standard, multi-sig, time-locked, data storage)
- **Wallet Manager**: Manage wallets and view transaction history
- **Node Monitor**: Monitor and control blockchain nodes

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **React Query** - Server state management
- **Recharts** - Data visualization
- **Axios** - HTTP client

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development Server

```bash
npm run dev
```

The app will be available at http://localhost:3000 (development) or http://localhost:10000 (Docker)

### Build for Production

```bash
npm run build
```

## Docker

### Build Image

```bash
docker build -t decoin-frontend .
```

### Run Container

```bash
docker run -p 10000:80 decoin-frontend
```

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:10080
VITE_WS_URL=ws://localhost:6001
```

## API Integration

The frontend connects to the DeCoin API endpoints:

- `/status` - Node status
- `/blockchain` - Blockchain data
- `/transaction` - Send transactions
- `/mempool` - Pending transactions
- `/balance/{address}` - Wallet balance
- `/peers` - Connected peers
- `/mine` - Mining control

## UI Components

### Dashboard
- Network statistics
- Recent blocks
- Transaction volume charts
- Block time visualization

### Blockchain Explorer
- Block search by number or hash
- Block details view
- Transaction list
- Network statistics

### Transaction Manager
- Multiple transaction types support
- Form validation
- Mempool monitoring
- Fee estimation

### Wallet Manager
- Balance checking
- Transaction history
- Wallet generation
- Import/Export functionality

### Node Monitor
- Node selection
- Real-time status updates
- Mining control
- Peer management

## Styling

The app uses Tailwind CSS with a custom color scheme:

- Primary: Blue (#3B82F6)
- Dark mode support
- Responsive design
- Custom components

## Performance

- Code splitting
- Lazy loading
- Optimized bundle size
- Caching strategies
- Gzip compression

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## License

MIT