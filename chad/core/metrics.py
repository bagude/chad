"""Quality metrics tracking and reporting for CHAD system."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MetricType(Enum):
    """Types of metrics that can be tracked."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    DURATION = "duration"


@dataclass
class MetricValue:
    """Represents a single metric measurement."""
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)


class QualityMetric:
    """Base class for tracking quality metrics."""

    def __init__(
        self,
        name: str,
        type: MetricType,
        description: str,
        unit: str = ""
    ):
        self.name = name
        self.type = type
        self.description = description
        self.unit = unit
        self._values: List[MetricValue] = []

    def record(self, value: float, **labels) -> None:
        """Record a new metric value."""
        self._values.append(MetricValue(value=value, labels=labels))

    def get_latest(self) -> Optional[MetricValue]:
        """Get the most recent metric value."""
        return self._values[-1] if self._values else None

    def get_values(self) -> List[MetricValue]:
        """Get all recorded values."""
        return self._values.copy()


class MetricsRegistry:
    """Central registry for all quality metrics."""

    def __init__(self):
        self._metrics: Dict[str, QualityMetric] = {}

    def register(self, metric: QualityMetric) -> None:
        """Register a new metric."""
        if metric.name in self._metrics:
            raise ValueError(f"Metric {metric.name} already registered")
        self._metrics[metric.name] = metric

    def get_metric(self, name: str) -> QualityMetric:
        """Get a metric by name."""
        if name not in self._metrics:
            raise KeyError(f"Metric {name} not found")
        return self._metrics[name]

    def get_all_metrics(self) -> Dict[str, QualityMetric]:
        """Get all registered metrics."""
        return self._metrics.copy()

    def record(self, name: str, value: float, **labels) -> None:
        """Record a value for a named metric."""
        self.get_metric(name).record(value, **labels)


class QualityMetrics:
    """Quality metrics collection for content processing."""

    def __init__(self):
        self.registry = MetricsRegistry()
        self._setup_default_metrics()

    def _setup_default_metrics(self):
        """Setup default quality metrics."""
        self.registry.register(QualityMetric(
            name="processing_time",
            type=MetricType.DURATION,
            description="Time taken to process content",
            unit="seconds"
        ))

        self.registry.register(QualityMetric(
            name="content_length",
            type=MetricType.GAUGE,
            description="Length of processed content",
            unit="chars"
        ))

        self.registry.register(QualityMetric(
            name="error_count",
            type=MetricType.COUNTER,
            description="Number of processing errors"
        ))

    def get_metrics_report(self) -> Dict[str, Any]:
        """Generate a report of all metrics."""
        report = {}
        for name, metric in self.registry.get_all_metrics().items():
            latest = metric.get_latest()
            report[name] = {
                "type": metric.type.value,
                "description": metric.description,
                "unit": metric.unit,
                "latest_value": latest.value if latest else None,
                "latest_timestamp": latest.timestamp if latest else None
            }
        return report
