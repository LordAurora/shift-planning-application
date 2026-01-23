"""
Training Loop Implementation

Complete training workflow with:
- Configurable training parameters
- Early stopping
- Learning rate scheduling
- Checkpointing
- Metrics logging
"""

import numpy as np
import logging
import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class TrainingConfig:
    """
    Training configuration.
    
    Security-focused defaults:
    - Longer training for better recall
    - Conservative learning rate
    - Class weights enabled
    """
    # Basic parameters
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 1e-4
    
    # Optimizer
    optimizer: str = "adam"  # adam, sgd, adamw
    weight_decay: float = 1e-5
    
    # Learning rate schedule
    lr_schedule: str = "cosine"  # constant, cosine, step, warmup_cosine
    warmup_epochs: int = 5
    lr_decay_factor: float = 0.1
    lr_decay_epochs: List[int] = field(default_factory=lambda: [30, 60, 90])
    
    # Early stopping
    early_stopping: bool = True
    patience: int = 10
    min_delta: float = 1e-4
    monitor_metric: str = "val_recall"  # Recall is critical for security
    
    # Regularization
    dropout: float = 0.1
    label_smoothing: float = 0.1
    
    # Class balancing
    use_class_weights: bool = True
    use_focal_loss: bool = False
    focal_gamma: float = 2.0
    
    # Checkpointing
    checkpoint_dir: str = "./checkpoints"
    save_best_only: bool = True
    save_frequency: int = 5  # Save every N epochs
    
    # Logging
    log_dir: str = "./logs"
    log_frequency: int = 10  # Log every N batches
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "optimizer": self.optimizer,
            "lr_schedule": self.lr_schedule,
            "early_stopping": self.early_stopping,
            "patience": self.patience,
            "monitor_metric": self.monitor_metric,
            "use_class_weights": self.use_class_weights,
            "use_focal_loss": self.use_focal_loss,
        }


# =============================================================================
# EARLY STOPPING
# =============================================================================

class EarlyStopping:
    """
    Early stopping with patience.
    
    Monitors a metric and stops training if no improvement
    for `patience` epochs.
    """
    
    def __init__(
        self,
        patience: int = 10,
        min_delta: float = 1e-4,
        mode: str = "max",  # "min" for loss, "max" for accuracy/recall
        restore_best_weights: bool = True,
    ):
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.restore_best_weights = restore_best_weights
        
        self.best_value = None
        self.best_epoch = 0
        self.wait = 0
        self.stopped_epoch = 0
        self.best_weights = None
    
    def __call__(
        self,
        current_value: float,
        current_epoch: int,
        model_weights: Any = None,
    ) -> bool:
        """
        Check if training should stop.
        
        Args:
            current_value: Current metric value
            current_epoch: Current epoch number
            model_weights: Optional model weights to save
        
        Returns:
            True if training should stop
        """
        if self.best_value is None:
            self.best_value = current_value
            self.best_epoch = current_epoch
            if model_weights is not None:
                self.best_weights = model_weights
            return False
        
        if self.mode == "max":
            improved = current_value > self.best_value + self.min_delta
        else:
            improved = current_value < self.best_value - self.min_delta
        
        if improved:
            self.best_value = current_value
            self.best_epoch = current_epoch
            self.wait = 0
            if model_weights is not None:
                self.best_weights = model_weights
        else:
            self.wait += 1
            if self.wait >= self.patience:
                self.stopped_epoch = current_epoch
                return True
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "best_value": self.best_value,
            "best_epoch": self.best_epoch,
            "wait": self.wait,
            "patience": self.patience,
            "stopped_epoch": self.stopped_epoch,
        }


# =============================================================================
# LEARNING RATE SCHEDULER
# =============================================================================

class LearningRateScheduler:
    """
    Learning rate scheduling strategies.
    
    Supports:
    - Constant
    - Step decay
    - Cosine annealing
    - Warmup + cosine
    """
    
    def __init__(
        self,
        initial_lr: float,
        schedule_type: str = "cosine",
        total_epochs: int = 100,
        warmup_epochs: int = 5,
        decay_factor: float = 0.1,
        decay_epochs: Optional[List[int]] = None,
    ):
        self.initial_lr = initial_lr
        self.schedule_type = schedule_type
        self.total_epochs = total_epochs
        self.warmup_epochs = warmup_epochs
        self.decay_factor = decay_factor
        self.decay_epochs = decay_epochs or [30, 60, 90]
        
        self.current_lr = initial_lr
    
    def get_lr(self, epoch: int) -> float:
        """Get learning rate for given epoch."""
        if self.schedule_type == "constant":
            return self.initial_lr
        
        elif self.schedule_type == "step":
            lr = self.initial_lr
            for decay_epoch in self.decay_epochs:
                if epoch >= decay_epoch:
                    lr *= self.decay_factor
            return lr
        
        elif self.schedule_type == "cosine":
            return self._cosine_lr(epoch)
        
        elif self.schedule_type == "warmup_cosine":
            if epoch < self.warmup_epochs:
                # Linear warmup
                return self.initial_lr * (epoch + 1) / self.warmup_epochs
            else:
                # Cosine decay
                return self._cosine_lr(epoch - self.warmup_epochs, 
                                       self.total_epochs - self.warmup_epochs)
        
        return self.initial_lr
    
    def _cosine_lr(
        self, 
        epoch: int, 
        total_epochs: Optional[int] = None
    ) -> float:
        """Cosine annealing schedule."""
        total = total_epochs or self.total_epochs
        return self.initial_lr * 0.5 * (1 + np.cos(np.pi * epoch / total))
    
    def get_schedule_preview(self) -> List[Tuple[int, float]]:
        """Preview learning rate schedule."""
        return [(e, self.get_lr(e)) for e in range(self.total_epochs)]


# =============================================================================
# CHECKPOINT MANAGER
# =============================================================================

class CheckpointManager:
    """
    Manage model checkpoints.
    
    Features:
    - Save best model
    - Save periodic checkpoints
    - Load checkpoints
    - Cleanup old checkpoints
    """
    
    def __init__(
        self,
        checkpoint_dir: str,
        save_best_only: bool = True,
        max_to_keep: int = 5,
    ):
        self.checkpoint_dir = checkpoint_dir
        self.save_best_only = save_best_only
        self.max_to_keep = max_to_keep
        
        self.best_metric = None
        self.saved_checkpoints: List[str] = []
        
        os.makedirs(checkpoint_dir, exist_ok=True)
    
    def save(
        self,
        model,
        epoch: int,
        metrics: Dict[str, float],
        is_best: bool = False,
    ) -> Optional[str]:
        """
        Save model checkpoint.
        
        Args:
            model: Model to save (TensorFlow model)
            epoch: Current epoch
            metrics: Current metrics
            is_best: Whether this is the best model
        
        Returns:
            Path to saved checkpoint
        """
        if self.save_best_only and not is_best:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"checkpoint_epoch{epoch}_{timestamp}"
        
        if is_best:
            filename = "best_" + filename
        
        checkpoint_path = os.path.join(self.checkpoint_dir, filename)
        
        # Save model
        try:
            model.save(checkpoint_path)
            
            # Save metrics
            metrics_path = checkpoint_path + "_metrics.json"
            with open(metrics_path, 'w') as f:
                json.dump({
                    "epoch": epoch,
                    "metrics": metrics,
                    "timestamp": timestamp,
                }, f, indent=2)
            
            self.saved_checkpoints.append(checkpoint_path)
            logger.info(f"Saved checkpoint: {checkpoint_path}")
            
            # Cleanup old checkpoints
            self._cleanup()
            
            return checkpoint_path
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return None
    
    def load_best(self):
        """Load the best checkpoint."""
        best_checkpoints = [
            c for c in self.saved_checkpoints 
            if "best_" in c
        ]
        
        if not best_checkpoints:
            return None
        
        latest_best = sorted(best_checkpoints)[-1]
        return self.load(latest_best)
    
    def load(self, checkpoint_path: str):
        """Load a specific checkpoint."""
        try:
            import tensorflow as tf
            model = tf.keras.models.load_model(checkpoint_path)
            logger.info(f"Loaded checkpoint: {checkpoint_path}")
            return model
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    def _cleanup(self):
        """Remove old checkpoints beyond max_to_keep."""
        if len(self.saved_checkpoints) <= self.max_to_keep:
            return
        
        # Keep best checkpoints
        best = [c for c in self.saved_checkpoints if "best_" in c]
        others = [c for c in self.saved_checkpoints if "best_" not in c]
        
        # Remove oldest non-best checkpoints
        while len(others) > self.max_to_keep - len(best):
            to_remove = others.pop(0)
            try:
                import shutil
                shutil.rmtree(to_remove)
                if os.path.exists(to_remove + "_metrics.json"):
                    os.remove(to_remove + "_metrics.json")
                self.saved_checkpoints.remove(to_remove)
            except Exception as e:
                logger.warning(f"Failed to remove checkpoint: {e}")


# =============================================================================
# TRAINING LOOP
# =============================================================================

class TrainingLoop:
    """
    Complete training loop with all features.
    
    Usage:
        config = TrainingConfig(epochs=100)
        loop = TrainingLoop(config)
        history = loop.train(model, train_data, val_data)
    """
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        
        # Initialize components
        self.early_stopping = EarlyStopping(
            patience=config.patience,
            min_delta=config.min_delta,
            mode="max" if "recall" in config.monitor_metric or "f1" in config.monitor_metric else "min",
        ) if config.early_stopping else None
        
        self.lr_scheduler = LearningRateScheduler(
            initial_lr=config.learning_rate,
            schedule_type=config.lr_schedule,
            total_epochs=config.epochs,
            warmup_epochs=config.warmup_epochs,
            decay_factor=config.lr_decay_factor,
            decay_epochs=config.lr_decay_epochs,
        )
        
        self.checkpoint_manager = CheckpointManager(
            checkpoint_dir=config.checkpoint_dir,
            save_best_only=config.save_best_only,
        )
        
        # Training history
        self.history: Dict[str, List[float]] = {
            "loss": [],
            "val_loss": [],
            "precision": [],
            "val_precision": [],
            "recall": [],
            "val_recall": [],
            "f1": [],
            "val_f1": [],
            "fpr": [],
            "val_fpr": [],
            "lr": [],
        }
        
        self.best_metrics: Optional[Dict[str, float]] = None
    
    def train(
        self,
        model,
        train_data: Tuple[np.ndarray, np.ndarray],
        val_data: Tuple[np.ndarray, np.ndarray],
        class_weights: Optional[np.ndarray] = None,
    ) -> Dict[str, List[float]]:
        """
        Execute training loop.
        
        Args:
            model: TensorFlow model
            train_data: (X_train, y_train)
            val_data: (X_val, y_val)
            class_weights: Optional class weights
        
        Returns:
            Training history
        """
        X_train, y_train = train_data
        X_val, y_val = val_data
        
        logger.info(f"Starting training: {self.config.epochs} epochs")
        logger.info(f"Train samples: {len(X_train)}, Val samples: {len(X_val)}")
        
        for epoch in range(self.config.epochs):
            # Update learning rate
            lr = self.lr_scheduler.get_lr(epoch)
            model.optimizer.learning_rate.assign(lr)
            self.history["lr"].append(lr)
            
            # Training epoch
            train_metrics = self._train_epoch(
                model, X_train, y_train, class_weights
            )
            
            # Validation
            val_metrics = self._validate(model, X_val, y_val)
            
            # Log metrics
            self._log_epoch(epoch, train_metrics, val_metrics)
            
            # Check if best model
            monitor_value = val_metrics.get(
                self.config.monitor_metric.replace("val_", ""),
                val_metrics.get("recall", 0.0)
            )
            
            is_best = (
                self.best_metrics is None or 
                monitor_value > self.best_metrics.get(
                    self.config.monitor_metric.replace("val_", ""), 0.0
                )
            )
            
            if is_best:
                self.best_metrics = val_metrics
                self.checkpoint_manager.save(
                    model, epoch, val_metrics, is_best=True
                )
            
            # Early stopping check
            if self.early_stopping:
                if self.early_stopping(monitor_value, epoch, model.get_weights()):
                    logger.info(f"Early stopping at epoch {epoch}")
                    break
            
            # Periodic checkpoint
            if epoch % self.config.save_frequency == 0:
                self.checkpoint_manager.save(model, epoch, val_metrics)
        
        logger.info("Training complete")
        logger.info(f"Best metrics: {self.best_metrics}")
        
        return self.history
    
    def _train_epoch(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
        class_weights: Optional[np.ndarray],
    ) -> Dict[str, float]:
        """Train one epoch."""
        import tensorflow as tf
        
        # Shuffle data
        indices = np.random.permutation(len(X))
        X = X[indices]
        y = y[indices]
        
        # Batch training
        losses = []
        all_preds = []
        all_labels = []
        
        n_batches = len(X) // self.config.batch_size
        
        for i in range(n_batches):
            start = i * self.config.batch_size
            end = start + self.config.batch_size
            
            X_batch = X[start:end]
            y_batch = y[start:end]
            
            with tf.GradientTape() as tape:
                predictions = model(X_batch, training=True)
                
                # Calculate loss
                if self.config.use_focal_loss:
                    from .class_balancer import FocalLossWeighter
                    focal = FocalLossWeighter(
                        gamma=self.config.focal_gamma,
                        alpha=class_weights
                    )
                    loss = focal.get_loss_function()(y_batch, predictions)
                else:
                    loss = tf.keras.losses.binary_crossentropy(
                        y_batch, predictions
                    )
                    
                    if class_weights is not None:
                        weights = tf.reduce_sum(
                            y_batch * class_weights, axis=-1
                        )
                        loss = loss * weights
                    
                    loss = tf.reduce_mean(loss)
            
            # Gradient update
            gradients = tape.gradient(loss, model.trainable_variables)
            model.optimizer.apply_gradients(
                zip(gradients, model.trainable_variables)
            )
            
            losses.append(float(loss))
            all_preds.append(predictions.numpy())
            all_labels.append(y_batch)
        
        # Calculate metrics
        all_preds = np.concatenate(all_preds)
        all_labels = np.concatenate(all_labels)
        
        return self._calculate_metrics(all_labels, all_preds, np.mean(losses))
    
    def _validate(
        self,
        model,
        X: np.ndarray,
        y: np.ndarray,
    ) -> Dict[str, float]:
        """Validate model."""
        predictions = model(X, training=False).numpy()
        loss = float(np.mean(
            -y * np.log(predictions + 1e-7) - 
            (1 - y) * np.log(1 - predictions + 1e-7)
        ))
        
        return self._calculate_metrics(y, predictions, loss)
    
    def _calculate_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        loss: float,
    ) -> Dict[str, float]:
        """Calculate all metrics."""
        y_pred_binary = (y_pred >= 0.5).astype(int)
        
        tp = np.sum((y_pred_binary == 1) & (y_true == 1))
        fp = np.sum((y_pred_binary == 1) & (y_true == 0))
        fn = np.sum((y_pred_binary == 0) & (y_true == 1))
        tn = np.sum((y_pred_binary == 0) & (y_true == 0))
        
        precision = tp / (tp + fp + 1e-10)
        recall = tp / (tp + fn + 1e-10)
        f1 = 2 * precision * recall / (precision + recall + 1e-10)
        fpr = fp / (fp + tn + 1e-10)
        
        return {
            "loss": loss,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "fpr": fpr,
        }
    
    def _log_epoch(
        self,
        epoch: int,
        train_metrics: Dict[str, float],
        val_metrics: Dict[str, float],
    ):
        """Log epoch metrics."""
        self.history["loss"].append(train_metrics["loss"])
        self.history["val_loss"].append(val_metrics["loss"])
        self.history["precision"].append(train_metrics["precision"])
        self.history["val_precision"].append(val_metrics["precision"])
        self.history["recall"].append(train_metrics["recall"])
        self.history["val_recall"].append(val_metrics["recall"])
        self.history["f1"].append(train_metrics["f1"])
        self.history["val_f1"].append(val_metrics["f1"])
        self.history["fpr"].append(train_metrics["fpr"])
        self.history["val_fpr"].append(val_metrics["fpr"])
        
        logger.info(
            f"Epoch {epoch}: "
            f"loss={train_metrics['loss']:.4f}, "
            f"val_loss={val_metrics['loss']:.4f}, "
            f"recall={train_metrics['recall']:.4f}, "
            f"val_recall={val_metrics['recall']:.4f}, "
            f"fpr={train_metrics['fpr']:.4f}, "
            f"val_fpr={val_metrics['fpr']:.4f}"
        )
    
    def get_best_model(self):
        """Load the best saved model."""
        return self.checkpoint_manager.load_best()
    
    def export_history(self, path: str):
        """Export training history to JSON."""
        with open(path, 'w') as f:
            json.dump({
                "history": self.history,
                "config": self.config.to_dict(),
                "best_metrics": self.best_metrics,
            }, f, indent=2)
