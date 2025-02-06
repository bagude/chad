import pytest
from datetime import datetime, timedelta
from chad.core.metrics import (
    MetricType,
    MetricValue,
    QualityMetric,
    MetricsRegistry,
    QualityMetrics
)


def test_metric_value():
    """Test metric value creation and attributes."""
    value = MetricValue(
        value=42.0,
        labels={"env": "test"}
    )

    assert value.value == 42.0
    assert isinstance(value.timestamp, datetime)
    assert value.labels == {"env": "test"}


def test_quality_metric():
    """Test quality metric functionality."""
    metric = QualityMetric(
        name="test_metric",
        type=MetricType.COUNTER,
        description="Test metric",
        unit="count"
    )

    metric.record(1.0, env="test")
    metric.record(2.0, env="prod")

    assert len(metric.get_values()) == 2
    assert metric.get_latest().value == 2.0


def test_metrics_registry():
    """Test metrics registry operations."""
    registry = MetricsRegistry()

    metric = QualityMetric(
        name="test_metric",
        type=MetricType.GAUGE,
        description="Test metric"
    )

    registry.register(metric)
    assert "test_metric" in registry.get_all_metrics()

    with pytest.raises(ValueError):
        registry.register(metric)  # Duplicate registration

    with pytest.raises(KeyError):
        registry.get_metric("non_existent")


def test_quality_metrics():
    """Test quality metrics collection."""
    metrics = QualityMetrics()

    # Test default metrics exist
    assert "processing_time" in metrics.registry.get_all_metrics()
    assert "content_length" in metrics.registry.get_all_metrics()
    assert "error_count" in metrics.registry.get_all_metrics()

    # Test recording values
    metrics.registry.record("processing_time", 1.5)
    metrics.registry.record("content_length", 100)

    # Test metrics report
    report = metrics.get_metrics_report()
    assert report["processing_time"]["latest_value"] == 1.5
    assert report["content_length"]["latest_value"] == 100


def test_metric_labels():
    """Test metric labeling functionality."""
    metric = QualityMetric(
        name="test_metric",
        type=MetricType.COUNTER,
        description="Test metric"
    )

    metric.record(1.0, service="auth", env="prod")
    metric.record(2.0, service="auth", env="dev")

    values = metric.get_values()
    assert values[0].labels == {"service": "auth", "env": "prod"}
    assert values[1].labels == {"service": "auth", "env": "dev"}
