from typing import Any, Dict, List


REQUIRED_FIELDS = {
    "total_runs",
    "scenarios_per_run",
    "stable",
    "average_pass_rate",
    "minimum_pass_rate",
    "maximum_pass_rate",
    "average_allow_count",
    "average_deny_count",
}


def validate_report_structure(report: Dict[str, Any]) -> List[str]:
    """
    Validate that an experiment report contains all required fields.
    """

    missing_fields = [
        field
        for field in REQUIRED_FIELDS
        if field not in report
    ]

    return sorted(missing_fields)


def validate_report_values(report: Dict[str, Any]) -> List[str]:
    """
    Validate basic value constraints for an experiment report.
    """

    errors = []

    total_runs = report.get("total_runs", 0)
    scenarios_per_run = report.get("scenarios_per_run", 0)
    stable = report.get("stable")
    average_pass_rate = report.get("average_pass_rate", 0.0)
    minimum_pass_rate = report.get("minimum_pass_rate", 0.0)
    maximum_pass_rate = report.get("maximum_pass_rate", 0.0)
    average_allow_count = report.get("average_allow_count", 0.0)
    average_deny_count = report.get("average_deny_count", 0.0)

    if not isinstance(total_runs, int) or total_runs < 0:
        errors.append("total_runs must be a non-negative integer")

    if not isinstance(scenarios_per_run, int) or scenarios_per_run < 0:
        errors.append(
            "scenarios_per_run must be a non-negative integer"
        )

    if not isinstance(stable, bool):
        errors.append("stable must be a boolean")

    pass_rates = [
        average_pass_rate,
        minimum_pass_rate,
        maximum_pass_rate,
    ]

    for value in pass_rates:
        if not isinstance(value, (int, float)) or not 0 <= value <= 100:
            errors.append(
                "pass rates must be numeric values between 0 and 100"
            )
            break

    counts = [
        average_allow_count,
        average_deny_count,
    ]

    for value in counts:
        if not isinstance(value, (int, float)) or value < 0:
            errors.append(
                "average decision counts must be non-negative numbers"
            )
            break

    return errors


def validate_report_consistency(report: Dict[str, Any]) -> List[str]:
    """
    Validate relationships between report metrics.
    """

    errors = []

    total_runs = report.get("total_runs", 0)
    scenarios_per_run = report.get("scenarios_per_run", 0)
    minimum_pass_rate = report.get("minimum_pass_rate", 0.0)
    maximum_pass_rate = report.get("maximum_pass_rate", 0.0)
    average_pass_rate = report.get("average_pass_rate", 0.0)
    average_allow_count = report.get("average_allow_count", 0.0)
    average_deny_count = report.get("average_deny_count", 0.0)

    if minimum_pass_rate > maximum_pass_rate:
        errors.append(
            "minimum_pass_rate cannot exceed maximum_pass_rate"
        )

    if not minimum_pass_rate <= average_pass_rate <= maximum_pass_rate:
        errors.append(
            "average_pass_rate must be between minimum and maximum pass rates"
        )

    if scenarios_per_run > 0:
        if average_allow_count + average_deny_count > scenarios_per_run:
            errors.append(
                "average decision counts cannot exceed scenarios per run"
            )

    if total_runs == 0 and scenarios_per_run != 0:
        errors.append(
            "scenarios_per_run must be zero when total_runs is zero"
        )

    return errors


def validate_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform complete experiment report validation.
    """

    structure_errors = validate_report_structure(report)

    if structure_errors:
        return {
            "valid": False,
            "missing_fields": structure_errors,
            "value_errors": [],
            "consistency_errors": [],
        }

    value_errors = validate_report_values(report)
    consistency_errors = validate_report_consistency(report)

    return {
        "valid": not value_errors and not consistency_errors,
        "missing_fields": [],
        "value_errors": value_errors,
        "consistency_errors": consistency_errors,
    }