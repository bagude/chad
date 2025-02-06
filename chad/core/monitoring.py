"""Performance monitoring system for CHAD."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from contextlib import contextmanager
from time import perf_counter
from .metrics import MetricsRegistry, QualityMetric, MetricType


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics at a point in time."""
    timestamp: datetime
    metrics: Dict[str, float]
    context: Dict[str, Any]


class PerformanceMonitor:
    """Monitors and tracks system performance metrics."""

    def __init__(self, metrics_registry: MetricsRegistry):
        self.metrics_registry = metrics_registry
        self._snapshots: List[PerformanceSnapshot] = []
        self._setup_performance_metrics()

    def _setup_performance_metrics(self) -> None:
        """Setup default performance metrics."""
        self.metrics_registry.register(QualityMetric(
            name="cpu_usage",
            type=MetricType.GAUGE,
            description="CPU usage percentage",
            unit="percent"
        ))

        self.metrics_registry.register(QualityMetric(
            name="memory_usage",
            type=MetricType.GAUGE,
            description="Memory usage",
            unit="bytes"
        ))

        self.metrics_registry.register(QualityMetric(
            name="latency",
            type=MetricType.HISTOGRAM,
            description="Operation latency",
            unit="seconds"
        ))

    def take_snapshot(self, context: Dict[str, Any] = None) -> PerformanceSnapshot:
        """Take a snapshot of current performance metrics."""
        metrics = {}
        for name, metric in self.metrics_registry.get_all_metrics().items():
            latest = metric.get_latest()
            if latest:
                metrics[name] = latest.value

        snapshot = PerformanceSnapshot(
            timestamp=datetime.now(),
            metrics=metrics,
            context=context or {}
        )
        self._snapshots.append(snapshot)
        return snapshot

    def get_snapshots(self,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None) -> List[PerformanceSnapshot]:
        """Get performance snapshots within the specified time range."""
        if not start_time:
            start_time = datetime.min
        if not end_time:
            end_time = datetime.max

        return [
            snapshot for snapshot in self._snapshots
            if start_time <= snapshot.timestamp <= end_time
        ]

    @contextmanager
    def measure_time(self, operation_name: str, **labels):
        """Context manager to measure operation execution time."""
        start_time = perf_counter()
        try:
            yield
        finally:
            end_time = perf_counter()
            duration = end_time - start_time
            self.metrics_registry.record("latency", duration,
                                         operation=operation_name, **labels)

    def get_performance_report(self,
                               window: timedelta = timedelta(minutes=5)) -> Dict[str, Any]:
        """Generate a performance report for the specified time window."""
        end_time = datetime.now()
        start_time = end_time - window
        snapshots = self.get_snapshots(start_time, end_time)

        if not snapshots:
            return {"error": "No data available for the specified time window"}

        metrics_summary = {}
        for name in self.metrics_registry.get_all_metrics().keys():
            values = [s.metrics.get(name)
                      for s in snapshots if name in s.metrics]
            if values:
                metrics_summary[name] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "samples": len(values)
                }

        return {
            "time_window": {
                "start": start_time,
                "end": end_time
            },
            "metrics": metrics_summary,
            "total_snapshots": len(snapshots)
        }
