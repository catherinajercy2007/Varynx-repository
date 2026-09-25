"""
Varynx platform foundation.

Provides configuration, health/readiness checks, lightweight
platform metrics, behavioral baseline integration, behavioral
intelligence integration, BCSE scenario integration, and
predictive behavioral security integrations without modifying
the core security engine.
"""

from .behavioral import BehavioralPlatformAdapter
from .bcse import BCSEPlatformAdapter
from .bcse_consequence import BCSEConsequencePlatformAdapter
from .bcse_context import BCSEContextPlatformAdapter
from .bcse_evaluation import BCSEEvaluationPlatformAdapter
from .bcse_integration import BCSEIntegrationPlatformAdapter
from .config import PlatformConfig, get_platform_config
from .health import health_check, readiness_check
from .metrics import PlatformMetrics, get_metrics
from .predictive_control import PredictiveControlPlatformAdapter
from .predictive_forecast import PredictiveForecastPlatformAdapter
from .predictive_security import PredictiveSecurityPlatformAdapter
from .predictive_trajectory import PredictiveTrajectoryPlatformAdapter
from .predictive_runtime import PredictiveRuntimePlatformAdapter
from .unified_behavioral_pipeline import (
    UnifiedBehavioralPipelinePlatformAdapter,
)
from .security_decision_bridge import (
    SecurityDecisionBridgePlatformAdapter,
)
from .security_decision_reconciliation import (
    SecurityDecisionReconciliationPlatformAdapter,
)
from .security_decision_runtime_handoff import (
    SecurityDecisionRuntimeHandoffPlatformAdapter,
)
from .runtime_security_decision_enforcement import (
    RuntimeSecurityDecisionEnforcementBoundary,
    RuntimeSecurityRequest,
)
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
    "PredictiveTrajectoryPlatformAdapter",
    "PredictiveForecastPlatformAdapter",
    "PredictiveControlPlatformAdapter",
    "PredictiveRuntimePlatformAdapter",
    "UnifiedBehavioralPipelinePlatformAdapter",
    "SecurityDecisionBridgePlatformAdapter",
    "SecurityDecisionReconciliationPlatformAdapter",
    "SecurityDecisionRuntimeHandoffPlatformAdapter",
]