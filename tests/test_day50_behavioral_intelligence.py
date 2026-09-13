from app.behavioral_intelligence import (
    BehavioralIntelligenceOrchestrator,
)


def build_default_snapshot(orchestrator):
    return orchestrator.build_snapshot(
        "agent-1",
        trust_score=85,
        trust_band="HIGH",
        state_score=82,
        state_level="STABLE",
        deviation_score=10,
        deviation_level="NONE",
        baseline_adapted=True,
        evidence=[
            "Stable action pattern",
        ],
    )


def test_build_snapshot():
    orchestrator = BehavioralIntelligenceOrchestrator()

    snapshot = build_default_snapshot(
        orchestrator
    )

    assert snapshot.agent_id == "agent-1"
    assert snapshot.trust_score == 85
    assert snapshot.trust_band == "HIGH"
    assert snapshot.state_score == 82
    assert snapshot.state_level == "STABLE"
    assert snapshot.deviation_score == 10
    assert snapshot.deviation_level == "NONE"
    assert snapshot.baseline_adapted is True


def test_snapshot_preserves_evidence():
    orchestrator = BehavioralIntelligenceOrchestrator()

    snapshot = orchestrator.build_snapshot(
        "agent-1",
        trust_score=70,
        trust_band="MODERATE",
        state_score=65,
        state_level="MOSTLY_STABLE",
        deviation_score=20,
        deviation_level="LOW",
        evidence=[
            "Action pattern changed",
            "Resource pattern stable",
        ],
    )

    assert snapshot.evidence == [
        "Action pattern changed",
        "Resource pattern stable",
    ]


def test_evidence_is_copied():
    orchestrator = BehavioralIntelligenceOrchestrator()

    evidence = ["Evidence A"]

    snapshot = orchestrator.build_snapshot(
        "agent-1",
        trust_score=70,
        trust_band="MODERATE",
        state_score=65,
        state_level="MOSTLY_STABLE",
        deviation_score=20,
        deviation_level="LOW",
        evidence=evidence,
    )

    evidence.append("Evidence B")

    assert snapshot.evidence == ["Evidence A"]


def test_high_trust_high_deviation_flag():
    orchestrator = BehavioralIntelligenceOrchestrator()

    snapshot = orchestrator.build_snapshot(
        "agent-1",
        trust_score=90,
        trust_band="HIGH",
        state_score=70,
        state_level="MOSTLY_STABLE",
        deviation_score=70,
        deviation_level="HIGH",
    )

    assert "HIGH_TRUST_WITH_HIGH_DEVIATION" in (
        snapshot.consistency_flags
    )


def test_low_trust_low_deviation_flag():
    orchestrator = BehavioralIntelligenceOrchestrator()

    snapshot = orchestrator.build_snapshot(
        "agent-1",
        trust_score=30,
        trust_band="CRITICAL",
        state_score=50,
        state_level="VARIABLE",
        deviation_score=10,
        deviation_level="NONE",
    )

    assert "LOW_TRUST_WITH_LOW_DEVIATION" in (
        snapshot.consistency_flags
    )


def test_stable_state_high_deviation_flag():
    orchestrator = BehavioralIntelligenceOrchestrator()

    snapshot = orchestrator.build_snapshot(
        "agent-1",
        trust_score=70,
        trust_band="MODERATE",
        state_score=90,
        state_level="STABLE",
        deviation_score=70,
        deviation_level="HIGH",
    )

    assert "STABLE_STATE_WITH_HIGH_DEVIATION" in (
        snapshot.consistency_flags
    )


def test_unstable_state_low_deviation_flag():
    orchestrator = BehavioralIntelligenceOrchestrator()

    snapshot = orchestrator.build_snapshot(
        "agent-1",
        trust_score=50,
        trust_band="MODERATE",
        state_score=30,
        state_level="UNSTABLE",
        deviation_score=10,
        deviation_level="NONE",
    )

    assert "UNSTABLE_STATE_WITH_LOW_DEVIATION" in (
        snapshot.consistency_flags
    )


def test_high_trust_unstable_state_flag():
    orchestrator = BehavioralIntelligenceOrchestrator()

    snapshot = orchestrator.build_snapshot(
        "agent-1",
        trust_score=90,
        trust_band="HIGH",
        state_score=30,
        state_level="UNSTABLE",
        deviation_score=30,
        deviation_level="LOW",
    )

    assert "HIGH_TRUST_WITH_UNSTABLE_STATE" in (
        snapshot.consistency_flags
    )


def test_critical_deviation_and_trust_flag():
    orchestrator = BehavioralIntelligenceOrchestrator()

    snapshot = orchestrator.build_snapshot(
        "agent-1",
        trust_score=20,
        trust_band="CRITICAL",
        state_score=30,
        state_level="UNSTABLE",
        deviation_score=95,
        deviation_level="CRITICAL",
    )

    assert "CRITICAL_DEVIATION_AND_TRUST" in (
        snapshot.consistency_flags
    )


def test_no_consistency_flags_for_normal_profile():
    orchestrator = BehavioralIntelligenceOrchestrator()

    snapshot = orchestrator.build_snapshot(
        "agent-1",
        trust_score=75,
        trust_band="MODERATE",
        state_score=75,
        state_level="MOSTLY_STABLE",
        deviation_score=15,
        deviation_level="NONE",
    )

    assert snapshot.consistency_flags == []


def test_history_is_recorded():
    orchestrator = BehavioralIntelligenceOrchestrator()

    build_default_snapshot(orchestrator)

    orchestrator.build_snapshot(
        "agent-1",
        trust_score=70,
        trust_band="MODERATE",
        state_score=70,
        state_level="MOSTLY_STABLE",
        deviation_score=20,
        deviation_level="LOW",
    )

    assert len(
        orchestrator.history("agent-1")
    ) == 2


def test_latest_returns_latest_snapshot():
    orchestrator = BehavioralIntelligenceOrchestrator()

    build_default_snapshot(orchestrator)

    second = orchestrator.build_snapshot(
        "agent-1",
        trust_score=60,
        trust_band="MODERATE",
        state_score=55,
        state_level="VARIABLE",
        deviation_score=35,
        deviation_level="LOW",
    )

    assert (
        orchestrator.latest("agent-1")
        == second
    )


def test_latest_without_history():
    orchestrator = BehavioralIntelligenceOrchestrator()

    assert orchestrator.latest("agent-1") is None


def test_multiple_agents_are_isolated():
    orchestrator = BehavioralIntelligenceOrchestrator()

    orchestrator.build_snapshot(
        "agent-a",
        trust_score=90,
        trust_band="HIGH",
        state_score=90,
        state_level="STABLE",
        deviation_score=5,
        deviation_level="NONE",
    )

    orchestrator.build_snapshot(
        "agent-b",
        trust_score=30,
        trust_band="CRITICAL",
        state_score=30,
        state_level="UNSTABLE",
        deviation_score=80,
        deviation_level="CRITICAL",
    )

    assert len(
        orchestrator.history("agent-a")
    ) == 1

    assert len(
        orchestrator.history("agent-b")
    ) == 1


def test_invalid_agent_id():
    orchestrator = BehavioralIntelligenceOrchestrator()

    try:
        orchestrator.build_snapshot(
            "",
            trust_score=50,
            trust_band="MODERATE",
            state_score=50,
            state_level="VARIABLE",
            deviation_score=50,
            deviation_level="MODERATE",
        )
        assert False
    except ValueError:
        pass


def test_invalid_trust_score():
    orchestrator = BehavioralIntelligenceOrchestrator()

    try:
        orchestrator.build_snapshot(
            "agent-1",
            trust_score=101,
            trust_band="HIGH",
            state_score=50,
            state_level="VARIABLE",
            deviation_score=50,
            deviation_level="MODERATE",
        )
        assert False
    except ValueError:
        pass


def test_invalid_state_score():
    orchestrator = BehavioralIntelligenceOrchestrator()

    try:
        orchestrator.build_snapshot(
            "agent-1",
            trust_score=50,
            trust_band="MODERATE",
            state_score=-1,
            state_level="VARIABLE",
            deviation_score=50,
            deviation_level="MODERATE",
        )
        assert False
    except ValueError:
        pass


def test_invalid_deviation_score():
    orchestrator = BehavioralIntelligenceOrchestrator()

    try:
        orchestrator.build_snapshot(
            "agent-1",
            trust_score=50,
            trust_band="MODERATE",
            state_score=50,
            state_level="VARIABLE",
            deviation_score=101,
            deviation_level="CRITICAL",
        )
        assert False
    except ValueError:
        pass


def test_invalid_trust_band():
    orchestrator = BehavioralIntelligenceOrchestrator()

    try:
        orchestrator.build_snapshot(
            "agent-1",
            trust_score=50,
            trust_band="INVALID",
            state_score=50,
            state_level="VARIABLE",
            deviation_score=50,
            deviation_level="MODERATE",
        )
        assert False
    except ValueError:
        pass


def test_invalid_state_level():
    orchestrator = BehavioralIntelligenceOrchestrator()

    try:
        orchestrator.build_snapshot(
            "agent-1",
            trust_score=50,
            trust_band="MODERATE",
            state_score=50,
            state_level="INVALID",
            deviation_score=50,
            deviation_level="MODERATE",
        )
        assert False
    except ValueError:
        pass


def test_invalid_deviation_level():
    orchestrator = BehavioralIntelligenceOrchestrator()

    try:
        orchestrator.build_snapshot(
            "agent-1",
            trust_score=50,
            trust_band="MODERATE",
            state_score=50,
            state_level="VARIABLE",
            deviation_score=50,
            deviation_level="INVALID",
        )
        assert False
    except ValueError:
        pass


def test_baseline_adapted_must_be_boolean():
    orchestrator = BehavioralIntelligenceOrchestrator()

    try:
        orchestrator.build_snapshot(
            "agent-1",
            trust_score=50,
            trust_band="MODERATE",
            state_score=50,
            state_level="VARIABLE",
            deviation_score=50,
            deviation_level="MODERATE",
            baseline_adapted=1,
        )
        assert False
    except TypeError:
        pass


def test_reset_single_agent():
    orchestrator = BehavioralIntelligenceOrchestrator()

    build_default_snapshot(orchestrator)

    orchestrator.reset("agent-1")

    assert orchestrator.history("agent-1") == []


def test_reset_all_agents():
    orchestrator = BehavioralIntelligenceOrchestrator()

    build_default_snapshot(orchestrator)

    orchestrator.build_snapshot(
        "agent-2",
        trust_score=70,
        trust_band="MODERATE",
        state_score=70,
        state_level="MOSTLY_STABLE",
        deviation_score=20,
        deviation_level="LOW",
    )

    orchestrator.reset()

    assert orchestrator.history("agent-1") == []
    assert orchestrator.history("agent-2") == []


def test_history_returns_copy():
    orchestrator = BehavioralIntelligenceOrchestrator()

    build_default_snapshot(orchestrator)

    history = orchestrator.history("agent-1")
    history.clear()

    assert len(
        orchestrator.history("agent-1")
    ) == 1


def test_snapshot_has_no_security_decision():
    orchestrator = BehavioralIntelligenceOrchestrator()

    snapshot = build_default_snapshot(
        orchestrator
    )

    assert not hasattr(snapshot, "decision")
    assert not hasattr(snapshot, "response")
    assert not hasattr(snapshot, "authorization")


def test_snapshot_preserves_independent_scores():
    orchestrator = BehavioralIntelligenceOrchestrator()

    snapshot = orchestrator.build_snapshot(
        "agent-1",
        trust_score=90,
        trust_band="HIGH",
        state_score=40,
        state_level="VARIABLE",
        deviation_score=70,
        deviation_level="HIGH",
    )

    assert snapshot.trust_score == 90
    assert snapshot.state_score == 40
    assert snapshot.deviation_score == 70


def test_baseline_adaptation_is_explicit():
    orchestrator = BehavioralIntelligenceOrchestrator()

    snapshot = orchestrator.build_snapshot(
        "agent-1",
        trust_score=70,
        trust_band="MODERATE",
        state_score=70,
        state_level="MOSTLY_STABLE",
        deviation_score=20,
        deviation_level="LOW",
        baseline_adapted=False,
    )

    assert snapshot.baseline_adapted is False


def test_empty_evidence_is_supported():
    orchestrator = BehavioralIntelligenceOrchestrator()

    snapshot = orchestrator.build_snapshot(
        "agent-1",
        trust_score=70,
        trust_band="MODERATE",
        state_score=70,
        state_level="MOSTLY_STABLE",
        deviation_score=20,
        deviation_level="LOW",
    )

    assert snapshot.evidence == []