"""
Varynx Day 44 - Edge Case and Integration Test Expansion

This test module intentionally builds on the existing public APIs rather
than replacing earlier tests. It targets:
- core module importability
- adaptive-response boundary behavior
- adaptive-response malformed evidence
- investigation validation and filtering
- event-schema validation when the current API exposes a validator
- dashboard source-level integrity without executing Streamlit UI code

These tests do not manufacture research metrics. They validate software
correctness and integration contracts.
"""

from __future__ import annotations

import ast
import importlib
import sqlite3
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


CORE_MODULES = [
    "app.analytics",
    "app.behavior",
    "app.attack_scenarios",
    "app.investigation",
    "app.experimental_dataset",
    "app.evaluation",
    "app.comparison",
    "app.repeated_evaluation",
    "app.statistical_evaluation",
    "app.multiresolution_behavior",
    "app.cross_context_correlation",
    "app.adaptive_response",
    "app.event_schema",
]


def test_core_security_modules_are_importable():
    """All major Day 1-43 modules must remain importable."""
    failures = []

    for module_name in CORE_MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            failures.append(f"{module_name}: {type(exc).__name__}: {exc}")

    assert not failures, "Core module import failures:\n" + "\n".join(failures)


def test_adaptive_response_boundary_values():
    """Boundary inputs must produce a valid graduated response."""
    adaptive = importlib.import_module("app.adaptive_response")

    calculate = getattr(adaptive, "calculate_adaptive_response", None)
    response_action = getattr(adaptive, "ResponseAction", None)

    assert callable(calculate), (
        "calculate_adaptive_response is required by the Day 30 contract"
    )
    assert response_action is not None, "ResponseAction enum is required"

    valid_actions = {member.value for member in response_action}

    for score in (0, 1, 20, 21, 44, 45, 50, 51, 79, 80, 99, 100):
        result = calculate(
            {
                "risk_score": score,
                "anomaly_score": 0,
            }
        )

        assert isinstance(result, dict)
        assert result.get("action") in valid_actions


@pytest.mark.parametrize(
    "evidence",
    [
        {"risk_score": 0, "anomaly_score": 0},
        {"risk_score": 100, "anomaly_score": 100},
        {"risk_score": 45, "anomaly_score": 20},
        {"risk_score": 80, "anomaly_score": 0},
        {"risk_score": 0, "anomaly_score": 100},
    ],
)
def test_adaptive_response_output_is_explainable(evidence):
    """Adaptive responses must expose an action and score-like evidence."""
    adaptive = importlib.import_module("app.adaptive_response")
    calculate = adaptive.calculate_adaptive_response

    result = calculate(evidence)

    assert isinstance(result, dict)
    assert result.get("action")
    assert any(
        key in result
        for key in ("score", "adaptive_score", "risk_score")
    )


@pytest.mark.parametrize(
    "bad_evidence",
    [
        None,
        [],
        "risk_score=80",
        80,
        object(),
    ],
)
def test_adaptive_response_rejects_non_mapping_evidence(bad_evidence):
    """Malformed evidence must not silently become a valid decision."""
    adaptive = importlib.import_module("app.adaptive_response")
    calculate = adaptive.calculate_adaptive_response

    with pytest.raises((TypeError, ValueError)):
        calculate(bad_evidence)


def test_adaptive_response_clamps_or_rejects_extreme_numeric_values():
    """
    Extreme values must never produce an out-of-range adaptive score.

    If the implementation rejects the values, that is acceptable and is
    explicitly treated as safe behavior.
    """
    adaptive = importlib.import_module("app.adaptive_response")
    calculate = adaptive.calculate_adaptive_response

    try:
        result = calculate(
            {
                "risk_score": 10_000,
                "anomaly_score": -10_000,
            }
        )
    except (TypeError, ValueError, OverflowError):
        return

    assert isinstance(result, dict)

    score = result.get(
        "score",
        result.get(
            "adaptive_score",
            result.get("risk_score"),
        ),
    )

    if isinstance(score, (int, float)):
        assert 0 <= float(score) <= 100


@pytest.fixture()
def investigation_database(tmp_path, monkeypatch):
    """Create an isolated SQLite audit database for investigation tests."""
    database_path = tmp_path / "day44_investigation.db"

    connection = sqlite3.connect(database_path)
    connection.execute(
        """
        CREATE TABLE audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            action TEXT NOT NULL,
            resource TEXT NOT NULL,
            decision TEXT NOT NULL,
            risk INTEGER NOT NULL,
            reason TEXT NOT NULL
        )
        """
    )

    events = [
        (
            "2026-08-31T10:00:00+00:00",
            "agent-alpha",
            "task-analysis",
            "s3:GetObject",
            "public/data.csv",
            "ALLOW",
            20,
            "Authorized request",
        ),
        (
            "2026-08-31T10:01:00+00:00",
            "agent-alpha",
            "task-analysis",
            "s3:DeleteObject",
            "private/data.csv",
            "DENY",
            85,
            "High-risk destructive action",
        ),
        (
            "2026-08-31T10:02:00+00:00",
            "agent-beta",
            "task-report",
            "s3:GetObject",
            "public/report.csv",
            "ALLOW",
            35,
            "Authorized request",
        ),
        (
            "2026-08-31T10:03:00+00:00",
            "agent-beta",
            "task-report",
            "iam:CreateUser",
            "admin/users",
            "DENY",
            95,
            "Unauthorized administrative action",
        ),
    ]

    connection.executemany(
        """
        INSERT INTO audit_events (
            timestamp,
            agent_id,
            task_id,
            action,
            resource,
            decision,
            risk,
            reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        events,
    )
    connection.commit()
    connection.close()

    investigation = importlib.import_module("app.investigation")

    if not hasattr(investigation, "DATABASE_PATH"):
        pytest.fail(
            "app.investigation must expose DATABASE_PATH so tests can "
            "isolate database access"
        )

    monkeypatch.setattr(
        investigation,
        "DATABASE_PATH",
        str(database_path),
    )

    return investigation


def test_investigation_empty_filter_returns_events(investigation_database):
    """An unfiltered investigation query should return available events."""
    rows = investigation_database.get_investigation_events()

    assert isinstance(rows, list)
    assert len(rows) == 4


def test_investigation_filters_by_agent(investigation_database):
    rows = investigation_database.get_investigation_events(
        agent_id="agent-alpha"
    )

    assert len(rows) == 2
    assert {row["agent_id"] for row in rows} == {"agent-alpha"}


def test_investigation_filters_by_decision(investigation_database):
    rows = investigation_database.get_investigation_events(
        decision="deny"
    )

    assert len(rows) == 2
    assert {row["decision"] for row in rows} == {"DENY"}


def test_investigation_filters_by_risk_level(investigation_database):
    rows = investigation_database.get_investigation_events(
        risk_level="critical"
    )

    assert len(rows) == 2
    assert rows[0]["risk"] == 95


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": 0},
        {"limit": -1},
        {"limit": 5001},
        {"minimum_risk": -1},
        {"minimum_risk": 101},
        {"maximum_risk": -1},
        {"maximum_risk": 101},
        {"minimum_risk": 90, "maximum_risk": 10},
        {"decision": "UNKNOWN"},
        {"risk_level": "UNKNOWN"},
    ],
)
def test_investigation_rejects_invalid_filters(
    investigation_database,
    kwargs,
):
    with pytest.raises(ValueError):
        investigation_database.get_investigation_events(**kwargs)


def test_investigation_event_lookup_handles_missing_id(investigation_database):
    result = investigation_database.get_investigation_event(999999)

    assert result is None


def test_investigation_event_lookup_rejects_invalid_id(investigation_database):
    with pytest.raises(ValueError):
        investigation_database.get_investigation_event(0)


def test_investigation_filter_options_are_structured(investigation_database):
    options = investigation_database.get_investigation_filter_options()

    assert isinstance(options, dict)

    for key in ("agents", "tasks", "actions", "resources"):
        assert key in options
        assert isinstance(options[key], list)


def test_dashboard_source_is_valid_python():
    """
    Parse dashboard.py without importing Streamlit.

    This catches accidental pasted text, misplaced future imports and
    other syntax corruption without triggering UI execution.
    """
    dashboard = PROJECT_ROOT / "dashboard.py"

    if not dashboard.exists():
        pytest.skip("dashboard.py is not present in the checked-out workspace")

    source = dashboard.read_text(encoding="utf-8")
    ast.parse(source, filename=str(dashboard))


def test_dashboard_contains_day43_hardening_contract():
    """Day 43 dashboard hardening helpers should remain present."""
    dashboard = PROJECT_ROOT / "dashboard.py"

    if not dashboard.exists():
        pytest.skip("dashboard.py is not present in the checked-out workspace")

    source = dashboard.read_text(encoding="utf-8")

    required_markers = [
        "record_dashboard_error",
        "safe_import",
        "render_dashboard_health",
        "dashboard_errors",
        "Reload Modules",
        "Clear Diagnostics",
    ]

    missing = [marker for marker in required_markers if marker not in source]

    assert not missing, (
        "Day 43 dashboard hardening contract is incomplete. "
        f"Missing markers: {missing}"
    )


def test_event_schema_module_imports_without_circular_dependency():
    """Day 40 event schema must remain independently importable."""
    module = importlib.import_module("app.event_schema")
    assert module is not None


def test_event_schema_has_public_validation_surface():
    """
    Verify that the event schema module exposes at least one public
    callable related to validation/schema handling.

    This deliberately avoids inventing a function name because the
    project's actual event-schema API may evolve.
    """
    module = importlib.import_module("app.event_schema")

    public_callables = [
        name
        for name in dir(module)
        if not name.startswith("_")
        and callable(getattr(module, name))
        and any(
            token in name.lower()
            for token in ("valid", "schema", "event", "normal")
        )
    ]

    assert public_callables, (
        "event_schema.py does not expose a recognizable public "
        "validation/schema callable"
    )
