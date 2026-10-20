
"""Day 82: Behavioral Runtime Rate-Limit Assessment for Varynx.

Evaluates recorded activity against configurable rolling-window limits.
This module produces recommendations only; it does not throttle,
authorize, or execute runtime enforcement.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from math import isfinite
from typing import Any, Iterable


VERSION = "DAY82-V1"

STATUS_WITHIN_LIMIT = "WITHIN_LIMIT"
STATUS_LIMIT_REACHED = "LIMIT_REACHED"
STATUS_LIMIT_EXCEEDED = "LIMIT_EXCEEDED"

RECOMMEND_CONTINUE_MONITORING = "CONTINUE_MONITORING"
RECOMMEND_REVIEW_RATE_LIMIT = "REVIEW_RATE_LIMIT"
RECOMMEND_RESTRICT_RATE = "RESTRICT_RATE"

REASON_WITHIN_LIMIT = "REQUEST_WITHIN_CONFIGURED_RATE_LIMIT"
REASON_LIMIT_REACHED = "REQUEST_REACHES_CONFIGURED_RATE_LIMIT"
REASON_LIMIT_EXCEEDED = "REQUEST_EXCEEDS_CONFIGURED_RATE_LIMIT"


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _aware_datetime(value: Any, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{field} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")
    return value


def _positive_integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    if value < 1:
        raise ValueError(f"{field} must be at least 1")
    return value


@dataclass(frozen=True)
class RateLimitPolicy:
    """A per-key rolling-window request limit."""

    policy_id: str
    max_requests: int
    window_seconds: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "policy_id", _text(self.policy_id, "policy_id")
        )
        object.__setattr__(
            self,
            "max_requests",
            _positive_integer(self.max_requests, "max_requests"),
        )
        object.__setattr__(
            self,
            "window_seconds",
            _positive_integer(self.window_seconds, "window_seconds"),
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["version"] = VERSION
        return result


@dataclass(frozen=True)
class RateLimitEvent:
    """One previously observed event for rate assessment."""

    agent_id: str
    capability: str
    resource: str
    timestamp: datetime
    correlation_id: str

    def __post_init__(self) -> None:
        for field in ("agent_id", "capability", "resource", "correlation_id"):
            object.__setattr__(
                self, field, _text(getattr(self, field), field)
            )
        object.__setattr__(
            self,
            "timestamp",
            _aware_datetime(self.timestamp, "timestamp"),
        )


@dataclass(frozen=True)
class RateLimitAssessment:
    """Immutable assessment; never an enforcement result."""

    policy_id: str
    agent_id: str
    capability: str
    resource: str
    correlation_id: str
    status: str
    prior_requests_in_window: int
    projected_requests_in_window: int
    max_requests: int
    window_seconds: int
    window_start: datetime
    evaluated_at: datetime
    recommendation: str
    reason_codes: tuple[str, ...]

    @property
    def limit_exceeded(self) -> bool:
        return self.projected_requests_in_window > self.max_requests

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["version"] = VERSION
        result["window_start"] = self.window_start.isoformat()
        result["evaluated_at"] = self.evaluated_at.isoformat()
        result["reason_codes"] = list(self.reason_codes)
        result["limit_exceeded"] = self.limit_exceeded
        result["is_authorization_decision"] = False
        result["executes_throttling"] = False
        result["executes_enforcement"] = False
        return result


def assess_runtime_rate_limit(
    *,
    policy: RateLimitPolicy,
    agent_id: str,
    capability: str,
    resource: str,
    correlation_id: str,
    now: datetime,
    prior_events: Iterable[RateLimitEvent],
) -> RateLimitAssessment:
    """Assess one proposed request using a rolling time window.

    The current proposed request is counted once. Prior events are counted
    only when they match the exact agent, capability, and resource and fall
    in the interval (now - window, now]. Future events are ignored.

    This is an assessment over caller-supplied evidence, not a live
    rate limiter. The caller must supply trustworthy event history.
    """
    if not isinstance(policy, RateLimitPolicy):
        raise TypeError("policy must be a RateLimitPolicy")

    agent_id = _text(agent_id, "agent_id")
    capability = _text(capability, "capability")
    resource = _text(resource, "resource")
    correlation_id = _text(correlation_id, "correlation_id")
    now = _aware_datetime(now, "now")

    if isinstance(prior_events, (str, bytes, dict)):
        raise TypeError("prior_events must be an iterable of RateLimitEvent")

    try:
        events = tuple(prior_events)
    except TypeError as exc:
        raise TypeError(
            "prior_events must be an iterable of RateLimitEvent"
        ) from exc

    if any(not isinstance(event, RateLimitEvent) for event in events):
        raise TypeError("prior_events must contain only RateLimitEvent values")

    for event in events:
        if event.timestamp.utcoffset() != now.utcoffset():
            # Different timezone offsets are valid instants, so this check
            # intentionally does not reject them. Datetime comparison below
            # handles timezone-aware timestamps.
            pass

    window_start = now - timedelta(seconds=policy.window_seconds)

    matching = [
        event
        for event in events
        if event.agent_id == agent_id
        and event.capability == capability
        and event.resource == resource
        and window_start < event.timestamp <= now
    ]

    # A repeated correlation ID must not inflate the historical count.
    # Preserve the first event for each ID, deterministically.
    unique_by_id: dict[str, RateLimitEvent] = {}
    for event in sorted(
        matching,
        key=lambda item: (item.timestamp, item.correlation_id),
    ):
        unique_by_id.setdefault(event.correlation_id, event)

    prior_count = len(unique_by_id)
    projected_count = prior_count + 1

    if projected_count < policy.max_requests:
        status = STATUS_WITHIN_LIMIT
        recommendation = RECOMMEND_CONTINUE_MONITORING
        reason = REASON_WITHIN_LIMIT
    elif projected_count == policy.max_requests:
        status = STATUS_LIMIT_REACHED
        recommendation = RECOMMEND_REVIEW_RATE_LIMIT
        reason = REASON_LIMIT_REACHED
    else:
        status = STATUS_LIMIT_EXCEEDED
        recommendation = RECOMMEND_RESTRICT_RATE
        reason = REASON_LIMIT_EXCEEDED

    return RateLimitAssessment(
        policy_id=policy.policy_id,
        agent_id=agent_id,
        capability=capability,
        resource=resource,
        correlation_id=correlation_id,
        status=status,
        prior_requests_in_window=prior_count,
        projected_requests_in_window=projected_count,
        max_requests=policy.max_requests,
        window_seconds=policy.window_seconds,
        window_start=window_start,
        evaluated_at=now,
        recommendation=recommendation,
        reason_codes=(reason,),
    )


__all__ = [
    "VERSION",
    "RateLimitPolicy",
    "RateLimitEvent",
    "RateLimitAssessment",
    "assess_runtime_rate_limit",
    "STATUS_WITHIN_LIMIT",
    "STATUS_LIMIT_REACHED",
    "STATUS_LIMIT_EXCEEDED",
    "RECOMMEND_CONTINUE_MONITORING",
    "RECOMMEND_REVIEW_RATE_LIMIT",
    "RECOMMEND_RESTRICT_RATE",
]
