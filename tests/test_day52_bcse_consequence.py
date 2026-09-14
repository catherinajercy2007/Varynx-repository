from app.bcse_consequence import (
    SecurityConsequenceEstimator,
    aggregate_consequence,
    classify_consequence,
    classify_confidence,
    identify_consequence_evidence,
)


def test_empty_dimensions_return_zero():
    assert aggregate_consequence({}) == 0


def test_single_dimension():
    score = aggregate_consequence(
        {"confidentiality": 100},
        {"confidentiality": 1.0},
    )

    assert score == 100


def test_equal_weighted_dimensions():
    score = aggregate_consequence(
        {
            "confidentiality": 100,
            "integrity": 0,
        },
        {
            "confidentiality": 0.5,
            "integrity": 0.5,
        },
    )

    assert score == 50


def test_missing_dimensions_are_renormalized():
    score = aggregate_consequence(
        {
            "confidentiality": 100,
        },
        {
            "confidentiality": 0.25,
            "integrity": 0.75,
        },
    )

    assert score == 100


def test_consequence_is_bounded():
    score = aggregate_consequence(
        {
            "confidentiality": 100,
            "integrity": 100,
            "availability": 100,
        }
    )

    assert 0 <= score <= 100


def test_none_classification():
    assert classify_consequence(0) == "NONE"


def test_low_classification():
    assert classify_consequence(20) == "LOW"


def test_moderate_classification():
    assert classify_consequence(40) == "MODERATE"


def test_high_classification():
    assert classify_consequence(60) == "HIGH"


def test_critical_classification():
    assert classify_consequence(80) == "CRITICAL"


def test_upper_bound_classification():
    assert classify_consequence(100) == "CRITICAL"


def test_high_confidence():
    assert (
        classify_confidence(
            evidence_count=3,
            assumption_count=1,
        )
        == "HIGH"
    )


def test_moderate_confidence():
    assert (
        classify_confidence(
            evidence_count=1,
            assumption_count=2,
        )
        == "MODERATE"
    )


def test_low_confidence():
    assert (
        classify_confidence(
            evidence_count=0,
            assumption_count=5,
        )
        == "LOW"
    )


def test_evidence_generation():
    evidence = identify_consequence_evidence(
        {
            "confidentiality": 80,
            "integrity": 20,
            "scope": 60,
        }
    )

    assert len(evidence) == 2

    assert any(
        "confidentiality" in item.lower()
        for item in evidence
    )

    assert any(
        "scope" in item.lower()
        for item in evidence
    )


def test_evidence_threshold():
    evidence = identify_consequence_evidence(
        {
            "confidentiality": 39,
            "integrity": 40,
        },
        threshold=40,
    )

    assert len(evidence) == 1


def test_estimator():
    estimator = SecurityConsequenceEstimator()

    result = estimator.estimate(
        "agent-1-cf-1",
        {
            "confidentiality": 80,
            "integrity": 20,
            "availability": 10,
            "scope": 60,
            "privilege": 70,
            "persistence": 10,
        },
        evidence=[
            "Resource sensitivity increased",
        ],
        assumptions=[
            "Hypothetical resource access is permitted",
        ],
    )

    assert result.scenario_id == "agent-1-cf-1"
    assert 0 <= result.consequence_score <= 100
    assert result.consequence_level in {
        "NONE",
        "LOW",
        "MODERATE",
        "HIGH",
        "CRITICAL",
    }


def test_estimator_generates_evidence():
    estimator = SecurityConsequenceEstimator()

    result = estimator.estimate(
        "scenario-1",
        {
            "confidentiality": 80,
            "integrity": 10,
        },
    )

    assert result.evidence
    assert any(
        "confidentiality" in item.lower()
        for item in result.evidence
    )


def test_estimator_confidence_uses_evidence():
    estimator = SecurityConsequenceEstimator()

    result = estimator.estimate(
        "scenario-1",
        {
            "confidentiality": 80,
        },
        evidence=[
            "Evidence 1",
            "Evidence 2",
            "Evidence 3",
        ],
        assumptions=[],
    )

    assert result.confidence == "HIGH"


def test_estimator_confidence_accounts_for_assumptions():
    estimator = SecurityConsequenceEstimator()

    result = estimator.estimate(
        "scenario-1",
        {
            "confidentiality": 80,
        },
        evidence=[],
        assumptions=[
            "Assumption 1",
            "Assumption 2",
            "Assumption 3",
            "Assumption 4",
        ],
    )

    assert result.confidence == "LOW"


def test_estimator_preserves_dimensions():
    estimator = SecurityConsequenceEstimator()

    dimensions = {
        "confidentiality": 70,
        "integrity": 30,
    }

    result = estimator.estimate(
        "scenario-1",
        dimensions,
    )

    assert result.dimensions == dimensions


def test_estimator_copies_evidence():
    estimator = SecurityConsequenceEstimator()

    evidence = ["Evidence A"]

    result = estimator.estimate(
        "scenario-1",
        {
            "confidentiality": 70,
        },
        evidence=evidence,
    )

    evidence.append("Evidence B")

    assert result.evidence != evidence
    assert "Evidence B" not in result.evidence


def test_estimator_copies_assumptions():
    estimator = SecurityConsequenceEstimator()

    assumptions = ["Assumption A"]

    result = estimator.estimate(
        "scenario-1",
        {
            "confidentiality": 70,
        },
        assumptions=assumptions,
    )

    assumptions.append("Assumption B")

    assert result.assumptions == [
        "Assumption A"
    ]


def test_zero_consequence():
    estimator = SecurityConsequenceEstimator()

    result = estimator.estimate(
        "scenario-1",
        {
            "confidentiality": 0,
            "integrity": 0,
            "availability": 0,
            "scope": 0,
            "privilege": 0,
            "persistence": 0,
        },
    )

    assert result.consequence_score == 0
    assert result.consequence_level == "NONE"


def test_maximum_consequence():
    estimator = SecurityConsequenceEstimator()

    result = estimator.estimate(
        "scenario-1",
        {
            "confidentiality": 100,
            "integrity": 100,
            "availability": 100,
            "scope": 100,
            "privilege": 100,
            "persistence": 100,
        },
    )

    assert result.consequence_score == 100
    assert result.consequence_level == "CRITICAL"


def test_custom_weights():
    estimator = SecurityConsequenceEstimator(
        weights={
            "confidentiality": 1.0,
        }
    )

    result = estimator.estimate(
        "scenario-1",
        {
            "confidentiality": 90,
        },
    )

    assert result.consequence_score == 90


def test_custom_evidence_threshold():
    estimator = SecurityConsequenceEstimator(
        evidence_threshold=70,
    )

    result = estimator.estimate(
        "scenario-1",
        {
            "confidentiality": 75,
            "integrity": 50,
        },
    )

    assert len(result.evidence) == 1


def test_invalid_scenario_id():
    estimator = SecurityConsequenceEstimator()

    try:
        estimator.estimate(
            "",
            {"confidentiality": 50},
        )
        assert False
    except ValueError:
        pass


def test_invalid_dimension_score():
    estimator = SecurityConsequenceEstimator()

    try:
        estimator.estimate(
            "scenario-1",
            {"confidentiality": 101},
        )
        assert False
    except ValueError:
        pass


def test_negative_dimension_score():
    estimator = SecurityConsequenceEstimator()

    try:
        estimator.estimate(
            "scenario-1",
            {"confidentiality": -1},
        )
        assert False
    except ValueError:
        pass


def test_empty_estimation_dimensions():
    estimator = SecurityConsequenceEstimator()

    try:
        estimator.estimate(
            "scenario-1",
            {},
        )
        assert False
    except ValueError:
        pass


def test_invalid_weights():
    try:
        aggregate_consequence(
            {"confidentiality": 50},
            {"confidentiality": -1},
        )
        assert False
    except ValueError:
        pass


def test_zero_total_weights():
    try:
        aggregate_consequence(
            {"confidentiality": 50},
            {"confidentiality": 0},
        )
        assert False
    except ValueError:
        pass


def test_invalid_confidence_counts():
    try:
        classify_confidence(
            -1,
            0,
        )
        assert False
    except ValueError:
        pass


def test_result_is_not_security_decision():
    estimator = SecurityConsequenceEstimator()

    result = estimator.estimate(
        "scenario-1",
        {
            "confidentiality": 100,
            "integrity": 100,
        },
    )

    assert hasattr(
        result,
        "consequence_score",
    )

    assert hasattr(
        result,
        "consequence_level",
    )

    assert hasattr(
        result,
        "confidence",
    )

    assert not hasattr(
        result,
        "decision",
    )

    assert not hasattr(
        result,
        "response",
    )

    assert not hasattr(
        result,
        "action",
    )


def test_same_input_is_deterministic():
    estimator = SecurityConsequenceEstimator()

    dimensions = {
        "confidentiality": 80,
        "integrity": 40,
        "availability": 20,
    }

    first = estimator.estimate(
        "scenario-1",
        dimensions,
        evidence=["Evidence"],
        assumptions=["Assumption"],
    )

    second = estimator.estimate(
        "scenario-1",
        dimensions,
        evidence=["Evidence"],
        assumptions=["Assumption"],
    )

    assert first == second