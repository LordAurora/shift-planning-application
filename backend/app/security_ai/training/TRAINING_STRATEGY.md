# Training & Evaluation Strategy

## Module 4: Realistic Training, Evaluation, and Iteration

This document defines the complete training, evaluation, and continuous learning strategy for the Security AI vulnerability detection system.

---

## 1. Training Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TRAINING PIPELINE ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐     ┌──────────────┐     ┌─────────────────┐             │
│   │  Raw Code   │────▶│ Preprocessor │────▶│ Feature Vectors │             │
│   │  Dataset    │     │  (Tokenize)  │     │  (Embedded)     │             │
│   └─────────────┘     └──────────────┘     └────────┬────────┘             │
│                                                      │                      │
│   ┌──────────────────────────────────────────────────▼──────────────────┐  │
│   │                      DATA SPLITTING STRATEGY                        │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │  │
│   │  │   Train     │  │ Validation  │  │    Test     │                  │  │
│   │  │   (70%)     │  │   (15%)     │  │   (15%)     │                  │  │
│   │  │             │  │             │  │  (FROZEN)   │                  │  │
│   │  └──────┬──────┘  └──────┬──────┘  └─────────────┘                  │  │
│   └─────────│───────────────│────────────────────────────────────────────┘  │
│             │               │                                               │
│   ┌─────────▼───────────────▼─────────────────────────────────────────┐    │
│   │                      CLASS BALANCING                              │    │
│   │  ┌──────────┐  ┌──────────┐  ┌─────────────┐  ┌──────────────┐   │    │
│   │  │ SMOTE    │  │ Focal    │  │ Class       │  │ Threshold    │   │    │
│   │  │ Sampling │  │ Loss     │  │ Weights     │  │ Optimization │   │    │
│   │  └──────────┘  └──────────┘  └─────────────┘  └──────────────┘   │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│   ┌────────────────────────────────▼────────────────────────────────────┐  │
│   │                       TRAINING LOOP                                 │  │
│   │  ┌─────────────────────────────────────────────────────────────┐   │  │
│   │  │  for epoch in epochs:                                        │   │  │
│   │  │      train_step(model, X_train, y_train)                     │   │  │
│   │  │      val_metrics = validate(model, X_val, y_val)             │   │  │
│   │  │      lr_scheduler.step(epoch)                                │   │  │
│   │  │      if early_stopping.should_stop(val_metrics): break       │   │  │
│   │  │      checkpoint_manager.save_if_best(val_metrics)            │   │  │
│   │  └─────────────────────────────────────────────────────────────┘   │  │
│   └────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Metrics Framework

### 2.1 Primary Metrics

| Metric | Formula | Target | Priority |
|--------|---------|--------|----------|
| **Recall** | TP / (TP + FN) | ≥ 95% | **CRITICAL** |
| **False Positive Rate** | FP / (FP + TN) | ≤ 10% | **CRITICAL** |
| **Precision** | TP / (TP + FP) | ≥ 80% | HIGH |
| **F1 Score** | 2 × (P × R) / (P + R) | ≥ 85% | HIGH |
| **Matthews Correlation** | (TP×TN - FP×FN) / √(...) | ≥ 0.80 | MEDIUM |

### 2.2 Why Recall is Critical

```
Security Context:
- FALSE NEGATIVE = Missed vulnerability = SECURITY BREACH
- FALSE POSITIVE = Alert fatigue = Reduced trust

Risk Assessment:
┌──────────────────────────────────────────────────────────┐
│  Missed SQL Injection  →  Data breach  →  $4.45M avg    │
│  False alarm on clean  →  Dev annoyance →  Minutes lost │
└──────────────────────────────────────────────────────────┘

Conclusion: Prioritize recall (catch everything), then optimize precision
```

### 2.3 Per-Class Metrics

Critical vulnerability classes require **99% recall minimum**:

```python
CRITICAL_CLASSES = [
    "sql_injection",           # CWE-89   - Database compromise
    "command_injection",       # CWE-78   - System takeover
    "path_traversal",          # CWE-22   - File access
    "code_injection",          # CWE-94   - Arbitrary execution
    "insecure_deserialization", # CWE-502 - RCE
    "hardcoded_credentials",   # CWE-798  - Auth bypass
]
```

---

## 3. Dataset Splitting Strategy

### 3.1 Standard Split (Stratified)

```python
# Maintain class distribution across splits
splitter = StratifiedSplitter(
    train_ratio=0.70,
    val_ratio=0.15,
    test_ratio=0.15,
    random_seed=42,
)

train, val, test = splitter.split(X, y)
```

**Why Stratified?**
- Security datasets are highly imbalanced
- SQL injection: ~5% of samples
- Hardcoded credentials: ~2% of samples
- Random split might miss rare classes entirely

### 3.2 Temporal Split (Production Simulation)

```python
# Train on older code, test on newer code
splitter = TemporalSplitter(
    train_cutoff=0.70,  # First 70% by date
    val_cutoff=0.85,    # Next 15%
)

train, val, test = splitter.split(X, y, timestamps)
```

**Why Temporal?**
- Simulates real-world deployment
- Detects if model generalizes to new patterns
- Catches overfitting to historical patterns

### 3.3 Cross-Validation (Hyperparameter Tuning)

```python
# K-Fold with stratification
cross_validator = CrossValidator(
    n_folds=5,
    stratified=True,
)

for fold_num, (train_idx, val_idx) in cross_validator.split(X, y):
    # Train and evaluate on fold
    pass
```

---

## 4. Handling Class Imbalance

### 4.1 The Imbalance Problem

```
Real-world security dataset distribution:
┌─────────────────────────────────────────────────────────┐
│ Class                    │ Samples │ Percentage │       │
├─────────────────────────────────────────────────────────┤
│ Clean (no vulnerability) │ 80,000  │   80.0%    │ ████████████████ │
│ SQL Injection            │  5,000  │    5.0%    │ █               │
│ XSS                      │  4,000  │    4.0%    │ █               │
│ Path Traversal           │  3,000  │    3.0%    │ █               │
│ Hardcoded Credentials    │  2,000  │    2.0%    │ ▌               │
│ Command Injection        │  1,500  │    1.5%    │ ▌               │
│ Other (9 classes)        │  4,500  │    4.5%    │ █               │
└─────────────────────────────────────────────────────────┘

Problem: Model learns to predict "clean" 80% of the time
```

### 4.2 Solution: Multi-Strategy Approach

#### Strategy 1: SMOTE Oversampling

```python
# Synthetic Minority Over-sampling Technique
smote_balancer = SMOTEBalancer(
    k_neighbors=5,
    target_ratio=0.5,  # Balance to 50%
)

X_balanced, y_balanced = smote_balancer.balance(X_train, y_train)
```

**How SMOTE Works:**
1. Select minority class sample
2. Find k nearest neighbors
3. Create synthetic sample along line between them
4. Repeat until balanced

#### Strategy 2: Focal Loss

```python
# Focus on hard examples
focal_loss = FocalLossWeighter(
    gamma=2.0,  # Focus factor
    alpha=None, # Auto-compute from class distribution
)

# During training
loss = focal_loss.compute_loss(y_true, y_pred)
```

**Focal Loss Formula:**
```
FL(p) = -α(1 - p)^γ × log(p)

Where:
- p = predicted probability for true class
- γ = focusing parameter (2.0 works well)
- α = class weight

Effect: Down-weights easy examples, focuses on hard ones
```

#### Strategy 3: Per-Class Thresholds

```python
# Optimize threshold per class
optimizer = ThresholdOptimizer(min_recall=0.95)

thresholds = optimizer.optimize(
    y_true=y_val,
    y_prob=model.predict(X_val),
)

# Result: {"sql_injection": 0.3, "xss": 0.45, ...}
```

**Why Different Thresholds?**
- Critical vulnerabilities: Lower threshold (catch more)
- Informational issues: Higher threshold (reduce noise)

---

## 5. Training Loop Configuration

### 5.1 Recommended Configuration

```python
config = TrainingConfig(
    # Basic
    epochs=100,
    batch_size=32,
    
    # Learning rate
    learning_rate=1e-4,
    lr_schedule="warmup_cosine",
    warmup_epochs=5,
    
    # Early stopping
    early_stopping_patience=10,
    early_stopping_metric="val_recall",  # CRITICAL: Monitor recall!
    early_stopping_mode="max",
    
    # Class balancing
    use_class_weights=True,
    use_focal_loss=True,
    focal_gamma=2.0,
    
    # Checkpointing
    checkpoint_metric="val_f1",
    save_best_only=True,
)
```

### 5.2 Learning Rate Schedule

```
Warmup Cosine Schedule:
┌────────────────────────────────────────────────────────────┐
│ LR │                                                        │
│    │  ╭─────────────────╮                                   │
│    │ ╱                   ╲                                  │
│ 1e-4 ╱                     ╲                                │
│    ╱                        ╲                               │
│   ╱                          ╲                              │
│  ╱                            ╲                             │
│ ╱ Warmup                       ╲ Cosine decay               │
│ 5 epochs                        ╲                           │
│                                  ╲────────────────          │
│                                                  → min_lr   │
└──────────────────────────────────────────────────Epochs─────┘
     0     5     20    40    60    80    100
```

### 5.3 Early Stopping Strategy

```python
early_stopper = EarlyStopping(
    patience=10,
    min_delta=0.001,
    metric="val_recall",
    mode="max",
    restore_best_weights=True,
)

# Stops training if recall doesn't improve for 10 epochs
```

---

## 6. Evaluation Methodology

### 6.1 Evaluation Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EVALUATION PIPELINE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐    │
│   │ 1. METRICS CALCULATION                                            │    │
│   │    ├── Overall: Precision, Recall, F1, FPR, MCC                   │    │
│   │    ├── Per-Class: Same metrics for each vulnerability type        │    │
│   │    └── Critical Classes: Separate tracking for severe vulns       │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│   ┌───────────────────────────────▼───────────────────────────────────┐    │
│   │ 2. THRESHOLD ANALYSIS                                             │    │
│   │    ├── Test at: 0.3, 0.4, 0.5, 0.6, 0.7, 0.8                      │    │
│   │    ├── Find optimal threshold for target recall                   │    │
│   │    └── Per-class threshold optimization                           │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│   ┌───────────────────────────────▼───────────────────────────────────┐    │
│   │ 3. ERROR ANALYSIS                                                 │    │
│   │    ├── Confusion matrix analysis                                  │    │
│   │    ├── Most confused class pairs                                  │    │
│   │    └── False positive/negative patterns                           │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│   ┌───────────────────────────────▼───────────────────────────────────┐    │
│   │ 4. SECURITY REQUIREMENTS CHECK                                    │    │
│   │    ├── Overall recall ≥ 95%                                       │    │
│   │    ├── Critical class recall ≥ 99%                                │    │
│   │    ├── FPR ≤ 10%                                                  │    │
│   │    └── Pass/Fail determination                                    │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Evaluation Report Example

```markdown
# Evaluation Report: security_model v1.2.0
**Date:** 2024-01-15

## Overall Metrics
| Metric | Value |
|--------|-------|
| Precision | 0.8523 |
| Recall | 0.9612 |
| F1 Score | 0.9035 |
| False Positive Rate | 0.0834 |
| Matthews Correlation | 0.8891 |

## Security Requirements
✅ **All security requirements PASSED**

## Critical Vulnerability Detection
| Class | Recall | Precision | F1 | Support |
|-------|--------|-----------|-------|---------|
| sql_injection | 0.9920 | 0.8750 | 0.9298 | 500 |
| command_injection | 0.9933 | 0.8820 | 0.9343 | 150 |
| path_traversal | 0.9900 | 0.8910 | 0.9380 | 300 |
```

### 6.3 Benchmark Testing

```python
benchmark = SecurityBenchmark(model, preprocessor)
results = benchmark.run_benchmark()

# Tests against known patterns:
# ✅ sql_injection_fstring: Detected
# ✅ command_injection_system: Detected
# ✅ hardcoded_password: Detected
# ✅ clean_parameterized: No false positive
```

---

## 7. Continuous Learning Loop

### 7.1 Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CONTINUOUS LEARNING CYCLE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐                                                          │
│   │  PRODUCTION │◀─────────────────────────────────────────────┐           │
│   │    MODEL    │                                              │           │
│   └──────┬──────┘                                              │           │
│          │                                                     │           │
│          ▼                                                     │           │
│   ┌─────────────────────────────────────────────────┐          │           │
│   │         INFERENCE MONITORING                    │          │           │
│   │  ┌─────────────┐  ┌─────────────────────────┐   │          │           │
│   │  │ Predictions │  │ Confidence Scores       │   │          │           │
│   │  └──────┬──────┘  └───────────┬─────────────┘   │          │           │
│   └─────────│─────────────────────│─────────────────┘          │           │
│             │                     │                            │           │
│             ▼                     ▼                            │           │
│   ┌─────────────────────────────────────────────────┐          │           │
│   │           FEEDBACK COLLECTION                   │          │           │
│   │  ┌─────────────────┐  ┌─────────────────────┐   │          │           │
│   │  │ Human Review    │  │ Auto Misclass Log   │   │          │           │
│   │  │ (Corrections)   │  │ (Ground Truth)      │   │          │           │
│   │  └────────┬────────┘  └───────────┬─────────┘   │          │           │
│   └───────────│───────────────────────│─────────────┘          │           │
│               │                       │                        │           │
│               ▼                       ▼                        │           │
│   ┌─────────────────────────────────────────────────┐          │           │
│   │           RETRAINING TRIGGERS                   │          │           │
│   │  • Error rate > 15%                             │          │           │
│   │  • Critical recall < 95%                        │          │           │
│   │  • 30 days since last retrain                   │          │           │
│   │  • 500+ new samples available                   │          │           │
│   └─────────────────────┬───────────────────────────┘          │           │
│                         │                                      │           │
│               ┌─────────▼──────────┐                           │           │
│               │ Trigger Activated? │                           │           │
│               └─────────┬──────────┘                           │           │
│                         │ YES                                  │           │
│                         ▼                                      │           │
│   ┌─────────────────────────────────────────────────┐          │           │
│   │             RETRAINING CYCLE                    │          │           │
│   │  1. Prepare data (base + feedback)              │          │           │
│   │  2. Retrain model                               │          │           │
│   │  3. Evaluate on test set                        │          │           │
│   │  4. Regression testing                          │          │           │
│   │  5. If improved & passes reqs → Deploy          │          │           │
│   └─────────────────────────────────────────────────┘          │           │
│                         │                                      │           │
│                         └──────────────────────────────────────┘           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Manual Review Process

```
Human-in-the-Loop Workflow:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  1. Model flags code as vulnerable                          │
│                    │                                        │
│                    ▼                                        │
│  2. Security engineer reviews:                              │
│     ┌──────────────────────────────────────────────┐       │
│     │ Code: query = f"SELECT * FROM {table}"       │       │
│     │ Prediction: sql_injection (85%)              │       │
│     │                                              │       │
│     │ [✓ Correct]  [✗ False Positive]  [Edit]     │       │
│     └──────────────────────────────────────────────┘       │
│                    │                                        │
│                    ▼                                        │
│  3. Feedback stored for retraining                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Automated Triggers

```python
trigger_config = RetrainingTriggerConfig(
    # Performance degradation
    max_error_rate=0.15,           # 15% errors from feedback
    min_critical_recall=0.95,      # Critical vulns recall
    
    # Time-based
    max_days_since_retrain=30,     # Monthly minimum
    
    # Data availability
    min_new_samples=500,           # Enough new data
)
```

### 7.4 Deployment Criteria

New model deployed only if:

1. ✅ **Recall ≥ previous model** (no regression on detection)
2. ✅ **F1 ≥ previous model** (overall improvement)
3. ✅ **FPR ≤ previous + 2%** (no significant FP increase)
4. ✅ **Passes security requirements** (absolute thresholds met)
5. ✅ **Passes regression tests** (known patterns still detected)

---

## 8. Implementation Summary

### 8.1 Module Files

| File | Purpose |
|------|---------|
| `metrics.py` | SecurityMetrics, MetricsCalculator, ConfusionMatrixAnalyzer, FalsePositiveTracker |
| `data_splitting.py` | DataSplitter, StratifiedSplitter, TemporalSplitter, CrossValidator |
| `class_balancer.py` | ClassBalancer, SMOTEBalancer, FocalLossWeighter, ThresholdOptimizer |
| `training_loop.py` | TrainingConfig, TrainingLoop, EarlyStopping, LearningRateScheduler, CheckpointManager |
| `evaluation.py` | ModelEvaluator, EvaluationReport, SecurityBenchmark, RegressionTester |
| `continuous_learning.py` | MisclassificationLogger, FeedbackCollector, RetrainingTrigger, ContinuousLearningPipeline |

### 8.2 Quick Start

```python
from training import (
    StratifiedSplitter,
    SMOTEBalancer,
    FocalLossWeighter,
    TrainingConfig,
    TrainingLoop,
    ModelEvaluator,
    ContinuousLearningPipeline,
)

# 1. Split data
splitter = StratifiedSplitter()
X_train, X_val, X_test, y_train, y_val, y_test = splitter.split(X, y)

# 2. Balance classes
balancer = SMOTEBalancer()
X_train_balanced, y_train_balanced = balancer.balance(X_train, y_train)

# 3. Configure training
config = TrainingConfig(
    epochs=100,
    use_focal_loss=True,
    early_stopping_metric="val_recall",
)

# 4. Train
trainer = TrainingLoop(model, config)
history = trainer.train(X_train_balanced, y_train_balanced, X_val, y_val)

# 5. Evaluate
evaluator = ModelEvaluator()
report = evaluator.evaluate(model, X_test, y_test)

# 6. Check requirements
passes, failures = report.passes_security_requirements()
print(f"Deployment ready: {passes}")
```

---

## 9. Key Takeaways

### Security-First Principles

1. **Recall over Precision**: Missing a vulnerability is worse than a false alarm
2. **Critical Class Focus**: SQL injection, command injection require 99%+ recall
3. **FPR Control**: Keep false positives under 10% to maintain developer trust

### Continuous Improvement

1. **Log Everything**: Track all misclassifications for analysis
2. **Human Review**: Expert feedback improves ground truth
3. **Automated Triggers**: Don't wait for complaints, proactively retrain
4. **Regression Testing**: New models must not lose capabilities

### Practical Implementation

1. **Stratified Splits**: Always maintain class distribution
2. **Multiple Balancing**: Combine SMOTE + Focal Loss + Thresholds
3. **Warmup Cosine LR**: Stable training with good convergence
4. **Early Stopping on Recall**: Stop when recall plateaus, not loss

---

*Module 4 Complete - Training & Evaluation Strategy*
