"""
Monitoring service for MARIA project
"""

import time
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    load_average: List[float]
    timestamp: str

@dataclass
class APIMetrics:
    """API performance metrics"""
    total_requests: int
    requests_per_minute: float
    avg_response_time_ms: float
    error_rate_percent: float
    status_codes: Dict[int, int]
    endpoint_stats: Dict[str, Dict[str, Any]]
    timestamp: str

@dataclass
class ServiceMetrics:
    """External service metrics"""
    database_connected: bool
    redis_connected: bool
    llm_requests_total: int
    llm_errors_total: int
    llm_avg_response_time_ms: float
    external_api_calls: Dict[str, Dict[str, Any]]
    timestamp: str

class MonitoringService:
    """Service for collecting and analyzing system metrics"""
    
    def __init__(self, history_minutes: int = 60):
        self.history_minutes = history_minutes
        self.max_history_points = history_minutes * 2  # Store 2 points per minute
        
        # Metrics storage
        self.system_metrics_history = deque(maxlen=self.max_history_points)
        self.api_metrics_history = deque(maxlen=self.max_history_points)
        self.service_metrics_history = deque(maxlen=self.max_history_points)
        
        # Request tracking
        self.request_times = deque(maxlen=1000)  # Last 1000 requests
        self.request_counts = defaultdict(int)
        self.error_counts = defaultdict(int)
        self.endpoint_metrics = defaultdict(lambda: {
            'count': 0, 
            'total_time': 0, 
            'errors': 0,
            'avg_time': 0
        })
        
        # Service tracking
        self.llm_requests = 0
        self.llm_errors = 0
        self.llm_total_time = 0
        self.external_api_stats = defaultdict(lambda: {
            'calls': 0,
            'errors': 0,
            'total_time': 0,
            'avg_time': 0,
            'last_call': None
        })
        
        self.start_time = time.time()
    
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / 1024 / 1024
            memory_total_mb = memory.total / 1024 / 1024
            
            # Disk
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / 1024 / 1024 / 1024
            disk_total_gb = disk.total / 1024 / 1024 / 1024
            
            # Load average (Unix only)
            try:
                load_avg = list(os.getloadavg())
            except (AttributeError, OSError):
                load_avg = [0.0, 0.0, 0.0]
            
            metrics = SystemMetrics(
                cpu_percent=round(cpu_percent, 2),
                memory_percent=round(memory_percent, 2),
                memory_used_mb=round(memory_used_mb, 2),
                memory_total_mb=round(memory_total_mb, 2),
                disk_percent=round(disk_percent, 2),
                disk_used_gb=round(disk_used_gb, 2),
                disk_total_gb=round(disk_total_gb, 2),
                load_average=[round(x, 2) for x in load_avg],
                timestamp=datetime.utcnow().isoformat()
            )
            
            self.system_metrics_history.append(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(0, 0, 0, 0, 0, 0, 0, [0, 0, 0], datetime.utcnow().isoformat())
    
    def record_api_request(self, method: str, path: str, status_code: int, response_time_ms: float):
        """Record an API request for metrics"""
        now = time.time()
        
        # Store request time
        self.request_times.append(now)
        
        # Update counters
        self.request_counts[status_code] += 1
        if status_code >= 400:
            self.error_counts[f"{method} {path}"] += 1
        
        # Update endpoint metrics
        endpoint_key = f"{method} {path}"
        endpoint_stats = self.endpoint_metrics[endpoint_key]
        endpoint_stats['count'] += 1
        endpoint_stats['total_time'] += response_time_ms
        endpoint_stats['avg_time'] = endpoint_stats['total_time'] / endpoint_stats['count']
        if status_code >= 400:
            endpoint_stats['errors'] += 1
    
    def record_llm_request(self, response_time_ms: float, success: bool = True):
        """Record an LLM request"""
        self.llm_requests += 1
        self.llm_total_time += response_time_ms
        if not success:
            self.llm_errors += 1
    
    def record_external_api_call(self, service: str, response_time_ms: float, success: bool = True):
        """Record an external API call"""
        stats = self.external_api_stats[service]
        stats['calls'] += 1
        stats['total_time'] += response_time_ms
        stats['avg_time'] = stats['total_time'] / stats['calls']
        stats['last_call'] = datetime.utcnow().isoformat()
        if not success:
            stats['errors'] += 1
    
    def collect_api_metrics(self) -> APIMetrics:
        """Collect current API metrics"""
        try:
            now = time.time()
            
            # Calculate requests per minute
            recent_requests = [t for t in self.request_times if now - t <= 60]
            requests_per_minute = len(recent_requests)
            
            # Calculate average response time
            total_requests = sum(endpoint['count'] for endpoint in self.endpoint_metrics.values())
            total_time = sum(endpoint['total_time'] for endpoint in self.endpoint_metrics.values())
            avg_response_time = total_time / total_requests if total_requests > 0 else 0
            
            # Calculate error rate
            total_errors = sum(endpoint['errors'] for endpoint in self.endpoint_metrics.values())
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
            
            # Status code distribution
            status_codes = dict(self.request_counts)
            
            # Endpoint statistics
            endpoint_stats = {}
            for endpoint, stats in self.endpoint_metrics.items():
                endpoint_stats[endpoint] = {
                    'requests': stats['count'],
                    'avg_response_time_ms': round(stats['avg_time'], 2),
                    'errors': stats['errors'],
                    'error_rate': round(stats['errors'] / stats['count'] * 100, 2) if stats['count'] > 0 else 0
                }
            
            metrics = APIMetrics(
                total_requests=total_requests,
                requests_per_minute=requests_per_minute,
                avg_response_time_ms=round(avg_response_time, 2),
                error_rate_percent=round(error_rate, 2),
                status_codes=status_codes,
                endpoint_stats=endpoint_stats,
                timestamp=datetime.utcnow().isoformat()
            )
            
            self.api_metrics_history.append(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting API metrics: {e}")
            return APIMetrics(0, 0, 0, 0, {}, {}, datetime.utcnow().isoformat())
    
    async def collect_service_metrics(self, database_service=None, cache_service=None) -> ServiceMetrics:
        """Collect service-specific metrics"""
        try:
            # Database status
            db_connected = False
            if database_service:
                try:
                    db_connected = await database_service.test_connection()
                except:
                    pass
            
            # Redis status
            redis_connected = False
            if cache_service:
                try:
                    health = await cache_service.health_check()
                    redis_connected = health.get('connected', False)
                except:
                    pass
            
            # LLM metrics
            llm_avg_time = self.llm_total_time / self.llm_requests if self.llm_requests > 0 else 0
            
            # External API stats
            external_api_calls = {}
            for service, stats in self.external_api_stats.items():
                external_api_calls[service] = {
                    'total_calls': stats['calls'],
                    'errors': stats['errors'],
                    'avg_response_time_ms': round(stats['avg_time'], 2),
                    'error_rate': round(stats['errors'] / stats['calls'] * 100, 2) if stats['calls'] > 0 else 0,
                    'last_call': stats['last_call']
                }
            
            metrics = ServiceMetrics(
                database_connected=db_connected,
                redis_connected=redis_connected,
                llm_requests_total=self.llm_requests,
                llm_errors_total=self.llm_errors,
                llm_avg_response_time_ms=round(llm_avg_time, 2),
                external_api_calls=external_api_calls,
                timestamp=datetime.utcnow().isoformat()
            )
            
            self.service_metrics_history.append(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting service metrics: {e}")
            return ServiceMetrics(False, False, 0, 0, 0, {}, datetime.utcnow().isoformat())
    
    def get_uptime_seconds(self) -> float:
        """Get application uptime in seconds"""
        return time.time() - self.start_time
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        uptime_seconds = self.get_uptime_seconds()
        
        # Get latest metrics
        latest_system = self.system_metrics_history[-1] if self.system_metrics_history else None
        latest_api = self.api_metrics_history[-1] if self.api_metrics_history else None
        latest_service = self.service_metrics_history[-1] if self.service_metrics_history else None
        
        return {
            "uptime_seconds": round(uptime_seconds, 2),
            "uptime_formatted": self._format_uptime(uptime_seconds),
            "system_metrics": asdict(latest_system) if latest_system else None,
            "api_metrics": asdict(latest_api) if latest_api else None,
            "service_metrics": asdict(latest_service) if latest_service else None,
            "history_points": len(self.system_metrics_history),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        else:
            days = int(seconds // 86400)
            hours = int((seconds % 86400) // 3600)
            return f"{days}d {hours}h"
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get system alerts based on thresholds"""
        alerts = []
        
        if self.system_metrics_history:
            latest = self.system_metrics_history[-1]
            
            # CPU alert
            if latest.cpu_percent > 80:
                alerts.append({
                    "type": "warning" if latest.cpu_percent < 90 else "error",
                    "message": f"High CPU usage: {latest.cpu_percent}%",
                    "metric": "cpu",
                    "value": latest.cpu_percent
                })
            
            # Memory alert
            if latest.memory_percent > 85:
                alerts.append({
                    "type": "warning" if latest.memory_percent < 95 else "error",
                    "message": f"High memory usage: {latest.memory_percent}%",
                    "metric": "memory",
                    "value": latest.memory_percent
                })
            
            # Disk alert
            if latest.disk_percent > 90:
                alerts.append({
                    "type": "warning" if latest.disk_percent < 95 else "error",
                    "message": f"High disk usage: {latest.disk_percent}%",
                    "metric": "disk",
                    "value": latest.disk_percent
                })
        
        # API error rate alert
        if self.api_metrics_history:
            latest_api = self.api_metrics_history[-1]
            if latest_api.error_rate_percent > 10:
                alerts.append({
                    "type": "warning" if latest_api.error_rate_percent < 25 else "error",
                    "message": f"High API error rate: {latest_api.error_rate_percent}%",
                    "metric": "api_errors",
                    "value": latest_api.error_rate_percent
                })
        
        return alerts

# Global monitoring service instance
monitoring_service = MonitoringService()
