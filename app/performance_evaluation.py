"""
Varynx Day 39
Latency and Performance Evaluation

Measures operational characteristics of a security pipeline:

- total execution time
- average latency
- median latency
- p95 latency
- p99 latency
- throughput
- CPU usage
- memory usage

This module is an experimental measurement layer.
It does not implement a second security detector.
"""

from __future__ import annotations

import gc
import os
import statistics
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence


try:
    import resource
except ImportError:
    resource = None


# ============================================================
# TYPES
# ============================================================

PerformanceFunction = Callable[
    [Mapping[str, Any]],
    Mapping[str, Any],
]


@dataclass(frozen=True)
class PerformanceSample:
    """
    One measured execution.
    """

    operation: str
    elapsed_seconds: float
    cpu_seconds: float
    memory_delta_bytes: int
    event_count: int

    @property
    def latency_ms(self) -> float:
        return self.elapsed_seconds * 1000.0

    @property
    def throughput_events_per_second(self) -> float:
        if self.elapsed_seconds <= 0:
            return 0.0

        return (
            self.event_count
            / self.elapsed_seconds
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "elapsed_seconds": self.elapsed_seconds,
            "latency_ms": self.latency_ms,
            "cpu_seconds": self.cpu_seconds,
            "memory_delta_bytes": (
                self.memory_delta_bytes
            ),
            "event_count": self.event_count,
            "throughput_events_per_second": (
                self.throughput_events_per_second
            ),
        }


@dataclass(frozen=True)
class PerformanceSummary:
    """
    Aggregated performance measurements.
    """

    operation: str
    runs: int
    event_count: int

    total_seconds: float
    mean_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float

    min_latency_ms: float
    max_latency_ms: float

    mean_cpu_seconds: float
    mean_memory_delta_bytes: float

    throughput_events_per_second: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "runs": self.runs,
            "event_count": self.event_count,
            "total_seconds": self.total_seconds,
            "mean_latency_ms": (
                self.mean_latency_ms
            ),
            "median_latency_ms": (
                self.median_latency_ms
            ),
            "p95_latency_ms": (
                self.p95_latency_ms
            ),
            "p99_latency_ms": (
                self.p99_latency_ms
            ),
            "min_latency_ms": (
                self.min_latency_ms
            ),
            "max_latency_ms": (
                self.max_latency_ms
            ),
            "mean_cpu_seconds": (
                self.mean_cpu_seconds
            ),
            "mean_memory_delta_bytes": (
                self.mean_memory_delta_bytes
            ),
            "throughput_events_per_second": (
                self.throughput_events_per_second
            ),
        }


@dataclass(frozen=True)
class VolumePerformanceResult:
    """
    Performance result for one workload size.
    """

    event_volume: int
    summary: PerformanceSummary

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_volume": self.event_volume,
            "summary": self.summary.to_dict(),
        }


# ============================================================
# RESOURCE MEASUREMENT
# ============================================================


def _process_cpu_seconds() -> float:
    """
    Return process CPU time.

    Uses resource on supported platforms and falls back to
    process_time on Windows.
    """

    return time.process_time()


def _memory_usage_bytes() -> int:
    """
    Return current process memory estimate.

    Uses psutil when available.

    If psutil is unavailable, return zero rather than
    fabricating a measurement.
    """

    try:
        import psutil

        process = psutil.Process(
            os.getpid()
        )

        return int(
            process.memory_info().rss
        )

    except ImportError:
        return 0


# ============================================================
# PERCENTILES
# ============================================================


def _percentile(
    values: Sequence[float],
    percentile: float,
) -> float:
    """
    Calculate a percentile using linear interpolation.

    percentile must be between 0 and 100.
    """

    if not values:
        raise ValueError(
            "Cannot calculate percentile of empty data"
        )

    if not 0.0 <= percentile <= 100.0:
        raise ValueError(
            "Percentile must be between 0 and 100"
        )

    ordered = sorted(
        float(value)
        for value in values
    )

    if len(ordered) == 1:
        return ordered[0]

    position = (
        percentile
        / 100.0
        * (len(ordered) - 1)
    )

    lower = int(position)
    upper = min(
        lower + 1,
        len(ordered) - 1,
    )

    fraction = position - lower

    return (
        ordered[lower]
        + (
            ordered[upper]
            - ordered[lower]
        )
        * fraction
    )


# ============================================================
# SINGLE BENCHMARK
# ============================================================


def benchmark_operation(
    operation: str,
    events: Sequence[Mapping[str, Any]],
    function: PerformanceFunction,
) -> PerformanceSample:
    """
    Measure one complete operation.

    The function receives one event at a time.

    The returned security decisions are intentionally ignored
    here because Day 39 measures operational cost rather than
    detection quality.
    """

    if not operation.strip():
        raise ValueError(
            "Operation name cannot be empty"
        )

    if not events:
        raise ValueError(
            "At least one event is required"
        )

    gc.collect()

    memory_before = (
        _memory_usage_bytes()
    )

    cpu_before = (
        _process_cpu_seconds()
    )

    start = time.perf_counter()

    for event in events:
        function(event)

    elapsed = (
        time.perf_counter()
        - start
    )

    cpu_after = (
        _process_cpu_seconds()
    )

    memory_after = (
        _memory_usage_bytes()
    )

    return PerformanceSample(
        operation=operation,
        elapsed_seconds=elapsed,
        cpu_seconds=max(
            0.0,
            cpu_after - cpu_before,
        ),
        memory_delta_bytes=(
            memory_after
            - memory_before
        ),
        event_count=len(events),
    )


# ============================================================
# REPEATED BENCHMARK
# ============================================================


def run_performance_benchmark(
    operation: str,
    events: Sequence[Mapping[str, Any]],
    function: PerformanceFunction,
    *,
    runs: int = 10,
    warmup_runs: int = 2,
) -> list[PerformanceSample]:
    """
    Execute repeated performance measurements.

    Warm-up runs are excluded from the reported measurements.
    """

    if runs <= 0:
        raise ValueError(
            "runs must be positive"
        )

    if warmup_runs < 0:
        raise ValueError(
            "warmup_runs cannot be negative"
        )

    if not events:
        raise ValueError(
            "At least one event is required"
        )

    for _ in range(warmup_runs):
        benchmark_operation(
            operation,
            events,
            function,
        )

    samples: list[PerformanceSample] = []

    for _ in range(runs):
        samples.append(
            benchmark_operation(
                operation,
                events,
                function,
            )
        )

    return samples


# ============================================================
# AGGREGATION
# ============================================================


def summarize_performance(
    samples: Sequence[PerformanceSample],
) -> PerformanceSummary:
    """
    Aggregate performance samples.
    """

    if not samples:
        raise ValueError(
            "At least one performance sample is required"
        )

    operation_names = {
        sample.operation
        for sample in samples
    }

    if len(operation_names) != 1:
        raise ValueError(
            "All samples must belong to the same operation"
        )

    operation = samples[0].operation

    latencies = [
        sample.latency_ms
        for sample in samples
    ]

    total_seconds = sum(
        sample.elapsed_seconds
        for sample in samples
    )

    total_events = sum(
        sample.event_count
        for sample in samples
    )

    total_cpu = sum(
        sample.cpu_seconds
        for sample in samples
    )

    mean_memory = statistics.mean(
        sample.memory_delta_bytes
        for sample in samples
    )

    average_events = statistics.mean(
        sample.event_count
        for sample in samples
    )

    average_seconds = statistics.mean(
        sample.elapsed_seconds
        for sample in samples
    )

    throughput = (
        average_events
        / average_seconds
        if average_seconds > 0
        else 0.0
    )

    return PerformanceSummary(
        operation=operation,
        runs=len(samples),
        event_count=int(
            average_events
        ),
        total_seconds=total_seconds,
        mean_latency_ms=statistics.mean(
            latencies
        ),
        median_latency_ms=statistics.median(
            latencies
        ),
        p95_latency_ms=_percentile(
            latencies,
            95,
        ),
        p99_latency_ms=_percentile(
            latencies,
            99,
        ),
        min_latency_ms=min(
            latencies
        ),
        max_latency_ms=max(
            latencies
        ),
        mean_cpu_seconds=(
            total_cpu
            / len(samples)
        ),
        mean_memory_delta_bytes=(
            mean_memory
        ),
        throughput_events_per_second=(
            throughput
        ),
    )


# ============================================================
# EVENT-VOLUME BENCHMARK
# ============================================================


def run_volume_benchmark(
    event_volumes: Sequence[int],
    event_factory: Callable[
        [int],
        Sequence[Mapping[str, Any]],
    ],
    function: PerformanceFunction,
    *,
    runs: int = 10,
    warmup_runs: int = 2,
) -> list[VolumePerformanceResult]:
    """
    Measure performance at multiple event volumes.
    """

    if not event_volumes:
        raise ValueError(
            "At least one event volume is required"
        )

    results: list[
        VolumePerformanceResult
    ] = []

    for volume in event_volumes:

        if volume <= 0:
            raise ValueError(
                "Event volume must be positive"
            )

        events = list(
            event_factory(volume)
        )

        if len(events) != volume:
            raise ValueError(
                "event_factory must return exactly "
                f"{volume} events"
            )

        samples = run_performance_benchmark(
            f"volume_{volume}",
            events,
            function,
            runs=runs,
            warmup_runs=warmup_runs,
        )

        summary = summarize_performance(
            samples
        )

        results.append(
            VolumePerformanceResult(
                event_volume=volume,
                summary=summary,
            )
        )

    return results


# ============================================================
# SCALING ANALYSIS
# ============================================================


def calculate_scaling_ratio(
    baseline: VolumePerformanceResult,
    comparison: VolumePerformanceResult,
) -> dict[str, float]:
    """
    Compare a larger workload against a baseline workload.
    """

    baseline_volume = (
        baseline.event_volume
    )

    comparison_volume = (
        comparison.event_volume
    )

    if baseline_volume <= 0:
        raise ValueError(
            "Baseline volume must be positive"
        )

    if comparison_volume <= 0:
        raise ValueError(
            "Comparison volume must be positive"
        )

    baseline_latency = (
        baseline.summary.mean_latency_ms
    )

    comparison_latency = (
        comparison.summary.mean_latency_ms
    )

    baseline_throughput = (
        baseline.summary
        .throughput_events_per_second
    )

    comparison_throughput = (
        comparison.summary
        .throughput_events_per_second
    )

    return {
        "volume_ratio": (
            comparison_volume
            / baseline_volume
        ),
        "latency_ratio": (
            comparison_latency
            / baseline_latency
            if baseline_latency > 0
            else 0.0
        ),
        "throughput_ratio": (
            comparison_throughput
            / baseline_throughput
            if baseline_throughput > 0
            else 0.0
        ),
    }


# ============================================================
# TABLE OUTPUT
# ============================================================


def build_performance_table(
    results: Sequence[
        VolumePerformanceResult
    ],
) -> list[dict[str, Any]]:
    """
    Create flat rows suitable for Streamlit/CSV/reporting.
    """

    table: list[dict[str, Any]] = []

    for result in results:

        summary = result.summary

        table.append(
            {
                "event_volume": (
                    result.event_volume
                ),
                "runs": summary.runs,
                "mean_latency_ms": round(
                    summary.mean_latency_ms,
                    6,
                ),
                "median_latency_ms": round(
                    summary.median_latency_ms,
                    6,
                ),
                "p95_latency_ms": round(
                    summary.p95_latency_ms,
                    6,
                ),
                "p99_latency_ms": round(
                    summary.p99_latency_ms,
                    6,
                ),
                "min_latency_ms": round(
                    summary.min_latency_ms,
                    6,
                ),
                "max_latency_ms": round(
                    summary.max_latency_ms,
                    6,
                ),
                "throughput_events_per_second": round(
                    summary.throughput_events_per_second,
                    6,
                ),
                "mean_cpu_seconds": round(
                    summary.mean_cpu_seconds,
                    6,
                ),
                "mean_memory_delta_bytes": round(
                    summary.mean_memory_delta_bytes,
                    2,
                ),
            }
        )

    return table


# ============================================================
# RESEARCH INTERPRETATION
# ============================================================


def interpret_performance(
    result: VolumePerformanceResult,
) -> str:
    """
    Generate cautious performance interpretation.
    """

    summary = result.summary

    return (
        f"At an event volume of "
        f"{result.event_volume}, the measured mean "
        f"latency was "
        f"{summary.mean_latency_ms:.4f} ms, "
        f"p95 latency was "
        f"{summary.p95_latency_ms:.4f} ms, "
        f"and measured throughput was "
        f"{summary.throughput_events_per_second:.2f} "
        "events/second. These measurements describe "
        "the tested environment and workload only; "
        "they do not establish production-scale performance."
    )


__all__ = [
    "PerformanceSample",
    "PerformanceSummary",
    "VolumePerformanceResult",
    "benchmark_operation",
    "run_performance_benchmark",
    "summarize_performance",
    "run_volume_benchmark",
    "calculate_scaling_ratio",
    "build_performance_table",
    "interpret_performance",
]