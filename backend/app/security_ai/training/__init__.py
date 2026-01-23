"""
Training & Evaluation Strategy Module

Enterprise-grade training, evaluation, and continuous learning system
for the security vulnerability detection model.

Architecture:
    ┌─────────────────────────────────────────────────────────────────┐
    │                    TRAINING PIPELINE                            │
    ├─────────────────────────────────────────────────────────────────┤
    │                                                                 │
    │  Dataset ──► Preprocessing ──► Training ──► Evaluation         │
    │     │                              │              │             │
    │     │                              ▼              ▼             │
    │     │                        Checkpoints    Metrics Logger      │
    │     │                              │              │             │
    │     └──────────────────────────────┴──────────────┘             │
    │                                    │                            │
    │                                    ▼                            │
    │                         Continuous Learning Loop                │
    │                                    │                            │
    │                    ┌───────────────┼───────────────┐            │
    │                    │               │               │            │
    │                    ▼               ▼               ▼            │
    │              Misclassification  Human Review   Automated        │
    │              Logger             Feedback      Retraining        │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
"""

from .metrics import (
    SecurityMetrics,
    MetricsCalculator,
    ConfusionMatrixAnalyzer,
    FalsePositiveTracker,
    ClasswiseMetrics,
)

from .data_splitting import (
    DataSplitter,
    SplitStrategy,
    StratifiedSplitter,
    TemporalSplitter,
    CrossValidator,
)

from .class_balancer import (
    ClassBalancer,
    BalancingStrategy,
    SMOTEBalancer,
    FocalLossWeighter,
    ThresholdOptimizer,
)

from .training_loop import (
    TrainingConfig,
    TrainingLoop,
    EarlyStopping,
    LearningRateScheduler,
    CheckpointManager,
)

from .evaluation import (
    ModelEvaluator,
    EvaluationReport,
    SecurityBenchmark,
    RegressionTester,
)

from .continuous_learning import (
    MisclassificationLogger,
    FeedbackCollector,
    RetrainingTrigger,
    ContinuousLearningPipeline,
)

__all__ = [
    # Metrics
    "SecurityMetrics",
    "MetricsCalculator",
    "ConfusionMatrixAnalyzer",
    "FalsePositiveTracker",
    "ClasswiseMetrics",
    # Data Splitting
    "DataSplitter",
    "SplitStrategy",
    "StratifiedSplitter",
    "TemporalSplitter",
    "CrossValidator",
    # Class Balancing
    "ClassBalancer",
    "BalancingStrategy",
    "SMOTEBalancer",
    "FocalLossWeighter",
    "ThresholdOptimizer",
    # Training
    "TrainingConfig",
    "TrainingLoop",
    "EarlyStopping",
    "LearningRateScheduler",
    "CheckpointManager",
    # Evaluation
    "ModelEvaluator",
    "EvaluationReport",
    "SecurityBenchmark",
    "RegressionTester",
    # Continuous Learning
    "MisclassificationLogger",
    "FeedbackCollector",
    "RetrainingTrigger",
    "ContinuousLearningPipeline",
]
