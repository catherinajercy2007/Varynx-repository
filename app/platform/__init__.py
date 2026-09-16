"""
Varynx platform foundation.

Provides configuration, health/readiness checks, lightweight
platform metrics, and behavioral baseline integration without
modifying the core security engine.
"""

from .behavioral import BehavioralPlatformAdapter
from .config import PlatformConfig, get_platform_config
from .health import health_check, readiness_check
from .metrics import PlatformMetrics, get_metrics

__all__ = [
    "BehavioralPlatformAdapter",
    "PlatformConfig",
    "get_platform_config",
    "health_check",
    "readiness_check",
    "PlatformMetrics",
    "get_metrics",
]