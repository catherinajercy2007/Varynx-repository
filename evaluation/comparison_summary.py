from dataclasses import dataclass
from typing import Any, Dict

from evaluation.baseline_comparison import (
    BaselineComparison,
    baseline_comparison_to_dict,
    generate_default_baseline_comparison,
)


@dataclass
class ComparisonSummary:
    valid: bool
    pass_rate_difference: float
    allow_count_difference: float
    deny_count_difference: float
    pass_rate_meets_baseline: bool
    allow_count_matches_baseline: bool
    deny_count_matches_baseline: bool
    baseline_aligned: bool


def create_comparison_summary(
    comparison: BaselineComparison,
) -> ComparisonSummary:
    """
    Convert baseline comparison results into an experiment summary.
    """

    baseline_aligned = (
        comparison.pass_rate_meets_baseline
        and comparison.allow_count_matches_baseline
        and comparison.deny_count_matches_baseline
    )

    return ComparisonSummary(
        valid=comparison.valid,
        pass_rate_difference=comparison.pass_rate_difference,
        allow_count_difference=comparison.allow_count_difference,
        deny_count_difference=comparison.deny_count_difference,
        pass_rate_meets_baseline=comparison.pass_rate_meets_baseline,
        allow_count_matches_baseline=comparison.allow_count_matches_baseline,
        deny_count_matches_baseline=comparison.deny_count_matches_baseline,
        baseline_aligned=baseline_aligned,
    )


def generate_default_comparison_summary(
    repetitions: int = 5,
) -> ComparisonSummary:
    """
    Generate the default experiment comparison summary.
    """

    comparison = generate_default_baseline_comparison(
        repetitions
    )

    return create_comparison_summary(comparison)


def comparison_summary_to_dict(
    summary: ComparisonSummary,
) -> Dict[str, Any]:
    """
    Convert a comparison summary into a serializable dictionary.
    """

    return {
        "valid": summary.valid,
        "pass_rate_difference": summary.pass_rate_difference,
        "allow_count_difference": summary.allow_count_difference,
        "deny_count_difference": summary.deny_count_difference,
        "pass_rate_meets_baseline": (
            summary.pass_rate_meets_baseline
        ),
        "allow_count_matches_baseline": (
            summary.allow_count_matches_baseline
        ),
        "deny_count_matches_baseline": (
            summary.deny_count_matches_baseline
        ),
        "baseline_aligned": summary.baseline_aligned,
    }


def comparison_summary_status(
    summary: ComparisonSummary,
) -> str:
    """
    Return a simple status for the comparison summary.
    """

    if not summary.valid:
        return "INVALID"

    if summary.baseline_aligned:
        return "ALIGNED"

    return "DIFFERS"


def comparison_summary_details(
    summary: ComparisonSummary,
) -> Dict[str, Any]:
    """
    Return the summary together with its high-level status.
    """

    data = comparison_summary_to_dict(summary)
    data["status"] = comparison_summary_status(summary)

    return data