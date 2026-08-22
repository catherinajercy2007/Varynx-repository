"""
Varynx Day 34
Adaptive Response Configuration

Purpose
-------
Centralize adaptive-response thresholds and configuration.

Design principles
-----------------
1. No threshold duplication across modules.
2. Configuration is explicit and inspectable.
3. Configuration is validated before use.
4. Default values preserve the existing Day 30/31 behavior.
5. Configuration changes can be reproduced in experiments.

This module does not make security decisions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class AdaptiveThresholds:
    """
    Thresholds controlling the adaptive response ladder.

    The ranges are lower-inclusive and upper-exclusive except
    for the final BLOCK threshold.
    """

    monitoring: float = 30.0
    step_up: float = 55.0
    reduce_scope: float = 70.0
    human_review: float = 80.0
    block: float = 90.0

    def validate(self) -> None:
        """
        Validate threshold ordering and bounds.
        """

        values = {
            "monitoring": self.monitoring,
            "step_up": self.step_up,
            "reduce_scope": self.reduce_scope,
            "human_review": self.human_review,
            "block": self.block,
        }

        for name, value in values.items():
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"{name} threshold must be numeric"
                )

            if not 0 <= value <= 100:
                raise ValueError(
                    f"{name} threshold must be between 0 and 100"
                )

        ordered = [
            self.monitoring,
            self.step_up,
            self.reduce_scope,
            self.human_review,
            self.block,
        ]

        if ordered != sorted(ordered):
            raise ValueError(
                "Adaptive thresholds must be monotonically increasing"
            )

        if len(set(ordered)) != len(ordered):
            raise ValueError(
                "Adaptive thresholds must be strictly increasing"
            )

    def to_dict(self) -> dict[str, float]:
        """Return a JSON-friendly representation."""

        self.validate()

        return {
            key: float(value)
            for key, value in asdict(self).items()
        }


@dataclass(frozen=True)
class EscalationThresholds:
    """
    Thresholds for individual evidence dimensions that can
    force escalation independent of the weighted score.
    """

    critical_risk: float = 95.0
    high_anomaly: float = 80.0
    high_repeated_denial: float = 80.0
    high_cross_context: float = 85.0
    combined_cross_context_denial: float = 70.0
    critical_anomaly: float = 90.0

    def validate(self) -> None:
        """Validate escalation thresholds."""

        values = {
            "critical_risk": self.critical_risk,
            "high_anomaly": self.high_anomaly,
            "high_repeated_denial": self.high_repeated_denial,
            "high_cross_context": self.high_cross_context,
            "combined_cross_context_denial": (
                self.combined_cross_context_denial
            ),
            "critical_anomaly": self.critical_anomaly,
        }

        for name, value in values.items():
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"{name} threshold must be numeric"
                )

            if not 0 <= value <= 100:
                raise ValueError(
                    f"{name} threshold must be between 0 and 100"
                )

    def to_dict(self) -> dict[str, float]:
        """Return a JSON-friendly representation."""

        self.validate()

        return {
            key: float(value)
            for key, value in asdict(self).items()
        }


@dataclass(frozen=True)
class AdaptiveConfig:
    """
    Complete adaptive-response configuration.

    This object is immutable after creation so a running
    security decision cannot silently mutate its thresholds.
    """

    name: str = "default"
    version: str = "1.0"

    thresholds: AdaptiveThresholds = AdaptiveThresholds()
    escalation: EscalationThresholds = EscalationThresholds()

    def validate(self) -> None:
        """Validate the complete configuration."""

        if not self.name.strip():
            raise ValueError(
                "Configuration name cannot be empty"
            )

        if not self.version.strip():
            raise ValueError(
                "Configuration version cannot be empty"
            )

        self.thresholds.validate()
        self.escalation.validate()

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable configuration."""

        self.validate()

        return {
            "name": self.name,
            "version": self.version,
            "thresholds": self.thresholds.to_dict(),
            "escalation": self.escalation.to_dict(),
        }


DEFAULT_ADAPTIVE_CONFIG = AdaptiveConfig()


def get_default_adaptive_config() -> AdaptiveConfig:
    """
    Return the canonical default configuration.
    """

    DEFAULT_ADAPTIVE_CONFIG.validate()

    return DEFAULT_ADAPTIVE_CONFIG


def build_adaptive_config(
    *,
    name: str = "custom",
    version: str = "1.0",
    thresholds: Mapping[str, Any] | None = None,
    escalation: Mapping[str, Any] | None = None,
) -> AdaptiveConfig:
    """
    Build and validate a custom configuration.

    Only explicitly supplied values override defaults.
    """

    default = get_default_adaptive_config()

    threshold_values = {
        **default.thresholds.to_dict(),
        **dict(thresholds or {}),
    }

    escalation_values = {
        **default.escalation.to_dict(),
        **dict(escalation or {}),
    }

    config = AdaptiveConfig(
        name=name,
        version=version,
        thresholds=AdaptiveThresholds(
            **threshold_values
        ),
        escalation=EscalationThresholds(
            **escalation_values
        ),
    )

    config.validate()

    return config


def validate_adaptive_config(
    config: AdaptiveConfig,
) -> AdaptiveConfig:
    """
    Validate an existing configuration and return it.

    Returning the same object makes this convenient for
    dependency/configuration injection.
    """

    if not isinstance(config, AdaptiveConfig):
        raise TypeError(
            "config must be an AdaptiveConfig instance"
        )

    config.validate()

    return config


__all__ = [
    "AdaptiveThresholds",
    "EscalationThresholds",
    "AdaptiveConfig",
    "DEFAULT_ADAPTIVE_CONFIG",
    "get_default_adaptive_config",
    "build_adaptive_config",
    "validate_adaptive_config",
]