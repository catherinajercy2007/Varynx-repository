import pytest

from app.adaptive_config import (
    AdaptiveConfig,
    AdaptiveThresholds,
    EscalationThresholds,
    build_adaptive_config,
    get_default_adaptive_config,
    validate_adaptive_config,
)


def test_default_configuration_is_valid():
    config = get_default_adaptive_config()

    config.validate()

    assert config.name == "default"
    assert config.version == "1.0"


def test_default_response_thresholds_preserve_existing_behavior():
    config = get_default_adaptive_config()

    assert config.thresholds.monitoring == 30.0
    assert config.thresholds.step_up == 55.0
    assert config.thresholds.reduce_scope == 70.0
    assert config.thresholds.human_review == 80.0
    assert config.thresholds.block == 90.0


def test_default_escalation_thresholds_preserve_existing_behavior():
    config = get_default_adaptive_config()

    assert config.escalation.critical_risk == 95.0
    assert config.escalation.high_anomaly == 80.0
    assert config.escalation.high_repeated_denial == 80.0
    assert config.escalation.high_cross_context == 85.0
    assert config.escalation.combined_cross_context_denial == 70.0
    assert config.escalation.critical_anomaly == 90.0


def test_thresholds_are_strictly_increasing():
    thresholds = AdaptiveThresholds(
        monitoring=30,
        step_up=55,
        reduce_scope=70,
        human_review=80,
        block=90,
    )

    thresholds.validate()


def test_equal_thresholds_are_rejected():
    thresholds = AdaptiveThresholds(
        monitoring=30,
        step_up=30,
        reduce_scope=70,
        human_review=80,
        block=90,
    )

    with pytest.raises(ValueError):
        thresholds.validate()


def test_decreasing_thresholds_are_rejected():
    thresholds = AdaptiveThresholds(
        monitoring=50,
        step_up=40,
        reduce_scope=70,
        human_review=80,
        block=90,
    )

    with pytest.raises(ValueError):
        thresholds.validate()


def test_negative_threshold_is_rejected():
    thresholds = AdaptiveThresholds(
        monitoring=-1,
        step_up=55,
        reduce_scope=70,
        human_review=80,
        block=90,
    )

    with pytest.raises(ValueError):
        thresholds.validate()


def test_threshold_above_100_is_rejected():
    thresholds = AdaptiveThresholds(
        monitoring=30,
        step_up=55,
        reduce_scope=70,
        human_review=80,
        block=101,
    )

    with pytest.raises(ValueError):
        thresholds.validate()


def test_non_numeric_threshold_is_rejected():
    thresholds = AdaptiveThresholds(
        monitoring="30",
        step_up=55,
        reduce_scope=70,
        human_review=80,
        block=90,
    )

    with pytest.raises(TypeError):
        thresholds.validate()


def test_escalation_thresholds_validate():
    thresholds = EscalationThresholds()

    thresholds.validate()


def test_escalation_threshold_out_of_range_is_rejected():
    thresholds = EscalationThresholds(
        critical_risk=101,
    )

    with pytest.raises(ValueError):
        thresholds.validate()


def test_custom_configuration_overrides_selected_values():
    config = build_adaptive_config(
        name="research-threshold-test",
        version="2.0",
        thresholds={
            "monitoring": 25,
            "step_up": 50,
        },
    )

    assert config.name == "research-threshold-test"
    assert config.version == "2.0"

    assert config.thresholds.monitoring == 25
    assert config.thresholds.step_up == 50

    assert config.thresholds.reduce_scope == 70
    assert config.thresholds.human_review == 80
    assert config.thresholds.block == 90


def test_custom_escalation_configuration_overrides_selected_values():
    config = build_adaptive_config(
        escalation={
            "critical_risk": 90,
            "high_anomaly": 75,
        }
    )

    assert config.escalation.critical_risk == 90
    assert config.escalation.high_anomaly == 75

    assert config.escalation.high_repeated_denial == 80


def test_configuration_is_serializable():
    config = get_default_adaptive_config()

    data = config.to_dict()

    assert data["name"] == "default"
    assert data["version"] == "1.0"

    assert data["thresholds"]["monitoring"] == 30.0
    assert data["thresholds"]["block"] == 90.0

    assert data["escalation"]["critical_risk"] == 95.0


def test_custom_configuration_is_serializable():
    config = build_adaptive_config(
        name="experiment-A",
        version="1.2",
        thresholds={
            "monitoring": 35,
        },
    )

    data = config.to_dict()

    assert data["name"] == "experiment-A"
    assert data["version"] == "1.2"
    assert data["thresholds"]["monitoring"] == 35.0


def test_configuration_validation_returns_same_object():
    config = get_default_adaptive_config()

    validated = validate_adaptive_config(config)

    assert validated is config


def test_invalid_configuration_type_is_rejected():
    with pytest.raises(TypeError):
        validate_adaptive_config(
            "not-a-config"
        )


def test_empty_name_is_rejected():
    config = AdaptiveConfig(
        name="",
    )

    with pytest.raises(ValueError):
        config.validate()


def test_empty_version_is_rejected():
    config = AdaptiveConfig(
        version="",
    )

    with pytest.raises(ValueError):
        config.validate()


def test_configuration_is_immutable():
    config = get_default_adaptive_config()

    with pytest.raises(
        AttributeError
    ):
        config.name = "changed"