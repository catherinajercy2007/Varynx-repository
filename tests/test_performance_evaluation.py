import pytest

from app.performance_evaluation import (
    PerformanceSample,
    PerformanceSummary,
    VolumePerformanceResult,
    benchmark_operation,
    build_performance_table,
    calculate_scaling_ratio,
    interpret_performance,
    run_performance_benchmark,
    run_volume_benchmark,
    summarize_performance,
)


def test_performance_sample_latency():
    sample = PerformanceSample(
        operation="test",
        elapsed_seconds=0.5,
        cpu_seconds=0.2,
        memory_delta_bytes=1000,
        event_count=100,
    )

    assert sample.latency_ms == pytest.approx(500.0)


def test_performance_sample_throughput():
    sample = PerformanceSample(
        operation="test",
        elapsed_seconds=2.0,
        cpu_seconds=0.5,
        memory_delta_bytes=1000,
        event_count=100,
    )

    assert (
        sample.throughput_events_per_second
        == pytest.approx(50.0)
    )


def test_benchmark_operation():
    events = [
        {"id": 1},
        {"id": 2},
        {"id": 3},
    ]

    calls = []

    def function(event):
        calls.append(event)
        return {"action": "ALLOW"}

    sample = benchmark_operation(
        "test",
        events,
        function,
    )

    assert sample.operation == "test"
    assert sample.event_count == 3
    assert len(calls) == 3
    assert sample.elapsed_seconds >= 0


def test_empty_events_are_rejected():
    with pytest.raises(ValueError):
        benchmark_operation(
            "test",
            [],
            lambda event: {},
        )


def test_empty_operation_name_is_rejected():
    with pytest.raises(ValueError):
        benchmark_operation(
            "",
            [{"id": 1}],
            lambda event: {},
        )


def test_repeated_benchmark():
    events = [
        {"id": index}
        for index in range(10)
    ]

    samples = run_performance_benchmark(
        "test",
        events,
        lambda event: {"action": "ALLOW"},
        runs=5,
        warmup_runs=1,
    )

    assert len(samples) == 5

    assert all(
        sample.event_count == 10
        for sample in samples
    )


def test_invalid_run_count():
    with pytest.raises(ValueError):
        run_performance_benchmark(
            "test",
            [{"id": 1}],
            lambda event: {},
            runs=0,
        )


def test_negative_warmup_count():
    with pytest.raises(ValueError):
        run_performance_benchmark(
            "test",
            [{"id": 1}],
            lambda event: {},
            warmup_runs=-1,
        )


def test_performance_summary():
    samples = [
        PerformanceSample(
            operation="test",
            elapsed_seconds=0.1,
            cpu_seconds=0.02,
            memory_delta_bytes=100,
            event_count=100,
        ),
        PerformanceSample(
            operation="test",
            elapsed_seconds=0.2,
            cpu_seconds=0.03,
            memory_delta_bytes=200,
            event_count=100,
        ),
        PerformanceSample(
            operation="test",
            elapsed_seconds=0.3,
            cpu_seconds=0.04,
            memory_delta_bytes=300,
            event_count=100,
        ),
    ]

    summary = summarize_performance(
        samples
    )

    assert summary.runs == 3
    assert summary.event_count == 100

    assert summary.mean_latency_ms == pytest.approx(
        200.0
    )

    assert summary.median_latency_ms == pytest.approx(
        200.0
    )

    assert summary.min_latency_ms == pytest.approx(
        100.0
    )

    assert summary.max_latency_ms == pytest.approx(
        300.0
    )


def test_summary_rejects_empty_samples():
    with pytest.raises(ValueError):
        summarize_performance([])


def test_summary_rejects_mixed_operations():
    samples = [
        PerformanceSample(
            operation="a",
            elapsed_seconds=0.1,
            cpu_seconds=0.01,
            memory_delta_bytes=0,
            event_count=10,
        ),
        PerformanceSample(
            operation="b",
            elapsed_seconds=0.1,
            cpu_seconds=0.01,
            memory_delta_bytes=0,
            event_count=10,
        ),
    ]

    with pytest.raises(ValueError):
        summarize_performance(samples)


def test_volume_benchmark():
    def event_factory(volume):
        return [
            {"id": index}
            for index in range(volume)
        ]

    results = run_volume_benchmark(
        [10, 20, 50],
        event_factory,
        lambda event: {"action": "ALLOW"},
        runs=2,
        warmup_runs=0,
    )

    assert len(results) == 3

    assert [
        result.event_volume
        for result in results
    ] == [
        10,
        20,
        50,
    ]


def test_volume_factory_must_return_exact_volume():
    def event_factory(volume):
        return [{"id": 1}]

    with pytest.raises(ValueError):
        run_volume_benchmark(
            [10],
            event_factory,
            lambda event: {},
            runs=1,
            warmup_runs=0,
        )


def test_invalid_volume_is_rejected():
    with pytest.raises(ValueError):
        run_volume_benchmark(
            [0],
            lambda volume: [],
            lambda event: {},
            runs=1,
            warmup_runs=0,
        )


def test_scaling_ratio():
    baseline = VolumePerformanceResult(
        event_volume=100,
        summary=PerformanceSummary(
            operation="volume_100",
            runs=5,
            event_count=100,
            total_seconds=1.0,
            mean_latency_ms=10.0,
            median_latency_ms=10.0,
            p95_latency_ms=12.0,
            p99_latency_ms=13.0,
            min_latency_ms=8.0,
            max_latency_ms=14.0,
            mean_cpu_seconds=0.2,
            mean_memory_delta_bytes=1000,
            throughput_events_per_second=100.0,
        ),
    )

    comparison = VolumePerformanceResult(
        event_volume=200,
        summary=PerformanceSummary(
            operation="volume_200",
            runs=5,
            event_count=200,
            total_seconds=2.5,
            mean_latency_ms=20.0,
            median_latency_ms=19.0,
            p95_latency_ms=24.0,
            p99_latency_ms=26.0,
            min_latency_ms=15.0,
            max_latency_ms=28.0,
            mean_cpu_seconds=0.5,
            mean_memory_delta_bytes=2000,
            throughput_events_per_second=80.0,
        ),
    )

    ratio = calculate_scaling_ratio(
        baseline,
        comparison,
    )

    assert ratio["volume_ratio"] == pytest.approx(
        2.0
    )

    assert ratio["latency_ratio"] == pytest.approx(
        2.0
    )

    assert ratio["throughput_ratio"] == pytest.approx(
        0.8
    )


def test_performance_table():
    summary = PerformanceSummary(
        operation="volume_100",
        runs=5,
        event_count=100,
        total_seconds=1.0,
        mean_latency_ms=10.0,
        median_latency_ms=9.0,
        p95_latency_ms=15.0,
        p99_latency_ms=17.0,
        min_latency_ms=7.0,
        max_latency_ms=20.0,
        mean_cpu_seconds=0.2,
        mean_memory_delta_bytes=1000.0,
        throughput_events_per_second=100.0,
    )

    result = VolumePerformanceResult(
        event_volume=100,
        summary=summary,
    )

    table = build_performance_table(
        [result]
    )

    assert len(table) == 1

    assert table[0]["event_volume"] == 100
    assert table[0]["mean_latency_ms"] == 10.0
    assert table[0]["p95_latency_ms"] == 15.0
    assert (
        table[0][
            "throughput_events_per_second"
        ]
        == 100.0
    )


def test_interpretation_is_cautious():
    summary = PerformanceSummary(
        operation="volume_100",
        runs=5,
        event_count=100,
        total_seconds=1.0,
        mean_latency_ms=10.0,
        median_latency_ms=9.0,
        p95_latency_ms=15.0,
        p99_latency_ms=17.0,
        min_latency_ms=7.0,
        max_latency_ms=20.0,
        mean_cpu_seconds=0.2,
        mean_memory_delta_bytes=1000.0,
        throughput_events_per_second=100.0,
    )

    result = VolumePerformanceResult(
        event_volume=100,
        summary=summary,
    )

    text = interpret_performance(
        result
    )

    assert "100" in text
    assert "production-scale performance" in text


def test_sample_serialization():
    sample = PerformanceSample(
        operation="test",
        elapsed_seconds=0.1,
        cpu_seconds=0.02,
        memory_delta_bytes=500,
        event_count=10,
    )

    data = sample.to_dict()

    assert data["operation"] == "test"
    assert data["event_count"] == 10
    assert "latency_ms" in data
    assert "throughput_events_per_second" in data