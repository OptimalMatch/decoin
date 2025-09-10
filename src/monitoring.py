"""
DeCoin Monitoring and Metrics System
Provides real-time monitoring, logging, and metrics collection
"""

import time
import json
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from collections import deque, defaultdict
from threading import Lock
import psutil
import asyncio


@dataclass
class Metric:
    """Single metric data point"""
    name: str
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HealthStatus:
    """System health status"""
    healthy: bool
    uptime: float
    checks: Dict[str, bool]
    issues: List[str]
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetricsCollector:
    """Collects and aggregates metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.lock = Lock()
        self.start_time = time.time()
    
    def record_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Record a counter metric"""
        with self.lock:
            self.counters[name] += value
            metric = Metric(name, self.counters[name], time.time(), tags or {})
            self.metrics[name].append(metric)
    
    def record_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a gauge metric"""
        with self.lock:
            self.gauges[name] = value
            metric = Metric(name, value, time.time(), tags or {})
            self.metrics[name].append(metric)
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram metric"""
        with self.lock:
            self.histograms[name].append(value)
            metric = Metric(name, value, time.time(), tags or {})
            self.metrics[name].append(metric)
    
    def get_counter(self, name: str) -> int:
        """Get current counter value"""
        return self.counters.get(name, 0)
    
    def get_gauge(self, name: str) -> Optional[float]:
        """Get current gauge value"""
        return self.gauges.get(name)
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics"""
        values = self.histograms.get(name, [])
        if not values:
            return {}
        
        return {
            'count': len(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values),
            'stddev': statistics.stdev(values) if len(values) > 1 else 0
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        with self.lock:
            return {
                'uptime': time.time() - self.start_time,
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'histograms': {
                    name: self.get_histogram_stats(name)
                    for name in self.histograms
                }
            }


class SystemMonitor:
    """Monitors system resources and blockchain health"""
    
    def __init__(self, blockchain=None, node=None):
        self.blockchain = blockchain
        self.node = node
        self.metrics = MetricsCollector()
        self.health_checks = {}
        self.alert_handlers = []
        self.monitoring = False
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup structured logging"""
        self.logger = logging.getLogger('decoin.monitor')
        self.logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler with JSON formatting
        file_handler = logging.FileHandler('decoin_monitor.log')
        file_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(file_handler)
    
    def collect_system_metrics(self):
        """Collect system resource metrics"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        self.metrics.record_gauge('system.cpu.percent', cpu_percent)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        self.metrics.record_gauge('system.memory.percent', memory.percent)
        self.metrics.record_gauge('system.memory.used', memory.used)
        self.metrics.record_gauge('system.memory.available', memory.available)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        self.metrics.record_gauge('system.disk.percent', disk.percent)
        self.metrics.record_gauge('system.disk.used', disk.used)
        self.metrics.record_gauge('system.disk.free', disk.free)
        
        # Network metrics
        net_io = psutil.net_io_counters()
        self.metrics.record_counter('system.network.bytes_sent', net_io.bytes_sent)
        self.metrics.record_counter('system.network.bytes_recv', net_io.bytes_recv)
    
    def collect_blockchain_metrics(self):
        """Collect blockchain-specific metrics"""
        if not self.blockchain:
            return
        
        # Chain metrics
        self.metrics.record_gauge('blockchain.height', len(self.blockchain.chain))
        self.metrics.record_gauge('blockchain.difficulty', self.blockchain.difficulty)
        self.metrics.record_gauge('blockchain.pending_transactions', 
                                  len(self.blockchain.pending_transactions))
        
        # Calculate transaction throughput
        if len(self.blockchain.chain) > 1:
            recent_blocks = self.blockchain.chain[-10:]
            total_tx = sum(len(block.transactions) for block in recent_blocks)
            time_span = recent_blocks[-1].timestamp - recent_blocks[0].timestamp
            if time_span > 0:
                tps = total_tx / time_span
                self.metrics.record_gauge('blockchain.transactions_per_second', tps)
    
    def collect_node_metrics(self):
        """Collect P2P node metrics"""
        if not self.node:
            return
        
        # Network metrics
        self.metrics.record_gauge('node.peers.connected', len(self.node.peers))
        self.metrics.record_counter('node.messages.sent', getattr(self.node, 'messages_sent', 0))
        self.metrics.record_counter('node.messages.received', getattr(self.node, 'messages_received', 0))
        
        # Mining metrics
        self.metrics.record_gauge('node.mining.active', 1 if getattr(self.node, 'is_mining', False) else 0)
        self.metrics.record_counter('node.blocks.mined', getattr(self.node, 'blocks_mined', 0))
    
    def check_health(self) -> HealthStatus:
        """Perform health checks"""
        checks = {}
        issues = []
        
        # System health checks
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        checks['cpu_ok'] = cpu_percent < 90
        if not checks['cpu_ok']:
            issues.append(f"High CPU usage: {cpu_percent}%")
        
        checks['memory_ok'] = memory_percent < 90
        if not checks['memory_ok']:
            issues.append(f"High memory usage: {memory_percent}%")
        
        checks['disk_ok'] = disk_percent < 90
        if not checks['disk_ok']:
            issues.append(f"High disk usage: {disk_percent}%")
        
        # Blockchain health checks
        if self.blockchain:
            checks['chain_valid'] = self.blockchain.validate_chain()
            if not checks['chain_valid']:
                issues.append("Blockchain validation failed")
            
            checks['mempool_ok'] = len(self.blockchain.pending_transactions) < 1000
            if not checks['mempool_ok']:
                issues.append(f"Mempool congestion: {len(self.blockchain.pending_transactions)} pending")
        
        # Node health checks
        if self.node:
            checks['peers_ok'] = len(getattr(self.node, 'peers', [])) > 0
            if not checks['peers_ok']:
                issues.append("No connected peers")
        
        healthy = all(checks.values())
        uptime = time.time() - self.metrics.start_time
        
        return HealthStatus(
            healthy=healthy,
            uptime=uptime,
            checks=checks,
            issues=issues,
            timestamp=time.time()
        )
    
    def register_alert_handler(self, handler):
        """Register an alert handler function"""
        self.alert_handlers.append(handler)
    
    def trigger_alert(self, level: str, message: str, details: Dict[str, Any] = None):
        """Trigger an alert"""
        alert = {
            'level': level,
            'message': message,
            'details': details or {},
            'timestamp': time.time()
        }
        
        # Log the alert
        if level == 'error':
            self.logger.error(f"Alert: {message}", extra=alert)
        elif level == 'warning':
            self.logger.warning(f"Alert: {message}", extra=alert)
        else:
            self.logger.info(f"Alert: {message}", extra=alert)
        
        # Call alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler error: {e}")
    
    async def start_monitoring(self, interval: int = 10):
        """Start continuous monitoring"""
        self.monitoring = True
        self.logger.info("Monitoring started")
        
        while self.monitoring:
            try:
                # Collect metrics
                self.collect_system_metrics()
                self.collect_blockchain_metrics()
                self.collect_node_metrics()
                
                # Check health
                health = self.check_health()
                if not health.healthy:
                    self.trigger_alert('warning', 'Health check failed', 
                                     {'issues': health.issues})
                
                # Log metrics summary periodically
                if int(time.time()) % 60 == 0:  # Every minute
                    summary = self.metrics.get_metrics_summary()
                    self.logger.info("Metrics summary", extra=summary)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                self.trigger_alert('error', f'Monitoring error: {e}')
            
            await asyncio.sleep(interval)
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        self.logger.info("Monitoring stopped")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        health = self.check_health()
        metrics = self.metrics.get_metrics_summary()
        
        return {
            'health': health.to_dict(),
            'metrics': metrics,
            'system': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            },
            'blockchain': {
                'height': len(self.blockchain.chain) if self.blockchain else 0,
                'pending_transactions': len(self.blockchain.pending_transactions) if self.blockchain else 0,
                'difficulty': self.blockchain.difficulty if self.blockchain else 0
            },
            'network': {
                'peers': len(getattr(self.node, 'peers', [])) if self.node else 0,
                'is_mining': getattr(self.node, 'is_mining', False) if self.node else False
            }
        }


class JsonFormatter(logging.Formatter):
    """JSON log formatter"""
    
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_obj.update(record.extra)
        
        return json.dumps(log_obj)


class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self):
        self.alerts = deque(maxlen=1000)
        self.alert_rules = []
        self.notification_channels = []
    
    def add_rule(self, name: str, condition, action):
        """Add an alert rule"""
        self.alert_rules.append({
            'name': name,
            'condition': condition,
            'action': action
        })
    
    def add_notification_channel(self, channel):
        """Add a notification channel"""
        self.notification_channels.append(channel)
    
    def process_metrics(self, metrics: Dict[str, Any]):
        """Process metrics and check alert rules"""
        for rule in self.alert_rules:
            try:
                if rule['condition'](metrics):
                    alert = {
                        'rule': rule['name'],
                        'triggered_at': time.time(),
                        'metrics': metrics
                    }
                    self.alerts.append(alert)
                    rule['action'](alert)
                    self.notify(alert)
            except Exception as e:
                logging.error(f"Error processing alert rule {rule['name']}: {e}")
    
    def notify(self, alert: Dict[str, Any]):
        """Send notifications through all channels"""
        for channel in self.notification_channels:
            try:
                channel.send(alert)
            except Exception as e:
                logging.error(f"Error sending notification: {e}")
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return list(self.alerts)[-limit:]


# Example alert rules
def high_cpu_rule(metrics):
    """Alert if CPU usage is too high"""
    cpu = metrics.get('gauges', {}).get('system.cpu.percent', 0)
    return cpu > 90

def mempool_congestion_rule(metrics):
    """Alert if mempool is congested"""
    pending = metrics.get('gauges', {}).get('blockchain.pending_transactions', 0)
    return pending > 500

def no_peers_rule(metrics):
    """Alert if no peers connected"""
    peers = metrics.get('gauges', {}).get('node.peers.connected', 0)
    return peers == 0