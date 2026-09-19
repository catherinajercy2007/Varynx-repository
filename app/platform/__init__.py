"""
Varynx platform foundation.

Provides configuration, health/readiness checks, lightweight
platform metrics, behavioral baseline integration, behavioral
intelligence integration, and BCSE scenario integration without
modifying the core security engine.
"""

from .behavioral import BehavioralPlatformAdapter
from .bcse import BCSEPlatformAdapter
from .bcse_consequence import BCSEConsequencePlatformAdapter
from .config import PlatformConfig, get_platform_config
from .health import health_check, readiness_check
from .metrics import PlatformMetrics, get_metrics
from .bcse_context import BCSEContextPlatformAdapter
from app.platform.bcse_evaluation import (
    BCSEEvaluationPlatformAdapter,
)
from app.platform.bcse_integration import (
    BCSEIntegrationPlatformAdapter,
)
from app.platform.predictive_security import PredictiveSecurityPlatformAdapter
__all__ = [
    "BCSEContextPlatformAdapter",
    "BehavioralPlatformAdapter",
    "BCSEPlatformAdapter",
    "BCSEConsequencePlatformAdapter",
    "PlatformConfig",
    "get_platform_config",
    "health_check",
    "readiness_check",
    "PlatformMetrics",
    "get_metrics",
    "BCSEEvaluationPlatformAdapter",
    "BCSEIntegrationPlatformAdapter",
    "PredictiveSecurityPlatformAdapter",
]