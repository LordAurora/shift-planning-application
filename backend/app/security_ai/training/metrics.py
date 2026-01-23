"""
Security-Focused Metrics Module

Comprehensive metrics for vulnerability detection with emphasis on:
- Minimizing false positives (alert fatigue)
- Maximizing recall for critical vulnerabilities
- Class-wise performance analysis
"""

import numpy as np
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from collections import defaultdict
import json
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# METRIC ENUMS
# =============================================================================

class MetricPriority(Enum):
    """Priority levels for different metrics in security context."""
    CRITICAL = "critical"    # Must meet threshold (e.g., recall for critical vulns)
    HIGH = "high"            # Important but some tolerance
    MEDIUM = "medium"        # Monitored
    LOW = "low"              # Informational


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SecurityMetrics:
    """
    Complete metrics for security vulnerability detection.
    
    Design: Security models prioritize recall over precision for
    critical vulnerabilities, but must maintain acceptable FPR
    to prevent alert fatigue.
    """
    # Basic metrics
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    accuracy: float = 0.0
    
    # Security-specific metrics
    false_positive_rate: float = 0.0  # FP / (FP + TN) - CRITICAL
    false_negative_rate: float = 0.0  # FN / (FN + TP)
    true_positive_rate: float = 0.0   # Same as recall
    true_negative_rate: float = 0.0   # Specificity
    
    # Confusion matrix components
    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    
    # Advanced metrics
    matthews_correlation: float = 0.0  # MCC - best for imbalanced
    cohen_kappa: float = 0.0
    balanced_accuracy: float = 0.0
    
    # Multi-label specific
    exact_match_ratio: float = 0.0     # All labels correct
    hamming_loss: float = 0.0          # Fraction of wrong labels
    
    # Threshold
    threshold: float = 0.5
    
    # Sample counts
    total_samples: int = 0
    positive_samples: int = 0
    negative_samples: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "accuracy": round(self.accuracy, 4),
            "false_positive_rate": round(self.false_positive_rate, 4),
            "false_negative_rate": round(self.false_negative_rate, 4),
            "true_positive_rate": round(self.true_positive_rate, 4),
            "true_negative_rate": round(self.true_negative_rate, 4),
            "confusion_matrix": {
                "TP": self.true_positives,
                "TN": self.true_negatives,
                "FP": self.false_positives,
                "FN": self.false_negatives,
            },
            "matthews_correlation": round(self.matthews_correlation, 4),
            "balanced_accuracy": round(self.balanced_accuracy, 4),
            "exact_match_ratio": round(self.exact_match_ratio, 4),
            "hamming_loss": round(self.hamming_loss, 4),
            "threshold": self.threshold,
            "samples": {
                "total": self.total_samples,
                "positive": self.positive_samples,
                "negative": self.negative_samples,
            }
        }
    
    def meets_security_threshold(
        self,
        min_recall: float = 0.95,
        max_fpr: float = 0.10,
    ) -> Tuple[bool, List[str]]:
        """
        Check if metrics meet security thresholds.
        
        Args:
            min_recall: Minimum recall (default 95% for security)
            max_fpr: Maximum false positive rate (default 10%)
        
        Returns:
            (passes, list of failures)
        """
        failures = []
        
        if self.recall < min_recall:
            failures.append(
                f"Recall {self.recall:.2%} below threshold {min_recall:.2%}"
            )
        
        if self.false_positive_rate > max_fpr:
            failures.append(
                f"FPR {self.false_positive_rate:.2%} above threshold {max_fpr:.2%}"
            )
        
        return len(failures) == 0, failures


@dataclass
class ClasswiseMetrics:
    """Metrics for a specific vulnerability class."""
    class_id: int
    class_name: str
    metrics: SecurityMetrics
    support: int  # Number of samples
    is_critical: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "metrics": self.metrics.to_dict(),
            "support": self.support,
            "is_critical": self.is_critical,
        }


# =============================================================================
# METRICS CALCULATOR
# =============================================================================

class MetricsCalculator:
    """
    Calculate comprehensive metrics for vulnerability detection.
    
    Features:
    - Binary and multi-label support
    - Class-wise breakdown
    - Threshold optimization
    - Security-focused metrics (FPR, FNR)
    """
    
    VULNERABILITY_CLASSES = [
        {"id": 0, "name": "sql_injection", "critical": True},
        {"id": 1, "name": "xss", "critical": True},
        {"id": 2, "name": "command_injection", "critical": True},
        {"id": 3, "name": "path_traversal", "critical": True},
        {"id": 4, "name": "code_injection", "critical": True},
        {"id": 5, "name": "ssrf", "critical": False},
        {"id": 6, "name": "xxe", "critical": False},
        {"id": 7, "name": "insecure_deserialization", "critical": True},
        {"id": 8, "name": "hardcoded_credentials", "critical": True},
        {"id": 9, "name": "weak_cryptography", "critical": False},
        {"id": 10, "name": "buffer_overflow", "critical": True},
        {"id": 11, "name": "race_condition", "critical": False},
        {"id": 12, "name": "improper_authentication", "critical": False},
        {"id": 13, "name": "sensitive_data_exposure", "critical": False},
        {"id": 14, "name": "insecure_configuration", "critical": False},
    ]
    
    def __init__(self, num_classes: int = 15):
        self.num_classes = num_classes
    
    def calculate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: Optional[np.ndarray] = None,
        threshold: float = 0.5,
    ) -> SecurityMetrics:
        """
        Calculate metrics for predictions.
        
        Args:
            y_true: Ground truth labels (N,) or (N, num_classes)
            y_pred: Predicted labels (same shape as y_true)
            y_prob: Prediction probabilities (optional)
            threshold: Classification threshold
        
        Returns:
            SecurityMetrics with all computed values
        """
        # Handle multi-label vs binary
        if len(y_true.shape) == 1:
            return self._calculate_binary(y_true, y_pred, threshold)
        else:
            return self._calculate_multilabel(y_true, y_pred, threshold)
    
    def _calculate_binary(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        threshold: float,
    ) -> SecurityMetrics:
        """Calculate binary classification metrics."""
        tp = np.sum((y_pred == 1) & (y_true == 1))
        tn = np.sum((y_pred == 0) & (y_true == 0))
        fp = np.sum((y_pred == 1) & (y_true == 0))
        fn = np.sum((y_pred == 0) & (y_true == 1))
        
        return self._compute_metrics(tp, tn, fp, fn, threshold, len(y_true))
    
    def _calculate_multilabel(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        threshold: float,
    ) -> SecurityMetrics:
        """Calculate multi-label classification metrics."""
        # Aggregate across all classes
        tp = np.sum((y_pred == 1) & (y_true == 1))
        tn = np.sum((y_pred == 0) & (y_true == 0))
        fp = np.sum((y_pred == 1) & (y_true == 0))
        fn = np.sum((y_pred == 0) & (y_true == 1))
        
        # Multi-label specific
        exact_match = np.mean(np.all(y_pred == y_true, axis=1))
        hamming = np.mean(y_pred != y_true)
        
        metrics = self._compute_metrics(
            tp, tn, fp, fn, threshold, y_true.shape[0]
        )
        metrics.exact_match_ratio = exact_match
        metrics.hamming_loss = hamming
        
        return metrics
    
    def _compute_metrics(
        self,
        tp: int,
        tn: int,
        fp: int,
        fn: int,
        threshold: float,
        total_samples: int,
    ) -> SecurityMetrics:
        """Compute all metrics from confusion matrix components."""
        # Avoid division by zero
        eps = 1e-10
        
        precision = tp / (tp + fp + eps)
        recall = tp / (tp + fn + eps)
        f1 = 2 * precision * recall / (precision + recall + eps)
        accuracy = (tp + tn) / (tp + tn + fp + fn + eps)
        
        fpr = fp / (fp + tn + eps)
        fnr = fn / (fn + tp + eps)
        tpr = recall
        tnr = tn / (tn + fp + eps)
        
        # Matthews Correlation Coefficient
        mcc_num = (tp * tn) - (fp * fn)
        mcc_den = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn) + eps)
        mcc = mcc_num / mcc_den
        
        # Balanced accuracy
        balanced_acc = (tpr + tnr) / 2
        
        return SecurityMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1,
            accuracy=accuracy,
            false_positive_rate=fpr,
            false_negative_rate=fnr,
            true_positive_rate=tpr,
            true_negative_rate=tnr,
            true_positives=int(tp),
            true_negatives=int(tn),
            false_positives=int(fp),
            false_negatives=int(fn),
            matthews_correlation=mcc,
            balanced_accuracy=balanced_acc,
            threshold=threshold,
            total_samples=total_samples,
            positive_samples=int(tp + fn),
            negative_samples=int(tn + fp),
        )
    
    def calculate_classwise(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        threshold: float = 0.5,
    ) -> List[ClasswiseMetrics]:
        """
        Calculate metrics for each vulnerability class.
        
        Args:
            y_true: Ground truth (N, num_classes)
            y_pred: Predictions (N, num_classes)
            threshold: Classification threshold
        
        Returns:
            List of ClasswiseMetrics
        """
        classwise = []
        
        for i in range(min(y_true.shape[1], len(self.VULNERABILITY_CLASSES))):
            class_info = self.VULNERABILITY_CLASSES[i]
            
            metrics = self._calculate_binary(
                y_true[:, i],
                y_pred[:, i],
                threshold,
            )
            
            classwise.append(ClasswiseMetrics(
                class_id=class_info["id"],
                class_name=class_info["name"],
                metrics=metrics,
                support=int(np.sum(y_true[:, i])),
                is_critical=class_info["critical"],
            ))
        
        return classwise
    
    def find_optimal_threshold(
        self,
        y_true: np.ndarray,
        y_prob: np.ndarray,
        metric: str = "f1",
        min_recall: float = 0.95,
    ) -> Tuple[float, SecurityMetrics]:
        """
        Find optimal threshold that maximizes metric while maintaining min recall.
        
        Args:
            y_true: Ground truth labels
            y_prob: Prediction probabilities
            metric: Metric to optimize ("f1", "precision", "balanced_accuracy")
            min_recall: Minimum recall constraint
        
        Returns:
            (optimal_threshold, metrics_at_threshold)
        """
        best_threshold = 0.5
        best_score = 0.0
        best_metrics = None
        
        for threshold in np.arange(0.1, 0.9, 0.05):
            y_pred = (y_prob >= threshold).astype(int)
            metrics = self.calculate(y_true, y_pred, threshold=threshold)
            
            # Check recall constraint
            if metrics.recall < min_recall:
                continue
            
            # Get target metric
            if metric == "f1":
                score = metrics.f1_score
            elif metric == "precision":
                score = metrics.precision
            elif metric == "balanced_accuracy":
                score = metrics.balanced_accuracy
            else:
                score = metrics.f1_score
            
            if score > best_score:
                best_score = score
                best_threshold = threshold
                best_metrics = metrics
        
        if best_metrics is None:
            # No threshold met recall constraint, use lowest threshold
            y_pred = (y_prob >= 0.1).astype(int)
            best_metrics = self.calculate(y_true, y_pred, threshold=0.1)
            best_threshold = 0.1
        
        return best_threshold, best_metrics


# =============================================================================
# CONFUSION MATRIX ANALYZER
# =============================================================================

class ConfusionMatrixAnalyzer:
    """
    Deep analysis of confusion matrix for security insights.
    
    Provides:
    - Error pattern analysis
    - Class confusion identification
    - Critical miss detection
    """
    
    def __init__(self, class_names: List[str]):
        self.class_names = class_names
        self.num_classes = len(class_names)
    
    def build_matrix(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> np.ndarray:
        """Build confusion matrix."""
        matrix = np.zeros((self.num_classes, self.num_classes), dtype=int)
        
        for true_label, pred_label in zip(y_true, y_pred):
            if isinstance(true_label, np.ndarray):
                # Multi-label: count co-occurrences
                true_classes = np.where(true_label == 1)[0]
                pred_classes = np.where(pred_label == 1)[0]
                
                for tc in true_classes:
                    for pc in pred_classes:
                        matrix[tc, pc] += 1
            else:
                matrix[true_label, pred_label] += 1
        
        return matrix
    
    def analyze_errors(
        self,
        confusion_matrix: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Analyze error patterns in confusion matrix.
        
        Returns:
            Analysis with most confused pairs, critical misses, etc.
        """
        analysis = {
            "most_confused_pairs": [],
            "critical_misses": [],
            "high_fp_classes": [],
            "per_class_accuracy": [],
        }
        
        # Find most confused pairs (off-diagonal)
        for i in range(self.num_classes):
            for j in range(self.num_classes):
                if i != j and confusion_matrix[i, j] > 0:
                    analysis["most_confused_pairs"].append({
                        "true_class": self.class_names[i],
                        "predicted_class": self.class_names[j],
                        "count": int(confusion_matrix[i, j]),
                    })
        
        # Sort by count
        analysis["most_confused_pairs"].sort(
            key=lambda x: x["count"], 
            reverse=True
        )
        analysis["most_confused_pairs"] = analysis["most_confused_pairs"][:10]
        
        # Per-class accuracy
        for i in range(self.num_classes):
            row_sum = confusion_matrix[i, :].sum()
            if row_sum > 0:
                accuracy = confusion_matrix[i, i] / row_sum
            else:
                accuracy = 0.0
            
            analysis["per_class_accuracy"].append({
                "class": self.class_names[i],
                "accuracy": round(accuracy, 4),
                "support": int(row_sum),
            })
        
        return analysis


# =============================================================================
# FALSE POSITIVE TRACKER
# =============================================================================

class FalsePositiveTracker:
    """
    Track and analyze false positives for continuous improvement.
    
    Critical for security: High FPR leads to alert fatigue.
    """
    
    def __init__(self, log_dir: str = "./fp_logs"):
        self.log_dir = log_dir
        self.fp_records: List[Dict[str, Any]] = []
        self.fp_by_class: Dict[str, List[Dict]] = defaultdict(list)
    
    def log_false_positive(
        self,
        sample_id: str,
        code: str,
        predicted_class: str,
        confidence: float,
        model_version: str,
        context: Optional[Dict] = None,
    ):
        """Log a false positive for analysis."""
        record = {
            "sample_id": sample_id,
            "code_snippet": code[:500],  # Truncate
            "predicted_class": predicted_class,
            "confidence": confidence,
            "model_version": model_version,
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
        }
        
        self.fp_records.append(record)
        self.fp_by_class[predicted_class].append(record)
        
        logger.debug(f"Logged FP: {predicted_class} (conf: {confidence:.2f})")
    
    def analyze_fp_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in false positives."""
        if not self.fp_records:
            return {"total_fps": 0, "patterns": []}
        
        analysis = {
            "total_fps": len(self.fp_records),
            "by_class": {},
            "high_confidence_fps": [],
            "common_patterns": [],
        }
        
        # By class breakdown
        for class_name, records in self.fp_by_class.items():
            avg_conf = np.mean([r["confidence"] for r in records])
            analysis["by_class"][class_name] = {
                "count": len(records),
                "avg_confidence": round(avg_conf, 4),
            }
        
        # High confidence FPs (most problematic)
        high_conf_fps = [
            r for r in self.fp_records 
            if r["confidence"] >= 0.8
        ]
        analysis["high_confidence_fps"] = len(high_conf_fps)
        
        return analysis
    
    def export_for_retraining(self, output_path: str) -> int:
        """Export FP records for retraining dataset."""
        export_data = []
        
        for record in self.fp_records:
            export_data.append({
                "code": record["code_snippet"],
                "false_positive_class": record["predicted_class"],
                "true_label": "benign",  # By definition, FP means it's safe
                "confidence": record["confidence"],
                "source": "fp_analysis",
            })
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported {len(export_data)} FP records to {output_path}")
        return len(export_data)
    
    def get_fp_rate_trend(
        self,
        window_size: int = 100,
    ) -> List[float]:
        """Get FP rate trend over time (rolling window)."""
        if len(self.fp_records) < window_size:
            return []
        
        # This would need total predictions to calculate rate
        # For now, return counts per window
        rates = []
        for i in range(0, len(self.fp_records) - window_size + 1, window_size // 2):
            window = self.fp_records[i:i + window_size]
            rates.append(len(window))
        
        return rates
