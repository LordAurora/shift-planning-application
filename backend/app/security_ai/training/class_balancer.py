"""
Class Imbalance Handling

Strategies for handling class imbalance in security datasets:
- Some vulnerability types are rare (e.g., buffer overflow)
- Clean code samples often outnumber vulnerable samples
- Critical vulnerabilities must not be under-represented

Techniques:
1. Oversampling (SMOTE)
2. Undersampling
3. Class weights
4. Focal Loss
5. Threshold optimization
"""

import numpy as np
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from collections import Counter

logger = logging.getLogger(__name__)


# =============================================================================
# STRATEGY ENUM
# =============================================================================

class BalancingStrategy(Enum):
    """Class balancing strategies."""
    NONE = "none"                    # No balancing
    OVERSAMPLE = "oversample"        # Duplicate minority samples
    UNDERSAMPLE = "undersample"      # Remove majority samples
    SMOTE = "smote"                  # Synthetic minority oversampling
    CLASS_WEIGHT = "class_weight"    # Weight loss by class frequency
    FOCAL_LOSS = "focal_loss"        # Focus on hard examples
    COMBINED = "combined"            # Combination of techniques


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class BalanceReport:
    """Report on class balance."""
    original_distribution: Dict[int, int]
    balanced_distribution: Dict[int, int]
    imbalance_ratio: float  # Max/min class size
    strategy_used: str
    samples_added: int = 0
    samples_removed: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_distribution": self.original_distribution,
            "balanced_distribution": self.balanced_distribution,
            "imbalance_ratio": round(self.imbalance_ratio, 2),
            "strategy": self.strategy_used,
            "samples_added": self.samples_added,
            "samples_removed": self.samples_removed,
        }


# =============================================================================
# CLASS BALANCER
# =============================================================================

class ClassBalancer:
    """
    Base class balancer using oversampling/undersampling.
    
    Strategy:
    - For security, prefer oversampling to avoid losing rare vulnerabilities
    - Target ratio (max_class / min_class) configurable
    """
    
    def __init__(
        self,
        strategy: BalancingStrategy = BalancingStrategy.OVERSAMPLE,
        target_ratio: float = 3.0,  # Max imbalance ratio
        random_seed: int = 42,
    ):
        self.strategy = strategy
        self.target_ratio = target_ratio
        self.random_seed = random_seed
        
        np.random.seed(random_seed)
    
    def balance(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, BalanceReport]:
        """
        Balance dataset.
        
        Args:
            X: Features (N, ...)
            y: Labels (N,) or (N, C)
        
        Returns:
            (balanced_X, balanced_y, report)
        """
        original_dist = self._get_distribution(y)
        original_ratio = max(original_dist.values()) / max(min(original_dist.values()), 1)
        
        if self.strategy == BalancingStrategy.NONE:
            return X, y, BalanceReport(
                original_distribution=original_dist,
                balanced_distribution=original_dist,
                imbalance_ratio=original_ratio,
                strategy_used="none",
            )
        
        if self.strategy == BalancingStrategy.OVERSAMPLE:
            X_bal, y_bal = self._oversample(X, y)
        elif self.strategy == BalancingStrategy.UNDERSAMPLE:
            X_bal, y_bal = self._undersample(X, y)
        else:
            X_bal, y_bal = self._oversample(X, y)
        
        balanced_dist = self._get_distribution(y_bal)
        balanced_ratio = max(balanced_dist.values()) / max(min(balanced_dist.values()), 1)
        
        return X_bal, y_bal, BalanceReport(
            original_distribution=original_dist,
            balanced_distribution=balanced_dist,
            imbalance_ratio=balanced_ratio,
            strategy_used=self.strategy.value,
            samples_added=len(y_bal) - len(y) if len(y_bal) > len(y) else 0,
            samples_removed=len(y) - len(y_bal) if len(y_bal) < len(y) else 0,
        )
    
    def _get_distribution(self, y: np.ndarray) -> Dict[int, int]:
        """Get class distribution."""
        if len(y.shape) == 1:
            return dict(Counter(y))
        else:
            # Multi-label: sum per class
            return {i: int(y[:, i].sum()) for i in range(y.shape[1])}
    
    def _oversample(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Oversample minority classes."""
        if len(y.shape) == 1:
            return self._oversample_single_label(X, y)
        else:
            return self._oversample_multi_label(X, y)
    
    def _oversample_single_label(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Oversample for single-label classification."""
        class_counts = Counter(y)
        max_count = max(class_counts.values())
        target_count = int(max_count / self.target_ratio)
        
        X_list = [X]
        y_list = [y]
        
        for class_label, count in class_counts.items():
            if count < target_count:
                # Oversample this class
                class_indices = np.where(y == class_label)[0]
                n_to_add = target_count - count
                
                # Random sampling with replacement
                new_indices = np.random.choice(
                    class_indices, 
                    size=n_to_add, 
                    replace=True
                )
                
                X_list.append(X[new_indices])
                y_list.append(y[new_indices])
        
        return np.concatenate(X_list), np.concatenate(y_list)
    
    def _oversample_multi_label(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Oversample for multi-label classification."""
        # Find samples with rare labels
        class_counts = y.sum(axis=0)
        max_count = class_counts.max()
        target_count = int(max_count / self.target_ratio)
        
        X_list = [X]
        y_list = [y]
        
        for class_idx in range(y.shape[1]):
            count = int(class_counts[class_idx])
            if count < target_count and count > 0:
                # Find samples with this class
                class_indices = np.where(y[:, class_idx] == 1)[0]
                n_to_add = target_count - count
                
                new_indices = np.random.choice(
                    class_indices,
                    size=min(n_to_add, len(class_indices) * 5),  # Cap at 5x
                    replace=True
                )
                
                X_list.append(X[new_indices])
                y_list.append(y[new_indices])
        
        return np.concatenate(X_list), np.concatenate(y_list)
    
    def _undersample(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Undersample majority classes."""
        if len(y.shape) == 1:
            class_counts = Counter(y)
            min_count = min(class_counts.values())
            target_count = int(min_count * self.target_ratio)
            
            indices = []
            for class_label, count in class_counts.items():
                class_indices = np.where(y == class_label)[0]
                if count > target_count:
                    selected = np.random.choice(
                        class_indices,
                        size=target_count,
                        replace=False
                    )
                else:
                    selected = class_indices
                indices.extend(selected)
            
            indices = np.array(indices)
            np.random.shuffle(indices)
            
            return X[indices], y[indices]
        else:
            # Multi-label: can't simply undersample
            # Return original for now
            logger.warning("Undersampling not supported for multi-label")
            return X, y
    
    def compute_class_weights(
        self,
        y: np.ndarray,
        weight_type: str = "balanced",
    ) -> np.ndarray:
        """
        Compute class weights for loss weighting.
        
        Args:
            y: Labels
            weight_type: "balanced" or "sqrt_balanced"
        
        Returns:
            Array of class weights
        """
        if len(y.shape) == 1:
            class_counts = np.bincount(y)
        else:
            class_counts = y.sum(axis=0)
        
        n_samples = len(y)
        n_classes = len(class_counts)
        
        if weight_type == "balanced":
            # Inverse frequency
            weights = n_samples / (n_classes * class_counts + 1e-6)
        elif weight_type == "sqrt_balanced":
            # Sqrt of inverse frequency (less aggressive)
            weights = np.sqrt(n_samples / (n_classes * class_counts + 1e-6))
        else:
            weights = np.ones(n_classes)
        
        # Normalize
        weights = weights / weights.sum() * n_classes
        
        return weights


# =============================================================================
# SMOTE BALANCER
# =============================================================================

class SMOTEBalancer:
    """
    Synthetic Minority Over-sampling Technique.
    
    Creates synthetic samples by interpolating between
    existing minority class samples.
    
    Better than simple oversampling for avoiding overfitting.
    """
    
    def __init__(
        self,
        k_neighbors: int = 5,
        target_ratio: float = 1.0,
        random_seed: int = 42,
    ):
        self.k_neighbors = k_neighbors
        self.target_ratio = target_ratio
        self.random_seed = random_seed
        
        np.random.seed(random_seed)
    
    def balance(
        self,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, BalanceReport]:
        """
        Apply SMOTE balancing.
        
        Args:
            X: Features (N, D)
            y: Labels (N,)
        
        Returns:
            (balanced_X, balanced_y, report)
        """
        if len(y.shape) > 1:
            logger.warning("SMOTE not implemented for multi-label, using simple oversample")
            balancer = ClassBalancer(BalancingStrategy.OVERSAMPLE)
            return balancer.balance(X, y)
        
        original_dist = dict(Counter(y))
        max_count = max(original_dist.values())
        
        X_list = [X]
        y_list = [y]
        
        for class_label, count in original_dist.items():
            target = int(max_count * self.target_ratio)
            if count < target:
                n_synthetic = target - count
                synthetic_X = self._generate_synthetic(
                    X[y == class_label],
                    n_synthetic
                )
                synthetic_y = np.full(n_synthetic, class_label)
                
                X_list.append(synthetic_X)
                y_list.append(synthetic_y)
        
        X_bal = np.concatenate(X_list)
        y_bal = np.concatenate(y_list)
        
        balanced_dist = dict(Counter(y_bal))
        
        return X_bal, y_bal, BalanceReport(
            original_distribution=original_dist,
            balanced_distribution=balanced_dist,
            imbalance_ratio=max(balanced_dist.values()) / min(balanced_dist.values()),
            strategy_used="smote",
            samples_added=len(y_bal) - len(y),
        )
    
    def _generate_synthetic(
        self,
        X_minority: np.ndarray,
        n_synthetic: int,
    ) -> np.ndarray:
        """Generate synthetic samples using SMOTE."""
        n_samples = len(X_minority)
        
        if n_samples < 2:
            # Can't do SMOTE with < 2 samples
            return np.tile(X_minority, (n_synthetic, 1))[:n_synthetic]
        
        k = min(self.k_neighbors, n_samples - 1)
        synthetic = []
        
        for _ in range(n_synthetic):
            # Pick a random sample
            idx = np.random.randint(0, n_samples)
            sample = X_minority[idx]
            
            # Find k nearest neighbors (simple Euclidean distance)
            distances = np.linalg.norm(X_minority - sample, axis=1)
            distances[idx] = np.inf  # Exclude self
            neighbor_indices = np.argsort(distances)[:k]
            
            # Pick a random neighbor
            neighbor_idx = np.random.choice(neighbor_indices)
            neighbor = X_minority[neighbor_idx]
            
            # Interpolate
            alpha = np.random.random()
            new_sample = sample + alpha * (neighbor - sample)
            synthetic.append(new_sample)
        
        return np.array(synthetic)


# =============================================================================
# FOCAL LOSS WEIGHTER
# =============================================================================

class FocalLossWeighter:
    """
    Focal Loss for handling class imbalance.
    
    FL(p) = -α(1-p)^γ * log(p)
    
    - α: Class weight (for imbalance)
    - γ: Focusing parameter (down-weight easy examples)
    
    Good for security: Focuses on hard-to-classify edge cases.
    """
    
    def __init__(
        self,
        gamma: float = 2.0,
        alpha: Optional[np.ndarray] = None,
    ):
        """
        Args:
            gamma: Focusing parameter (higher = more focus on hard examples)
            alpha: Class weights (optional)
        """
        self.gamma = gamma
        self.alpha = alpha
    
    def compute_weights(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> np.ndarray:
        """
        Compute focal loss weights for each sample.
        
        Args:
            y_true: Ground truth (N,) or (N, C)
            y_pred: Predicted probabilities (N,) or (N, C)
        
        Returns:
            Weight for each sample
        """
        # Clip predictions to avoid log(0)
        y_pred = np.clip(y_pred, 1e-7, 1 - 1e-7)
        
        if len(y_true.shape) == 1:
            # Binary classification
            pt = np.where(y_true == 1, y_pred, 1 - y_pred)
            focal_weight = (1 - pt) ** self.gamma
            
            if self.alpha is not None:
                alpha_t = np.where(y_true == 1, self.alpha[1], self.alpha[0])
                focal_weight = alpha_t * focal_weight
        else:
            # Multi-label
            pt = y_true * y_pred + (1 - y_true) * (1 - y_pred)
            focal_weight = (1 - pt) ** self.gamma
            
            if self.alpha is not None:
                alpha_t = y_true * self.alpha + (1 - y_true) * (1 - self.alpha)
                focal_weight = alpha_t * focal_weight
            
            # Average across classes
            focal_weight = focal_weight.mean(axis=1)
        
        return focal_weight
    
    def get_loss_function(self):
        """
        Get focal loss function for TensorFlow.
        
        Returns:
            Loss function compatible with TensorFlow
        """
        gamma = self.gamma
        alpha = self.alpha
        
        def focal_loss(y_true, y_pred):
            import tensorflow as tf
            
            y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)
            
            # Cross entropy
            ce = -y_true * tf.math.log(y_pred) - (1 - y_true) * tf.math.log(1 - y_pred)
            
            # Focal weight
            pt = y_true * y_pred + (1 - y_true) * (1 - y_pred)
            focal_weight = tf.pow(1 - pt, gamma)
            
            # Apply alpha if provided
            if alpha is not None:
                alpha_t = y_true * alpha + (1 - y_true) * (1 - alpha)
                focal_weight = alpha_t * focal_weight
            
            return tf.reduce_mean(focal_weight * ce)
        
        return focal_loss


# =============================================================================
# THRESHOLD OPTIMIZER
# =============================================================================

class ThresholdOptimizer:
    """
    Per-class threshold optimization for imbalanced multi-label.
    
    Instead of using 0.5 for all classes, optimize threshold
    per class to maximize F1 or achieve target recall.
    """
    
    def __init__(
        self,
        metric: str = "f1",
        min_recall: float = 0.95,
    ):
        """
        Args:
            metric: Metric to optimize ("f1", "precision", "recall")
            min_recall: Minimum recall constraint for security
        """
        self.metric = metric
        self.min_recall = min_recall
        self.thresholds: Optional[np.ndarray] = None
    
    def optimize(
        self,
        y_true: np.ndarray,
        y_prob: np.ndarray,
    ) -> np.ndarray:
        """
        Find optimal threshold for each class.
        
        Args:
            y_true: Ground truth (N, C)
            y_prob: Predicted probabilities (N, C)
        
        Returns:
            Optimal threshold for each class
        """
        n_classes = y_true.shape[1]
        optimal_thresholds = np.ones(n_classes) * 0.5
        
        for c in range(n_classes):
            best_threshold = 0.5
            best_score = 0.0
            
            for threshold in np.arange(0.1, 0.9, 0.05):
                y_pred_c = (y_prob[:, c] >= threshold).astype(int)
                
                # Calculate metrics
                tp = np.sum((y_pred_c == 1) & (y_true[:, c] == 1))
                fp = np.sum((y_pred_c == 1) & (y_true[:, c] == 0))
                fn = np.sum((y_pred_c == 0) & (y_true[:, c] == 1))
                
                precision = tp / (tp + fp + 1e-10)
                recall = tp / (tp + fn + 1e-10)
                f1 = 2 * precision * recall / (precision + recall + 1e-10)
                
                # Check recall constraint
                if recall < self.min_recall:
                    continue
                
                # Get target metric
                if self.metric == "f1":
                    score = f1
                elif self.metric == "precision":
                    score = precision
                else:
                    score = recall
                
                if score > best_score:
                    best_score = score
                    best_threshold = threshold
            
            optimal_thresholds[c] = best_threshold
        
        self.thresholds = optimal_thresholds
        return optimal_thresholds
    
    def apply_thresholds(
        self,
        y_prob: np.ndarray,
        thresholds: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Apply per-class thresholds to predictions.
        
        Args:
            y_prob: Predicted probabilities (N, C)
            thresholds: Optional custom thresholds
        
        Returns:
            Binary predictions
        """
        if thresholds is None:
            thresholds = self.thresholds
        
        if thresholds is None:
            raise ValueError("No thresholds available. Call optimize() first.")
        
        return (y_prob >= thresholds).astype(int)
    
    def get_threshold_report(self) -> Dict[str, Any]:
        """Get report on optimized thresholds."""
        if self.thresholds is None:
            return {"status": "not_optimized"}
        
        return {
            "thresholds": self.thresholds.tolist(),
            "mean_threshold": float(np.mean(self.thresholds)),
            "std_threshold": float(np.std(self.thresholds)),
            "min_threshold": float(np.min(self.thresholds)),
            "max_threshold": float(np.max(self.thresholds)),
        }
