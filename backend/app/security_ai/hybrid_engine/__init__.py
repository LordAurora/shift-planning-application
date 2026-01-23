"""
Hybrid AI Security Engine

Enterprise-grade security detection combining:
- Rule-based layer: Deterministic detection of known vulnerabilities
- ML-based layer: Pattern recognition for unknown/emerging threats
- Fusion layer: Intelligent result combination with confidence scoring

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                      INPUT (Code/Request)                    │
    └─────────────────────────────┬───────────────────────────────┘
                                  │
              ┌───────────────────┴───────────────────┐
              ▼                                       ▼
    ┌─────────────────────┐                ┌─────────────────────┐
    │   RULE ENGINE       │                │   ML ENGINE         │
    │   (Deterministic)   │                │   (Probabilistic)   │
    │                     │                │                     │
    │ • Regex patterns    │                │ • Transformer       │
    │ • AST analysis      │                │ • Attention-based   │
    │ • Known signatures  │                │ • Multi-label       │
    └─────────┬───────────┘                └─────────┬───────────┘
              │                                       │
              │  RuleResult[]                         │  MLPrediction
              │                                       │
              └───────────────────┬───────────────────┘
                                  ▼
                    ┌─────────────────────────┐
                    │     FUSION ENGINE       │
                    │                         │
                    │ • Priority arbitration  │
                    │ • Confidence scoring    │
                    │ • FP suppression        │
                    └───────────┬─────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │   HybridDetectionResult │
                    └─────────────────────────┘

See HYBRID_ENGINE.md for detailed design rationale.
"""

from .rule_engine import (
    RuleEngine,
    SecurityRule,
    RuleResult,
    RuleSeverity,
    RuleCategory,
    CriticalRules,
)

from .ml_adapter import (
    MLEngineAdapter,
    MLPrediction,
    MLConfidence,
)

from .fusion_engine import (
    FusionEngine,
    FusionStrategy,
    HybridDetectionResult,
    DetectionSource,
    ConfidenceScore,
)

from .hybrid_detector import (
    HybridSecurityDetector,
    HybridConfig,
    DetectionMode,
)

__all__ = [
    # Rule Engine
    "RuleEngine",
    "SecurityRule",
    "RuleResult",
    "RuleSeverity",
    "RuleCategory",
    "CriticalRules",
    # ML Adapter
    "MLEngineAdapter",
    "MLPrediction",
    "MLConfidence",
    # Fusion Engine
    "FusionEngine",
    "FusionStrategy",
    "HybridDetectionResult",
    "DetectionSource",
    "ConfidenceScore",
    # Hybrid Detector
    "HybridSecurityDetector",
    "HybridConfig",
    "DetectionMode",
]
