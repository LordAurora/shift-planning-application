"""
Security Model Training Pipeline

Training infrastructure for security vulnerability detection models.
Supports:
- Dataset preparation
- Model training with TensorFlow
- Evaluation and validation
- Checkpoint management
- Huawei Cloud ModelArts compatibility (Phase 2)
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import time

logger = logging.getLogger(__name__)


@dataclass
class TrainingExample:
    """Single training example."""
    code: str
    language: str
    labels: List[str]  # Vulnerability categories
    severity: str
    source: str = "manual"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainingDataset:
    """Training dataset container."""
    examples: List[TrainingExample]
    name: str
    version: str = "1.0"
    created_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "created_at": self.created_at,
            "num_examples": len(self.examples),
            "examples": [
                {
                    "code": e.code,
                    "language": e.language,
                    "labels": e.labels,
                    "severity": e.severity,
                    "source": e.source
                }
                for e in self.examples
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrainingDataset":
        examples = [
            TrainingExample(
                code=e["code"],
                language=e["language"],
                labels=e["labels"],
                severity=e["severity"],
                source=e.get("source", "manual")
            )
            for e in data.get("examples", [])
        ]
        return cls(
            examples=examples,
            name=data["name"],
            version=data.get("version", "1.0"),
            created_at=data.get("created_at", "")
        )


@dataclass
class TrainingConfig:
    """Training configuration."""
    batch_size: int = 32
    epochs: int = 100
    learning_rate: float = 0.001
    validation_split: float = 0.2
    early_stopping_patience: int = 10
    checkpoint_dir: str = "./checkpoints"
    log_dir: str = "./logs"
    mixed_precision: bool = False  # Enable for GPU optimization
    
    # Model architecture
    embedding_dim: int = 256
    num_heads: int = 8
    ff_dim: int = 512
    num_layers: int = 4
    dropout_rate: float = 0.1


@dataclass
class TrainingMetrics:
    """Training run metrics."""
    epoch: int
    train_loss: float
    train_accuracy: float
    val_loss: float
    val_accuracy: float
    learning_rate: float
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "epoch": self.epoch,
            "train_loss": self.train_loss,
            "train_accuracy": self.train_accuracy,
            "val_loss": self.val_loss,
            "val_accuracy": self.val_accuracy,
            "learning_rate": self.learning_rate,
            "timestamp": self.timestamp
        }


@dataclass
class TrainingResult:
    """Complete training run result."""
    model_name: str
    final_metrics: TrainingMetrics
    history: List[TrainingMetrics]
    total_epochs: int
    training_time_seconds: float
    checkpoint_path: str
    config: TrainingConfig


class SecurityTrainingPipeline:
    """
    Training pipeline for security vulnerability detection models.
    
    Supports training on custom vulnerability datasets with:
    - Multi-label classification for vulnerability types
    - Severity prediction
    - Transfer learning support
    
    Example:
        pipeline = SecurityTrainingPipeline()
        
        # Load or create dataset
        dataset = pipeline.create_sample_dataset()
        
        # Train model
        result = pipeline.train(
            dataset=dataset,
            config=TrainingConfig(epochs=50, batch_size=16)
        )
        
        print(f"Final accuracy: {result.final_metrics.val_accuracy}")
    """
    
    def __init__(self, config: Optional[TrainingConfig] = None):
        """Initialize training pipeline."""
        self.config = config or TrainingConfig()
        self._model = None
        self._tokenizer = None
        
        # Create directories
        Path(self.config.checkpoint_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.log_dir).mkdir(parents=True, exist_ok=True)
    
    def create_sample_dataset(self) -> TrainingDataset:
        """
        Create sample training dataset with vulnerability examples.
        
        Returns:
            TrainingDataset with example vulnerable code snippets
        """
        from datetime import datetime
        
        examples = [
            # SQL Injection examples
            TrainingExample(
                code='query = f"SELECT * FROM users WHERE id = {user_id}"',
                language="python",
                labels=["INJECTION"],
                severity="critical"
            ),
            TrainingExample(
                code='cursor.execute("SELECT * FROM users WHERE name = \'" + name + "\'")',
                language="python",
                labels=["INJECTION"],
                severity="critical"
            ),
            TrainingExample(
                code='const query = `SELECT * FROM products WHERE id = ${id}`',
                language="javascript",
                labels=["INJECTION"],
                severity="critical"
            ),
            
            # Hardcoded secrets
            TrainingExample(
                code='API_KEY = "sk-1234567890abcdef"',
                language="python",
                labels=["HARDCODED_SECRETS"],
                severity="high"
            ),
            TrainingExample(
                code='password = "admin123!@#"',
                language="python",
                labels=["HARDCODED_SECRETS"],
                severity="critical"
            ),
            TrainingExample(
                code='const AWS_SECRET = "AKIAIOSFODNN7EXAMPLE"',
                language="javascript",
                labels=["HARDCODED_SECRETS"],
                severity="critical"
            ),
            
            # Broken authentication
            TrainingExample(
                code='if user.password == input_password:',
                language="python",
                labels=["BROKEN_AUTH"],
                severity="high"
            ),
            TrainingExample(
                code='token = jwt.encode(payload, "secret", algorithm="none")',
                language="python",
                labels=["BROKEN_AUTH", "INSECURE_CRYPTO"],
                severity="critical"
            ),
            
            # XSS examples
            TrainingExample(
                code='document.innerHTML = userInput;',
                language="javascript",
                labels=["XSS"],
                severity="high"
            ),
            TrainingExample(
                code='return f"<div>{user_content}</div>"',
                language="python",
                labels=["XSS"],
                severity="medium"
            ),
            
            # Path traversal
            TrainingExample(
                code='open(f"/data/{filename}")',
                language="python",
                labels=["PATH_TRAVERSAL"],
                severity="high"
            ),
            TrainingExample(
                code='fs.readFileSync(baseDir + userPath)',
                language="javascript",
                labels=["PATH_TRAVERSAL"],
                severity="high"
            ),
            
            # Insecure deserialization
            TrainingExample(
                code='data = pickle.loads(user_input)',
                language="python",
                labels=["INSECURE_DESERIALIZATION"],
                severity="critical"
            ),
            TrainingExample(
                code='obj = yaml.load(request.data)',
                language="python",
                labels=["INSECURE_DESERIALIZATION"],
                severity="critical"
            ),
            
            # Insecure crypto
            TrainingExample(
                code='hashlib.md5(password.encode()).hexdigest()',
                language="python",
                labels=["INSECURE_CRYPTO"],
                severity="high"
            ),
            TrainingExample(
                code='from Crypto.Cipher import DES',
                language="python",
                labels=["INSECURE_CRYPTO"],
                severity="high"
            ),
            
            # SSRF
            TrainingExample(
                code='requests.get(user_provided_url)',
                language="python",
                labels=["SSRF"],
                severity="high"
            ),
            
            # Safe examples (no vulnerabilities)
            TrainingExample(
                code='cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))',
                language="python",
                labels=[],
                severity="info"
            ),
            TrainingExample(
                code='password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())',
                language="python",
                labels=[],
                severity="info"
            ),
            TrainingExample(
                code='api_key = os.environ.get("API_KEY")',
                language="python",
                labels=[],
                severity="info"
            ),
        ]
        
        return TrainingDataset(
            examples=examples,
            name="security_vulnerabilities_v1",
            version="1.0",
            created_at=datetime.utcnow().isoformat()
        )
    
    def prepare_data(
        self,
        dataset: TrainingDataset
    ) -> Tuple[Any, Any, Any, Any]:
        """
        Prepare dataset for training.
        
        Args:
            dataset: Training dataset
        
        Returns:
            Tuple of (X_train, X_val, y_train, y_val)
        """
        try:
            import numpy as np
        except ImportError:
            logger.error("NumPy required for training")
            raise
        
        # Define all vulnerability categories
        categories = [
            "INJECTION", "HARDCODED_SECRETS", "BROKEN_AUTH", "XSS",
            "PATH_TRAVERSAL", "INSECURE_DESERIALIZATION", "INSECURE_CRYPTO",
            "SSRF", "SECURITY_MISCONFIGURATION", "INSUFFICIENT_LOGGING"
        ]
        
        # Tokenize code
        X = []
        y = []
        
        for example in dataset.examples:
            # Simple tokenization (in production, use proper tokenizer)
            tokens = self._tokenize(example.code)
            X.append(tokens)
            
            # Multi-hot encode labels
            label_vec = [1 if cat in example.labels else 0 for cat in categories]
            y.append(label_vec)
        
        X = np.array(X)
        y = np.array(y)
        
        # Split
        split_idx = int(len(X) * (1 - self.config.validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        logger.info(f"Prepared {len(X_train)} training, {len(X_val)} validation examples")
        
        return X_train, X_val, y_train, y_val
    
    def _tokenize(self, code: str, max_length: int = 512) -> List[int]:
        """Simple character-level tokenization."""
        # In production, use proper tokenizer (SentencePiece, BPE)
        tokens = [ord(c) % 256 for c in code[:max_length]]
        # Pad to max_length
        tokens = tokens + [0] * (max_length - len(tokens))
        return tokens
    
    def build_model(self, num_classes: int = 10):
        """
        Build vulnerability detection model.
        
        Args:
            num_classes: Number of vulnerability categories
        
        Returns:
            Compiled TensorFlow model
        """
        try:
            import tensorflow as tf
            from tensorflow import keras
            from tensorflow.keras import layers
        except ImportError:
            logger.error("TensorFlow required for training")
            raise
        
        # Input
        inputs = layers.Input(shape=(512,), name="code_input")
        
        # Embedding
        x = layers.Embedding(
            input_dim=256,
            output_dim=self.config.embedding_dim,
            name="code_embedding"
        )(inputs)
        
        # Transformer blocks
        for i in range(self.config.num_layers):
            # Multi-head attention
            attn_output = layers.MultiHeadAttention(
                num_heads=self.config.num_heads,
                key_dim=self.config.embedding_dim // self.config.num_heads,
                name=f"attention_{i}"
            )(x, x)
            attn_output = layers.Dropout(self.config.dropout_rate)(attn_output)
            x = layers.LayerNormalization(epsilon=1e-6)(x + attn_output)
            
            # Feed forward
            ff = layers.Dense(self.config.ff_dim, activation="relu")(x)
            ff = layers.Dense(self.config.embedding_dim)(ff)
            ff = layers.Dropout(self.config.dropout_rate)(ff)
            x = layers.LayerNormalization(epsilon=1e-6)(x + ff)
        
        # Global pooling
        x = layers.GlobalAveragePooling1D()(x)
        
        # Classification head
        x = layers.Dense(256, activation="relu")(x)
        x = layers.Dropout(self.config.dropout_rate)(x)
        x = layers.Dense(128, activation="relu")(x)
        
        # Multi-label output
        outputs = layers.Dense(
            num_classes,
            activation="sigmoid",
            name="vulnerability_output"
        )(x)
        
        model = keras.Model(inputs=inputs, outputs=outputs, name="VulnerabilityDetector")
        
        # Compile
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.config.learning_rate),
            loss="binary_crossentropy",
            metrics=[
                keras.metrics.BinaryAccuracy(name="accuracy"),
                keras.metrics.Precision(name="precision"),
                keras.metrics.Recall(name="recall")
            ]
        )
        
        self._model = model
        logger.info(f"Built model with {model.count_params():,} parameters")
        
        return model
    
    def train(
        self,
        dataset: TrainingDataset,
        config: Optional[TrainingConfig] = None
    ) -> TrainingResult:
        """
        Train vulnerability detection model.
        
        Args:
            dataset: Training dataset
            config: Training configuration (optional override)
        
        Returns:
            TrainingResult with metrics and checkpoint path
        """
        try:
            import tensorflow as tf
            from tensorflow import keras
        except ImportError:
            logger.error("TensorFlow required for training")
            raise
        
        from datetime import datetime
        
        if config:
            self.config = config
        
        start_time = time.time()
        
        # Prepare data
        X_train, X_val, y_train, y_val = self.prepare_data(dataset)
        
        # Build model
        num_classes = y_train.shape[1]
        model = self.build_model(num_classes)
        
        # Callbacks
        checkpoint_path = Path(self.config.checkpoint_dir) / f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor="val_loss",
                patience=self.config.early_stopping_patience,
                restore_best_weights=True
            ),
            keras.callbacks.ModelCheckpoint(
                str(checkpoint_path),
                monitor="val_loss",
                save_best_only=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss",
                factor=0.5,
                patience=5,
                min_lr=1e-6
            ),
            keras.callbacks.TensorBoard(
                log_dir=self.config.log_dir
            )
        ]
        
        logger.info(f"Starting training for {self.config.epochs} epochs")
        
        # Train
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        # Collect metrics
        training_history = []
        for i in range(len(history.history["loss"])):
            training_history.append(TrainingMetrics(
                epoch=i + 1,
                train_loss=history.history["loss"][i],
                train_accuracy=history.history["accuracy"][i],
                val_loss=history.history["val_loss"][i],
                val_accuracy=history.history["val_accuracy"][i],
                learning_rate=float(model.optimizer.learning_rate.numpy()),
                timestamp=datetime.utcnow().isoformat()
            ))
        
        training_time = time.time() - start_time
        
        result = TrainingResult(
            model_name="vulnerability_detector",
            final_metrics=training_history[-1],
            history=training_history,
            total_epochs=len(training_history),
            training_time_seconds=round(training_time, 2),
            checkpoint_path=str(checkpoint_path),
            config=self.config
        )
        
        logger.info(f"Training complete in {training_time:.1f}s")
        logger.info(f"Final val_accuracy: {result.final_metrics.val_accuracy:.4f}")
        
        return result
    
    def evaluate(
        self,
        model_path: str,
        test_dataset: TrainingDataset
    ) -> Dict[str, float]:
        """
        Evaluate trained model on test dataset.
        
        Args:
            model_path: Path to saved model
            test_dataset: Test dataset
        
        Returns:
            Dictionary with evaluation metrics
        """
        try:
            import tensorflow as tf
            from tensorflow import keras
            import numpy as np
        except ImportError:
            raise ImportError("TensorFlow required")
        
        # Load model
        model = keras.models.load_model(model_path)
        
        # Prepare test data
        X_test = np.array([self._tokenize(e.code) for e in test_dataset.examples])
        categories = [
            "INJECTION", "HARDCODED_SECRETS", "BROKEN_AUTH", "XSS",
            "PATH_TRAVERSAL", "INSECURE_DESERIALIZATION", "INSECURE_CRYPTO",
            "SSRF", "SECURITY_MISCONFIGURATION", "INSUFFICIENT_LOGGING"
        ]
        y_test = np.array([
            [1 if cat in e.labels else 0 for cat in categories]
            for e in test_dataset.examples
        ])
        
        # Evaluate
        results = model.evaluate(X_test, y_test, verbose=0)
        
        metrics = {
            "loss": results[0],
            "accuracy": results[1],
            "precision": results[2],
            "recall": results[3]
        }
        
        return metrics
    
    def save_dataset(self, dataset: TrainingDataset, path: str) -> str:
        """Save dataset to JSON file."""
        with open(path, 'w') as f:
            json.dump(dataset.to_dict(), f, indent=2)
        logger.info(f"Dataset saved to {path}")
        return path
    
    def load_dataset(self, path: str) -> TrainingDataset:
        """Load dataset from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return TrainingDataset.from_dict(data)


class HuaweiCloudTrainer:
    """
    Training adapter for Huawei Cloud ModelArts.
    
    Phase 2 implementation for training on Huawei Cloud infrastructure.
    Supports:
    - ModelArts training jobs
    - Ascend NPU optimization
    - MindSpore model conversion
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Huawei Cloud trainer."""
        self.config = config
        self._client = None
    
    def connect(self, credentials: Dict[str, str]) -> bool:
        """Connect to Huawei Cloud ModelArts."""
        # Phase 2: Implement ModelArts SDK connection
        logger.info("Huawei Cloud ModelArts connection - Phase 2")
        return False
    
    def create_training_job(
        self,
        dataset_path: str,
        training_config: TrainingConfig
    ) -> str:
        """Create and submit training job to ModelArts."""
        # Phase 2: Implement job submission
        raise NotImplementedError("Phase 2: Huawei Cloud integration")
    
    def monitor_job(self, job_id: str) -> Dict[str, Any]:
        """Monitor training job status."""
        # Phase 2: Implement job monitoring
        raise NotImplementedError("Phase 2: Huawei Cloud integration")
    
    def convert_to_mindspore(self, tf_model_path: str) -> str:
        """Convert TensorFlow model to MindSpore format."""
        # Phase 2: Implement model conversion
        raise NotImplementedError("Phase 2: MindSpore conversion")
