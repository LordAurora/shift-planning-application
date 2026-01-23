"""
Dataset Splitting Strategies

Proper dataset splitting for security vulnerability detection:
- Stratified splits (maintain class distribution)
- Temporal splits (simulate real-world deployment)
- Cross-validation for robust evaluation
"""

import numpy as np
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, Iterator
from enum import Enum
from collections import Counter
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# SPLIT STRATEGY ENUM
# =============================================================================

class SplitStrategy(Enum):
    """Dataset splitting strategies."""
    RANDOM = "random"           # Simple random split
    STRATIFIED = "stratified"   # Maintain class distribution
    TEMPORAL = "temporal"       # Time-based split
    GROUPED = "grouped"         # Keep related samples together
    ADVERSARIAL = "adversarial" # Harder test set


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class DataSplit:
    """Container for a dataset split."""
    train_indices: np.ndarray
    val_indices: np.ndarray
    test_indices: np.ndarray
    
    # Metadata
    train_size: int = 0
    val_size: int = 0
    test_size: int = 0
    strategy: str = ""
    
    def __post_init__(self):
        self.train_size = len(self.train_indices)
        self.val_size = len(self.val_indices)
        self.test_size = len(self.test_indices)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "train_size": self.train_size,
            "val_size": self.val_size,
            "test_size": self.test_size,
            "strategy": self.strategy,
            "total_size": self.train_size + self.val_size + self.test_size,
        }


@dataclass
class CrossValFold:
    """Container for a cross-validation fold."""
    fold_id: int
    train_indices: np.ndarray
    val_indices: np.ndarray


# =============================================================================
# BASE SPLITTER
# =============================================================================

class DataSplitter:
    """
    Base class for dataset splitting.
    
    Default: 70% train, 15% validation, 15% test
    """
    
    def __init__(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_seed: int = 42,
    ):
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6
        
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.random_seed = random_seed
        
        np.random.seed(random_seed)
    
    def split(
        self,
        n_samples: int,
        labels: Optional[np.ndarray] = None,
    ) -> DataSplit:
        """
        Split dataset into train/val/test.
        
        Args:
            n_samples: Total number of samples
            labels: Optional labels for stratification
        
        Returns:
            DataSplit with indices
        """
        indices = np.arange(n_samples)
        np.random.shuffle(indices)
        
        train_end = int(n_samples * self.train_ratio)
        val_end = train_end + int(n_samples * self.val_ratio)
        
        return DataSplit(
            train_indices=indices[:train_end],
            val_indices=indices[train_end:val_end],
            test_indices=indices[val_end:],
            strategy="random",
        )


# =============================================================================
# STRATIFIED SPLITTER
# =============================================================================

class StratifiedSplitter(DataSplitter):
    """
    Stratified splitting to maintain class distribution.
    
    CRITICAL for imbalanced security datasets where some
    vulnerability types are rare.
    
    Approach:
    1. Group samples by label
    2. Split each group proportionally
    3. Combine splits
    """
    
    def split(
        self,
        n_samples: int,
        labels: np.ndarray,
    ) -> DataSplit:
        """
        Stratified split maintaining class distribution.
        
        Args:
            n_samples: Total number of samples
            labels: Labels array (N,) for single-label or (N, C) for multi-label
        
        Returns:
            DataSplit with stratified indices
        """
        if len(labels.shape) == 1:
            return self._split_single_label(n_samples, labels)
        else:
            return self._split_multi_label(n_samples, labels)
    
    def _split_single_label(
        self,
        n_samples: int,
        labels: np.ndarray,
    ) -> DataSplit:
        """Stratified split for single-label classification."""
        train_indices = []
        val_indices = []
        test_indices = []
        
        unique_labels = np.unique(labels)
        
        for label in unique_labels:
            label_indices = np.where(labels == label)[0]
            np.random.shuffle(label_indices)
            
            n_label = len(label_indices)
            train_end = int(n_label * self.train_ratio)
            val_end = train_end + int(n_label * self.val_ratio)
            
            train_indices.extend(label_indices[:train_end])
            val_indices.extend(label_indices[train_end:val_end])
            test_indices.extend(label_indices[val_end:])
        
        # Shuffle within each split
        np.random.shuffle(train_indices)
        np.random.shuffle(val_indices)
        np.random.shuffle(test_indices)
        
        return DataSplit(
            train_indices=np.array(train_indices),
            val_indices=np.array(val_indices),
            test_indices=np.array(test_indices),
            strategy="stratified_single_label",
        )
    
    def _split_multi_label(
        self,
        n_samples: int,
        labels: np.ndarray,
    ) -> DataSplit:
        """
        Stratified split for multi-label classification.
        
        Uses iterative stratification to maintain label distribution.
        """
        # Create label combination strings for grouping
        label_combos = [''.join(map(str, row)) for row in labels]
        
        train_indices = []
        val_indices = []
        test_indices = []
        
        # Group by unique label combinations
        combo_to_indices = {}
        for i, combo in enumerate(label_combos):
            if combo not in combo_to_indices:
                combo_to_indices[combo] = []
            combo_to_indices[combo].append(i)
        
        # Split each group
        for combo, indices in combo_to_indices.items():
            indices = np.array(indices)
            np.random.shuffle(indices)
            
            n = len(indices)
            train_end = max(1, int(n * self.train_ratio))
            val_end = train_end + max(1, int(n * self.val_ratio))
            
            train_indices.extend(indices[:train_end])
            val_indices.extend(indices[train_end:val_end])
            test_indices.extend(indices[val_end:])
        
        np.random.shuffle(train_indices)
        np.random.shuffle(val_indices)
        np.random.shuffle(test_indices)
        
        return DataSplit(
            train_indices=np.array(train_indices),
            val_indices=np.array(val_indices),
            test_indices=np.array(test_indices),
            strategy="stratified_multi_label",
        )
    
    def verify_stratification(
        self,
        labels: np.ndarray,
        split: DataSplit,
    ) -> Dict[str, Any]:
        """Verify that stratification was successful."""
        if len(labels.shape) == 1:
            # Single label
            train_dist = Counter(labels[split.train_indices])
            val_dist = Counter(labels[split.val_indices])
            test_dist = Counter(labels[split.test_indices])
            full_dist = Counter(labels)
        else:
            # Multi-label: check per-class distribution
            train_dist = {i: labels[split.train_indices, i].sum() 
                         for i in range(labels.shape[1])}
            val_dist = {i: labels[split.val_indices, i].sum() 
                       for i in range(labels.shape[1])}
            test_dist = {i: labels[split.test_indices, i].sum() 
                        for i in range(labels.shape[1])}
            full_dist = {i: labels[:, i].sum() 
                        for i in range(labels.shape[1])}
        
        return {
            "full_distribution": dict(full_dist),
            "train_distribution": dict(train_dist),
            "val_distribution": dict(val_dist),
            "test_distribution": dict(test_dist),
        }


# =============================================================================
# TEMPORAL SPLITTER
# =============================================================================

class TemporalSplitter(DataSplitter):
    """
    Temporal splitting for time-series data.
    
    CRITICAL for security: Models should be evaluated on
    future vulnerabilities, not randomly sampled ones.
    
    Approach:
    - Train on older data
    - Validate on recent data
    - Test on most recent data
    """
    
    def split(
        self,
        n_samples: int,
        timestamps: np.ndarray,
        labels: Optional[np.ndarray] = None,
    ) -> DataSplit:
        """
        Temporal split based on timestamps.
        
        Args:
            n_samples: Total number of samples
            timestamps: Timestamp for each sample
            labels: Optional labels (not used for splitting)
        
        Returns:
            DataSplit with temporal ordering
        """
        # Sort by timestamp
        sorted_indices = np.argsort(timestamps)
        
        train_end = int(n_samples * self.train_ratio)
        val_end = train_end + int(n_samples * self.val_ratio)
        
        return DataSplit(
            train_indices=sorted_indices[:train_end],
            val_indices=sorted_indices[train_end:val_end],
            test_indices=sorted_indices[val_end:],
            strategy="temporal",
        )
    
    def get_temporal_stats(
        self,
        timestamps: np.ndarray,
        split: DataSplit,
    ) -> Dict[str, Any]:
        """Get temporal statistics for the split."""
        train_ts = timestamps[split.train_indices]
        val_ts = timestamps[split.val_indices]
        test_ts = timestamps[split.test_indices]
        
        return {
            "train": {
                "start": str(np.min(train_ts)),
                "end": str(np.max(train_ts)),
                "count": len(train_ts),
            },
            "val": {
                "start": str(np.min(val_ts)),
                "end": str(np.max(val_ts)),
                "count": len(val_ts),
            },
            "test": {
                "start": str(np.min(test_ts)),
                "end": str(np.max(test_ts)),
                "count": len(test_ts),
            },
        }


# =============================================================================
# CROSS VALIDATOR
# =============================================================================

class CrossValidator:
    """
    K-Fold cross-validation for robust evaluation.
    
    Supports:
    - Standard K-Fold
    - Stratified K-Fold
    - Time-series K-Fold (no future data leakage)
    """
    
    def __init__(
        self,
        n_folds: int = 5,
        stratified: bool = True,
        random_seed: int = 42,
    ):
        self.n_folds = n_folds
        self.stratified = stratified
        self.random_seed = random_seed
        
        np.random.seed(random_seed)
    
    def split(
        self,
        n_samples: int,
        labels: Optional[np.ndarray] = None,
    ) -> Iterator[CrossValFold]:
        """
        Generate cross-validation folds.
        
        Args:
            n_samples: Total number of samples
            labels: Labels for stratification
        
        Yields:
            CrossValFold for each fold
        """
        indices = np.arange(n_samples)
        
        if self.stratified and labels is not None:
            yield from self._stratified_split(indices, labels)
        else:
            yield from self._standard_split(indices)
    
    def _standard_split(
        self,
        indices: np.ndarray,
    ) -> Iterator[CrossValFold]:
        """Standard K-Fold split."""
        np.random.shuffle(indices)
        fold_size = len(indices) // self.n_folds
        
        for i in range(self.n_folds):
            start = i * fold_size
            end = start + fold_size if i < self.n_folds - 1 else len(indices)
            
            val_indices = indices[start:end]
            train_indices = np.concatenate([
                indices[:start],
                indices[end:],
            ])
            
            yield CrossValFold(
                fold_id=i,
                train_indices=train_indices,
                val_indices=val_indices,
            )
    
    def _stratified_split(
        self,
        indices: np.ndarray,
        labels: np.ndarray,
    ) -> Iterator[CrossValFold]:
        """Stratified K-Fold split."""
        if len(labels.shape) > 1:
            # Multi-label: use label combination
            label_keys = [''.join(map(str, row)) for row in labels]
        else:
            label_keys = labels.tolist()
        
        # Group indices by label
        label_to_indices = {}
        for idx, label_key in zip(indices, label_keys):
            if label_key not in label_to_indices:
                label_to_indices[label_key] = []
            label_to_indices[label_key].append(idx)
        
        # Shuffle within groups
        for key in label_to_indices:
            np.random.shuffle(label_to_indices[key])
        
        # Generate folds
        for fold_id in range(self.n_folds):
            train_indices = []
            val_indices = []
            
            for key, group_indices in label_to_indices.items():
                n = len(group_indices)
                fold_size = max(1, n // self.n_folds)
                start = fold_id * fold_size
                end = start + fold_size if fold_id < self.n_folds - 1 else n
                
                val_indices.extend(group_indices[start:end])
                train_indices.extend(group_indices[:start] + group_indices[end:])
            
            np.random.shuffle(train_indices)
            np.random.shuffle(val_indices)
            
            yield CrossValFold(
                fold_id=fold_id,
                train_indices=np.array(train_indices),
                val_indices=np.array(val_indices),
            )
    
    def get_fold_statistics(
        self,
        labels: np.ndarray,
    ) -> List[Dict[str, Any]]:
        """Get statistics for each fold."""
        stats = []
        
        for fold in self.split(len(labels), labels):
            if len(labels.shape) == 1:
                train_dist = Counter(labels[fold.train_indices])
                val_dist = Counter(labels[fold.val_indices])
            else:
                train_dist = {
                    i: labels[fold.train_indices, i].sum()
                    for i in range(labels.shape[1])
                }
                val_dist = {
                    i: labels[fold.val_indices, i].sum()
                    for i in range(labels.shape[1])
                }
            
            stats.append({
                "fold_id": fold.fold_id,
                "train_size": len(fold.train_indices),
                "val_size": len(fold.val_indices),
                "train_distribution": dict(train_dist),
                "val_distribution": dict(val_dist),
            })
        
        return stats
