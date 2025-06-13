from prometheus_client import Counter, Histogram, Gauge
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI
import structlog
import time
from typing import Dict, Any
import json
from datetime import datetime

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Prometheus metrics
WORKFLOW_EXECUTION_TIME = Histogram(
    'workflow_execution_seconds',
    'Time spent executing workflows',
    ['workflow_name']
)

WORKFLOW_REQUESTS = Counter(
    'workflow_requests_total',
    'Total number of workflow requests',
    ['workflow_name', 'status']
)

ACTIVE_JOBS = Gauge(
    'active_jobs',
    'Number of active jobs',
    ['status']
)

DB_CONNECTION_POOL = Gauge(
    'db_connection_pool',
    'Database connection pool metrics',
    ['metric']
)

class MonitoringManager:
    def __init__(self, app: FastAPI):
        self.app = app
        self._setup_instrumentation()
        self._setup_metrics()
    
    def _setup_instrumentation(self):
        """Set up FastAPI instrumentation"""
        Instrumentator().instrument(self.app).expose(self.app)
    
    def _setup_metrics(self):
        """Initialize Prometheus metrics"""
        # Initialize metrics with default values
        ACTIVE_JOBS.labels(status='pending').set(0)
        ACTIVE_JOBS.labels(status='running').set(0)
        ACTIVE_JOBS.labels(status='completed').set(0)
        ACTIVE_JOBS.labels(status='failed').set(0)
    
    def track_workflow_execution(self, workflow_name: str, start_time: float):
        """Track workflow execution time"""
        execution_time = time.time() - start_time
        WORKFLOW_EXECUTION_TIME.labels(workflow_name=workflow_name).observe(execution_time)
    
    def track_workflow_request(self, workflow_name: str, status: str):
        """Track workflow request count"""
        WORKFLOW_REQUESTS.labels(workflow_name=workflow_name, status=status).inc()
    
    def update_active_jobs(self, status_counts: Dict[str, int]):
        """Update active jobs gauge"""
        for status, count in status_counts.items():
            ACTIVE_JOBS.labels(status=status).set(count)
    
    def update_db_pool_metrics(self, pool_metrics: Dict[str, Any]):
        """Update database connection pool metrics"""
        for metric, value in pool_metrics.items():
            DB_CONNECTION_POOL.labels(metric=metric).set(value)
    
    def log_workflow_event(self, event_type: str, data: Dict[str, Any]):
        """Log workflow events with structured logging"""
        logger.info(
            event_type,
            timestamp=datetime.utcnow().isoformat(),
            **data
        )
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Log errors with structured logging"""
        logger.error(
            error_type,
            error_message=error_message,
            timestamp=datetime.utcnow().isoformat(),
            **(context or {})
        )

# Create global instance
monitoring = None

def init_monitoring(app: FastAPI) -> MonitoringManager:
    """Initialize monitoring for the application"""
    global monitoring
    monitoring = MonitoringManager(app)
    return monitoring 