from datetime import datetime, timedelta, timezone

import pytest

from app.platform import CapabilityLease, CapabilityLeasePlatformAdapter


def make_clock():
    state = {"now": datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)}
    return state, lambda: state["now"]


def make_lease(adapter, **overrides):
    values = {
        "agent_id": "agent-1",
        "capability": "read_report",
        "scope": ["reports/weekly.csv", "reports/monthly.csv"],
        "ttl_seconds": 60,
        "lease_id": "lease-1",
    }
    values.update(overrides)
    return adapter.issue_lease(**values)


def test_day80_issues_scoped_time_bounded_lease():
    state, clock = make_clock()
    adapter = CapabilityLeasePlatformAdapter(clock=clock)

    lease = make_lease(adapter)

    assert isinstance(lease, CapabilityLease)
    assert lease.lease_id == "lease-1"
    assert lease.agent_id == "agent-1"
    assert lease.capability == "read_report"
    assert lease.scope == ("reports/weekly.csv", "reports/monthly.csv")
    assert lease.expires_at == state["now"] + timedelta(seconds=60)
    assert lease.status_at(state["now"]) == "active"


def test_day80_valid_lease_allows_matching_agent_capability_and_resource():
    _, clock = make_clock()
    adapter = CapabilityLeasePlatformAdapter(clock=clock)
    make_lease(adapter)

    result = adapter.validate_lease(
        "lease-1", "agent-1", "read_report", "reports/weekly.csv"
    )

    assert result["allowed"] is True
    assert result["decision"] == "ALLOW"
    assert result["reason_code"] == "LEASE_VALID"


def test_day80_expired_lease_is_denied():
    state, clock = make_clock()
    adapter = CapabilityLeasePlatformAdapter(clock=clock)
    make_lease(adapter, ttl_seconds=10)
    state["now"] += timedelta(seconds=10)

    result = adapter.validate_lease(
        "lease-1", "agent-1", "read_report", "reports/weekly.csv"
    )

    assert result["allowed"] is False
    assert result["reason_code"] == "LEASE_EXPIRED"
    assert adapter.get_lease("lease-1").status_at(state["now"]) == "expired"


def test_day80_revoked_lease_is_denied():
    _, clock = make_clock()
    adapter = CapabilityLeasePlatformAdapter(clock=clock)
    make_lease(adapter)

    adapter.revoke_lease("lease-1", "operator request")
    result = adapter.validate_lease(
        "lease-1", "agent-1", "read_report", "reports/weekly.csv"
    )

    assert result["allowed"] is False
    assert result["reason_code"] == "LEASE_REVOKED"
    assert adapter.get_lease("lease-1").revocation_reason == "operator request"


def test_day80_scope_mismatch_is_denied():
    _, clock = make_clock()
    adapter = CapabilityLeasePlatformAdapter(clock=clock)
    make_lease(adapter)

    result = adapter.validate_lease(
        "lease-1", "agent-1", "read_report", "reports/private.csv"
    )

    assert result["allowed"] is False
    assert result["reason_code"] == "SCOPE_MISMATCH"


def test_day80_agent_mismatch_is_denied():
    _, clock = make_clock()
    adapter = CapabilityLeasePlatformAdapter(clock=clock)
    make_lease(adapter)

    result = adapter.validate_lease(
        "lease-1", "agent-2", "read_report", "reports/weekly.csv"
    )

    assert result["reason_code"] == "AGENT_MISMATCH"


def test_day80_capability_mismatch_is_denied():
    _, clock = make_clock()
    adapter = CapabilityLeasePlatformAdapter(clock=clock)
    make_lease(adapter)

    result = adapter.validate_lease(
        "lease-1", "agent-1", "delete_report", "reports/weekly.csv"
    )

    assert result["reason_code"] == "CAPABILITY_MISMATCH"


def test_day80_unknown_lease_is_denied():
    _, clock = make_clock()
    adapter = CapabilityLeasePlatformAdapter(clock=clock)

    result = adapter.validate_lease(
        "missing", "agent-1", "read_report", "reports/weekly.csv"
    )

    assert result["reason_code"] == "LEASE_NOT_FOUND"


@pytest.mark.parametrize("ttl", [0, -1, True, 1.5])
def test_day80_rejects_invalid_ttl(ttl):
    _, clock = make_clock()
    adapter = CapabilityLeasePlatformAdapter(clock=clock)

    with pytest.raises(ValueError):
        make_lease(adapter, ttl_seconds=ttl)


@pytest.mark.parametrize(
    "overrides",
    [
        {"agent_id": ""},
        {"capability": " "},
        {"scope": []},
        {"scope": ["reports/a.csv", " "]},
        {"scope": "reports/a.csv"},
        {"lease_id": ""},
    ],
)
def test_day80_rejects_invalid_lease_fields(overrides):
    _, clock = make_clock()
    adapter = CapabilityLeasePlatformAdapter(clock=clock)

    with pytest.raises(ValueError):
        make_lease(adapter, **overrides)


def test_day80_duplicate_lease_id_is_rejected():
    _, clock = make_clock()
    adapter = CapabilityLeasePlatformAdapter(clock=clock)
    make_lease(adapter)

    with pytest.raises(ValueError, match="already exists"):
        make_lease(adapter)


def test_day80_revocation_is_idempotent():
    _, clock = make_clock()
    adapter = CapabilityLeasePlatformAdapter(clock=clock)
    make_lease(adapter)

    first = adapter.revoke_lease("lease-1", "operator request")
    second = adapter.revoke_lease("lease-1", "different reason")

    assert first is second
    assert second.status == "revoked"
    assert second.revocation_reason == "operator request"


def test_day80_missing_lease_cannot_be_revoked():
    _, clock = make_clock()
    adapter = CapabilityLeasePlatformAdapter(clock=clock)

    with pytest.raises(KeyError):
        adapter.revoke_lease("missing")


def test_day80_serialization_reports_expired_status():
    state, clock = make_clock()
    adapter = CapabilityLeasePlatformAdapter(clock=clock)
    make_lease(adapter, ttl_seconds=5)
    state["now"] += timedelta(seconds=5)

    record = adapter.list_leases()[0]

    assert record["lease_id"] == "lease-1"
    assert record["scope"] == ["reports/weekly.csv", "reports/monthly.csv"]
    assert record["status"] == "expired"
