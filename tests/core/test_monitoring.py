import pytest
from datetime import datetime, timedelta
from time import sleep
from chad.core.monitoring import (
    PerformanceSnapshot,
    PerformanceMonitor
)
from chad.core.metrics import MetricsRegistry


def test_performance_snapshot():
    """Test performance snapshot creation."""
    metrics = {"cpu": 50.0, "memory": 1024.0}
    context = {"service": "test"}

    snapshot = PerformanceSnapshot(
        timestamp=datetime.now(),
        metrics=metrics,
        context=context
    )

    assert snapshot.metrics == metrics
    assert snapshot.context == context


def test_performance_monitor_setup():
    """Test performance monitor initialization."""
    registry = MetricsRegistry()
    monitor = PerformanceMonitor(registry)

    metrics = registry.get_all_metrics()
    assert "cpu_usage" in metrics
    assert "memory_usage" in metrics
    assert "latency" in metrics


def test_performance_snapshot_taking():
    """Test taking performance snapshots."""
    registry = MetricsRegistry()
    monitor = PerformanceMonitor(registry)

    # Record some metrics
    registry.record("cpu_usage", 45.0)
    registry.record("memory_usage", 2048.0)

    snapshot = monitor.take_snapshot({"env": "test"})
    assert snapshot.metrics["cpu_usage"] == 45.0
    assert snapshot.metrics["memory_usage"] == 2048.0
    assert snapshot.context["env"] == "test"


def test_time_measurement():
    """Test operation time measurement."""
    registry = MetricsRegistry()
    monitor = PerformanceMonitor(registry)

    with monitor.measure_time("test_operation", env="test"):
        sleep(0.1)  # Simulate work

    latest = registry.get_metric("latency").get_latest()
    assert latest.value >= 0.1
    assert latest.labels["operation"] == "test_operation"
    assert latest.labels["env"] == "test"


def test_performance_report():
    """Test performance report generation."""
    registry = MetricsRegistry()
    monitor = PerformanceMonitor(registry)

    # Record some metrics over time
    registry.record("cpu_usage", 40.0)
    monitor.take_snapshot()

    registry.record("cpu_usage", 50.0)
    monitor.take_snapshot()

    report = monitor.get_performance_report(window=timedelta(minutes=1))

    assert report["total_snapshots"] == 2
    assert "time_window" in report
    assert "metrics" in report
    assert report["metrics"]["cpu_usage"]["min"] == 40.0
    assert report["metrics"]["cpu_usage"]["max"] == 50.0
    assert report["metrics"]["cpu_usage"]["avg"] == 45.0


def test_snapshot_filtering():
    """Test snapshot filtering by time range."""
    registry = MetricsRegistry()
    monitor = PerformanceMonitor(registry)

    # Create snapshots at different times
    old_time = datetime.now() - timedelta(minutes=10)
    new_time = datetime.now()

    monitor._snapshots = [
        PerformanceSnapshot(old_time, {"cpu": 40.0}, {}),
        PerformanceSnapshot(new_time, {"cpu": 50.0}, {})
    ]

    # Filter last 5 minutes
    recent = monitor.get_snapshots(
        start_time=datetime.now() - timedelta(minutes=5)
    )
    assert len(recent) == 1
    assert recent[0].metrics["cpu"] == 50.0
