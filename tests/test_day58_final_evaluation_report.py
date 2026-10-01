from evaluation.comparison_summary import (
    ComparisonSummary,
)
from evaluation.experiment_quality_gate import (
    QualityGateResult,
)
from evaluation.experiment_report import (
    generate_default_report,
)
from evaluation.final_evaluation_report import (
    determine_overall_status,
    final_report_to_dict,
    generate_default_final_report,
    generate_final_report,
)


def test_default_final_report():
    report = generate_default_final_report(5)

    assert report.overall_status == "PASS"
    assert report.experiment["total_runs"] == 5
    assert report.experiment["scenarios_per_run"] == 8


def test_default_quality_gate():
    report = generate_default_final_report(5)

    assert report.quality_gate["valid"] is True
    assert report.quality_gate["status"] == "PASS"


def test_default_comparison():
    report = generate_default_final_report(5)

    assert report.comparison["valid"] is True
    assert report.comparison["baseline_aligned"] is True


def test_final_report_dictionary():
    report = generate_default_final_report(5)

    data = final_report_to_dict(report)

    assert data["overall_status"] == "PASS"
    assert data["experiment"]["total_runs"] == 5
    assert data["quality_gate"]["valid"] is True
    assert data["comparison"]["baseline_aligned"] is True


def test_valid_overall_status():
    quality_gate = QualityGateResult(
        valid=True,
        status="PASS",
        missing_fields=[],
        value_errors=[],
        consistency_errors=[],
    )

    comparison = ComparisonSummary(
        valid=True,
        pass_rate_difference=0.0,
        allow_count_difference=0.0,
        deny_count_difference=0.0,
        pass_rate_meets_baseline=True,
        allow_count_matches_baseline=True,
        deny_count_matches_baseline=True,
        baseline_aligned=True,
    )

    assert determine_overall_status(
        quality_gate,
        comparison,
    ) == "PASS"


def test_invalid_quality_gate_status():
    quality_gate = QualityGateResult(
        valid=False,
        status="FAIL",
        missing_fields=["average_pass_rate"],
        value_errors=[],
        consistency_errors=[],
    )

    comparison = ComparisonSummary(
        valid=True,
        pass_rate_difference=0.0,
        allow_count_difference=0.0,
        deny_count_difference=0.0,
        pass_rate_meets_baseline=True,
        allow_count_matches_baseline=True,
        deny_count_matches_baseline=True,
        baseline_aligned=True,
    )

    assert determine_overall_status(
        quality_gate,
        comparison,
    ) == "INVALID"


def test_invalid_comparison_status():
    quality_gate = QualityGateResult(
        valid=True,
        status="PASS",
        missing_fields=[],
        value_errors=[],
        consistency_errors=[],
    )

    comparison = ComparisonSummary(
        valid=False,
        pass_rate_difference=0.0,
        allow_count_difference=0.0,
        deny_count_difference=0.0,
        pass_rate_meets_baseline=False,
        allow_count_matches_baseline=False,
        deny_count_matches_baseline=False,
        baseline_aligned=False,
    )

    assert determine_overall_status(
        quality_gate,
        comparison,
    ) == "INVALID"


def test_different_baseline_status():
    quality_gate = QualityGateResult(
        valid=True,
        status="PASS",
        missing_fields=[],
        value_errors=[],
        consistency_errors=[],
    )

    comparison = ComparisonSummary(
        valid=True,
        pass_rate_difference=5.0,
        allow_count_difference=1.0,
        deny_count_difference=-1.0,
        pass_rate_meets_baseline=True,
        allow_count_matches_baseline=False,
        deny_count_matches_baseline=False,
        baseline_aligned=False,
    )

    assert determine_overall_status(
        quality_gate,
        comparison,
    ) == "DIFFERS"


def test_report_contains_all_sections():
    report = generate_default_final_report(5)

    data = final_report_to_dict(report)

    assert "experiment" in data
    assert "quality_gate" in data
    assert "comparison" in data
    assert "overall_status" in data