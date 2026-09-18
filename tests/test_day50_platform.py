from app.behavioral_intelligence import (
    BehavioralIntelligenceOrchestrator,
)
from app.platform.behavioral import (
    BehavioralPlatformAdapter,
)


def build_snapshot(orchestrator, agent_id="agent-1"):
    return orchestrator.build_snapshot(
        agent_id,
        trust_score=85,
        trust_band="HIGH",
        state_score=82,
        state_level="STABLE",
        deviation_score=10,
        deviation_level="NONE",
        baseline_adapted=True,
        evidence=[
            "Stable action pattern",
            "Resource pattern within baseline",
        ],
    )


def test_platform_accepts_behavioral_intelligence_snapshot():
    orchestrator = BehavioralIntelligenceOrchestrator()
    adapter = BehavioralPlatformAdapter()

    snapshot = build_snapshot(orchestrator)

    result = adapter.record_intelligence(snapshot)

    assert result["status"] == "intelligence_recorded"
    assert result["agent_id"] == "agent-1"


def test_platform_returns_latest_behavioral_intelligence():
    orchestrator = BehavioralIntelligenceOrchestrator()
    adapter = BehavioralPlatformAdapter()

    snapshot = build_snapshot(orchestrator)

    adapter.record_intelligence(snapshot)

    result = adapter.latest_intelligence("agent-1")

    assert result["status"] == "latest_available"
    assert result["agent_id"] == "agent-1"

    intelligence = result["intelligence"]

    assert intelligence["trust_score"] == 85
    assert intelligence["trust_band"] == "HIGH"
    assert intelligence["state_score"] == 82
    assert intelligence["state_level"] == "STABLE"
    assert intelligence["deviation_score"] == 10
    assert intelligence["deviation_level"] == "NONE"
    assert intelligence["baseline_adapted"] is True


def test_platform_preserves_evidence_and_consistency_flags():
    orchestrator = BehavioralIntelligenceOrchestrator()
    adapter = BehavioralPlatformAdapter()

    snapshot = orchestrator.build_snapshot(
        "agent-1",
        trust_score=90,
        trust_band="HIGH",
        state_score=70,
        state_level="MOSTLY_STABLE",
        deviation_score=70,
        deviation_level="HIGH",
        evidence=["Behavior changed"],
    )

    adapter.record_intelligence(snapshot)

    result = adapter.latest_intelligence("agent-1")
    intelligence = result["intelligence"]

    assert intelligence["evidence"] == ["Behavior changed"]
    assert "HIGH_TRUST_WITH_HIGH_DEVIATION" in (
        intelligence["consistency_flags"]
    )


def test_platform_keeps_individual_scores_independent():
    orchestrator = BehavioralIntelligenceOrchestrator()
    adapter = BehavioralPlatformAdapter()

    snapshot = orchestrator.build_snapshot(
        "agent-1",
        trust_score=90,
        trust_band="HIGH",
        state_score=40,
        state_level="VARIABLE",
        deviation_score=70,
        deviation_level="HIGH",
    )

    adapter.record_intelligence(snapshot)

    result = adapter.latest_intelligence("agent-1")
    intelligence = result["intelligence"]

    assert intelligence["trust_score"] == 90
    assert intelligence["state_score"] == 40
    assert intelligence["deviation_score"] == 70

    assert "risk" not in intelligence
    assert "decision" not in intelligence
    assert "response" not in intelligence


def test_platform_history_is_agent_isolated():
    orchestrator = BehavioralIntelligenceOrchestrator()
    adapter = BehavioralPlatformAdapter()

    first = build_snapshot(orchestrator, "agent-a")

    second = orchestrator.build_snapshot(
        "agent-b",
        trust_score=30,
        trust_band="CRITICAL",
        state_score=30,
        state_level="UNSTABLE",
        deviation_score=80,
        deviation_level="CRITICAL",
    )

    adapter.record_intelligence(first)
    adapter.record_intelligence(second)

    agent_a = adapter.intelligence_history("agent-a")
    agent_b = adapter.intelligence_history("agent-b")

    assert agent_a["count"] == 1
    assert agent_b["count"] == 1

    assert agent_a["intelligence"][0]["agent_id"] == "agent-a"
    assert agent_b["intelligence"][0]["agent_id"] == "agent-b"


def test_platform_latest_without_intelligence():
    adapter = BehavioralPlatformAdapter()

    result = adapter.latest_intelligence("unknown-agent")

    assert result["status"] == "latest_not_found"
    assert result["agent_id"] == "unknown-agent"
    assert result["intelligence"] is None


def test_platform_history_without_intelligence():
    adapter = BehavioralPlatformAdapter()

    result = adapter.intelligence_history("unknown-agent")

    assert result["status"] == "history_available"
    assert result["agent_id"] == "unknown-agent"
    assert result["count"] == 0
    assert result["intelligence"] == []


def test_platform_reset_intelligence_for_agent():
    orchestrator = BehavioralIntelligenceOrchestrator()
    adapter = BehavioralPlatformAdapter()

    snapshot = build_snapshot(orchestrator)

    adapter.record_intelligence(snapshot)

    result = adapter.reset_intelligence("agent-1")

    assert result["status"] == "intelligence_reset"
    assert result["agent_id"] == "agent-1"

    latest = adapter.latest_intelligence("agent-1")

    assert latest["status"] == "latest_not_found"


def test_platform_reset_all_intelligence():
    orchestrator = BehavioralIntelligenceOrchestrator()
    adapter = BehavioralPlatformAdapter()

    adapter.record_intelligence(build_snapshot(orchestrator, "agent-a"))

    adapter.record_intelligence(
        build_snapshot(orchestrator, "agent-b")
    )

    result = adapter.reset_intelligence()

    assert result["status"] == "all_intelligence_reset"

    assert (
        adapter.latest_intelligence("agent-a")["intelligence"]
        is None
    )

    assert (
        adapter.latest_intelligence("agent-b")["intelligence"]
        is None
    )