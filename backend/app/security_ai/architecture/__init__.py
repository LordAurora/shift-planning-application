"""
Framework-Agnostic ML Architecture for Vulnerability Detection

Modular, explainable architecture designed for:
- Phase 1: TensorFlow training and inference
- Phase 2: MindSpore migration for Huawei Ascend NPU

Design Principles:
1. Clear separation of concerns (preprocessing, features, classification, inference)
2. Framework-agnostic interfaces with pluggable implementations
3. Explainability built-in (attention visualization, feature importance)
4. Multi-label classification support
5. Ascend NPU compatibility considerations
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Union, Protocol
from enum import Enum
import numpy as np
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class FrameworkType(Enum):
    """Supported ML frameworks."""
    TENSORFLOW = "tensorflow"
    MINDSPORE = "mindspore"
    NUMPY = "numpy"  # For CPU-only inference


@dataclass
class ModelConfig:
    """
    Framework-agnostic model configuration.
    
    All hyperparameters are framework-neutral to ensure
    identical model architecture across TensorFlow and MindSpore.
    """
    # Input configuration
    max_sequence_length: int = 512
    vocab_size: int = 50000
    
    # Embedding
    embedding_dim: int = 256
    use_positional_encoding: bool = True
    
    # Transformer encoder
    num_encoder_layers: int = 4
    num_attention_heads: int = 8
    feed_forward_dim: int = 1024
    dropout_rate: float = 0.1
    
    # Classification head
    num_classes: int = 15  # Vulnerability categories
    hidden_dims: List[int] = field(default_factory=lambda: [512, 256])
    
    # Multi-label settings
    multi_label: bool = True
    label_smoothing: float = 0.1
    
    # Explainability
    return_attention_weights: bool = True
    
    # Training (framework-neutral)
    learning_rate: float = 1e-4
    warmup_steps: int = 1000
    weight_decay: float = 0.01
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_sequence_length": self.max_sequence_length,
            "vocab_size": self.vocab_size,
            "embedding_dim": self.embedding_dim,
            "use_positional_encoding": self.use_positional_encoding,
            "num_encoder_layers": self.num_encoder_layers,
            "num_attention_heads": self.num_attention_heads,
            "feed_forward_dim": self.feed_forward_dim,
            "dropout_rate": self.dropout_rate,
            "num_classes": self.num_classes,
            "hidden_dims": self.hidden_dims,
            "multi_label": self.multi_label,
            "label_smoothing": self.label_smoothing,
            "return_attention_weights": self.return_attention_weights,
            "learning_rate": self.learning_rate,
            "warmup_steps": self.warmup_steps,
            "weight_decay": self.weight_decay,
        }


# =============================================================================
# ABSTRACT INTERFACES (Framework-Agnostic)
# =============================================================================

class Preprocessor(ABC):
    """
    Abstract preprocessor interface.
    
    Responsible for:
    - Text tokenization
    - Sequence padding/truncation
    - Vocabulary management
    
    Framework-agnostic: Uses only Python/NumPy operations.
    """
    
    @abstractmethod
    def tokenize(self, text: str) -> List[int]:
        """Convert text to token IDs."""
        pass
    
    @abstractmethod
    def encode(self, text: str, max_length: Optional[int] = None) -> np.ndarray:
        """Encode text to padded token IDs."""
        pass
    
    @abstractmethod
    def decode(self, token_ids: np.ndarray) -> str:
        """Decode token IDs back to text."""
        pass
    
    @abstractmethod
    def build_vocab(self, texts: List[str]) -> None:
        """Build vocabulary from corpus."""
        pass
    
    @abstractmethod
    def save(self, path: str) -> None:
        """Save preprocessor state."""
        pass
    
    @abstractmethod
    def load(self, path: str) -> None:
        """Load preprocessor state."""
        pass


class FeatureExtractor(ABC):
    """
    Abstract feature extractor interface.
    
    Responsible for:
    - Embedding lookup
    - Positional encoding
    - Transformer encoding
    - Attention computation
    
    Returns attention weights for explainability.
    """
    
    @abstractmethod
    def extract(
        self,
        token_ids: np.ndarray,
        return_attention: bool = False
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Extract features from token IDs.
        
        Args:
            token_ids: Input token IDs [batch, seq_len]
            return_attention: Whether to return attention weights
        
        Returns:
            Tuple of (features, attention_weights)
            - features: [batch, hidden_dim]
            - attention_weights: [batch, num_heads, seq_len, seq_len] or None
        """
        pass
    
    @abstractmethod
    def get_embeddings(self, token_ids: np.ndarray) -> np.ndarray:
        """Get token embeddings without full encoding."""
        pass


class Classifier(ABC):
    """
    Abstract classifier interface.
    
    Responsible for:
    - Multi-label classification
    - Probability calibration
    - Threshold optimization
    """
    
    @abstractmethod
    def predict(self, features: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.
        
        Args:
            features: Input features [batch, hidden_dim]
        
        Returns:
            Probabilities [batch, num_classes]
        """
        pass
    
    @abstractmethod
    def predict_labels(
        self,
        features: np.ndarray,
        threshold: float = 0.5
    ) -> np.ndarray:
        """
        Predict binary labels (multi-label).
        
        Args:
            features: Input features [batch, hidden_dim]
            threshold: Classification threshold
        
        Returns:
            Binary labels [batch, num_classes]
        """
        pass


class InferenceEngine(ABC):
    """
    Abstract inference engine interface.
    
    Orchestrates the full pipeline:
    Preprocess → Extract Features → Classify → Explain
    """
    
    @abstractmethod
    def predict(
        self,
        text: Union[str, List[str]],
        return_explanation: bool = False
    ) -> Dict[str, Any]:
        """
        Run full inference pipeline.
        
        Args:
            text: Input text or list of texts
            return_explanation: Whether to include explanations
        
        Returns:
            Dictionary with predictions and optional explanations
        """
        pass
    
    @abstractmethod
    def explain(
        self,
        text: str,
        target_class: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate explanation for prediction.
        
        Args:
            text: Input text
            target_class: Class to explain (None = top prediction)
        
        Returns:
            Explanation with attention weights, important tokens, etc.
        """
        pass
    
    @abstractmethod
    def batch_predict(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[Dict[str, Any]]:
        """Batch prediction for efficiency."""
        pass


# =============================================================================
# EXPLAINABILITY COMPONENTS
# =============================================================================

@dataclass
class AttentionExplanation:
    """Attention-based explanation for a prediction."""
    input_tokens: List[str]
    attention_weights: np.ndarray  # [num_heads, seq_len, seq_len]
    head_importance: np.ndarray    # [num_heads]
    token_importance: np.ndarray   # [seq_len]
    top_tokens: List[Tuple[str, float]]  # (token, importance)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "attention_weights": self.attention_weights.tolist(),
            "head_importance": self.head_importance.tolist(),
            "token_importance": self.token_importance.tolist(),
            "top_tokens": self.top_tokens
        }


@dataclass
class PredictionExplanation:
    """Full explanation for a vulnerability prediction."""
    input_text: str
    predicted_classes: List[str]
    class_probabilities: Dict[str, float]
    attention_explanation: AttentionExplanation
    feature_contributions: Dict[str, float]
    reasoning: str  # Human-readable explanation
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_text": self.input_text[:200] + "..." if len(self.input_text) > 200 else self.input_text,
            "predicted_classes": self.predicted_classes,
            "class_probabilities": self.class_probabilities,
            "attention_explanation": self.attention_explanation.to_dict(),
            "feature_contributions": self.feature_contributions,
            "reasoning": self.reasoning
        }


class ExplainabilityModule:
    """
    Framework-agnostic explainability module.
    
    Provides:
    - Attention weight visualization
    - Token importance scoring
    - Feature contribution analysis
    - Human-readable reasoning generation
    
    Uses only NumPy operations for framework independence.
    """
    
    def __init__(self, class_names: List[str]):
        self.class_names = class_names
    
    def compute_token_importance(
        self,
        attention_weights: np.ndarray,
        aggregation: str = "mean"
    ) -> np.ndarray:
        """
        Compute token importance from attention weights.
        
        Uses attention rollout technique for multi-layer transformers.
        
        Args:
            attention_weights: [num_layers, num_heads, seq_len, seq_len]
            aggregation: "mean", "max", or "rollout"
        
        Returns:
            Token importance scores [seq_len]
        """
        if aggregation == "mean":
            # Average attention across layers and heads, then sum columns
            avg_attention = attention_weights.mean(axis=(0, 1))  # [seq_len, seq_len]
            importance = avg_attention.sum(axis=0)  # How much each token is attended to
            
        elif aggregation == "max":
            # Max attention to each token
            max_attention = attention_weights.max(axis=(0, 1))
            importance = max_attention.sum(axis=0)
            
        elif aggregation == "rollout":
            # Attention rollout: multiply attention matrices
            # This captures indirect attention flow
            num_layers = attention_weights.shape[0]
            
            # Average over heads
            attention = attention_weights.mean(axis=1)  # [num_layers, seq_len, seq_len]
            
            # Add residual connection (identity matrix)
            eye = np.eye(attention.shape[1])
            attention = 0.5 * attention + 0.5 * eye
            
            # Renormalize
            attention = attention / attention.sum(axis=-1, keepdims=True)
            
            # Rollout: multiply through layers
            rollout = attention[0]
            for i in range(1, num_layers):
                rollout = np.matmul(attention[i], rollout)
            
            # CLS token (first token) attention to all others
            importance = rollout[0]
        else:
            raise ValueError(f"Unknown aggregation: {aggregation}")
        
        # Normalize to [0, 1]
        importance = importance / (importance.max() + 1e-8)
        
        return importance
    
    def compute_head_importance(
        self,
        attention_weights: np.ndarray,
        gradient: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Compute importance of each attention head.
        
        If gradient is provided, uses gradient-weighted attention.
        Otherwise, uses attention entropy as proxy.
        
        Args:
            attention_weights: [num_layers, num_heads, seq_len, seq_len]
            gradient: Optional gradient for gradient-based importance
        
        Returns:
            Head importance [num_layers * num_heads]
        """
        num_layers, num_heads, seq_len, _ = attention_weights.shape
        
        if gradient is not None:
            # Gradient-weighted importance
            importance = (attention_weights * gradient).sum(axis=(2, 3))
        else:
            # Use negative entropy as importance (lower entropy = more focused attention)
            # Focused attention is typically more important
            attention_flat = attention_weights.reshape(num_layers * num_heads, seq_len, seq_len)
            
            # Compute entropy per head
            entropy = -np.sum(
                attention_flat * np.log(attention_flat + 1e-8),
                axis=(1, 2)
            ) / (seq_len * seq_len)
            
            # Lower entropy = more important (more focused)
            importance = 1.0 - entropy / np.log(seq_len)
        
        return importance.flatten()
    
    def generate_reasoning(
        self,
        predicted_classes: List[str],
        probabilities: Dict[str, float],
        top_tokens: List[Tuple[str, float]],
        code_patterns: Optional[List[str]] = None
    ) -> str:
        """
        Generate human-readable explanation.
        
        Args:
            predicted_classes: List of predicted vulnerability types
            probabilities: Class probabilities
            top_tokens: Most important tokens with scores
            code_patterns: Detected code patterns (optional)
        
        Returns:
            Human-readable explanation string
        """
        if not predicted_classes:
            return "No vulnerabilities detected. The code appears to follow secure practices."
        
        lines = []
        
        # Main findings
        if len(predicted_classes) == 1:
            lines.append(f"**Detected Vulnerability:** {predicted_classes[0]} "
                        f"(confidence: {probabilities[predicted_classes[0]]:.1%})")
        else:
            lines.append(f"**Detected {len(predicted_classes)} Vulnerabilities:**")
            for cls in predicted_classes:
                lines.append(f"  - {cls}: {probabilities[cls]:.1%} confidence")
        
        # Key indicators
        if top_tokens:
            lines.append("\n**Key Code Indicators:**")
            for token, score in top_tokens[:5]:
                if score > 0.3:  # Only show significant tokens
                    lines.append(f"  - `{token}` (importance: {score:.2f})")
        
        # Pattern-based reasoning
        if code_patterns:
            lines.append("\n**Detected Patterns:**")
            for pattern in code_patterns[:3]:
                lines.append(f"  - {pattern}")
        
        # Recommendations
        lines.append("\n**Recommended Actions:**")
        for cls in predicted_classes[:2]:  # Top 2 recommendations
            rec = self._get_recommendation(cls)
            lines.append(f"  - {rec}")
        
        return "\n".join(lines)
    
    def _get_recommendation(self, vulnerability_class: str) -> str:
        """Get recommendation for a vulnerability class."""
        recommendations = {
            "INJECTION": "Use parameterized queries or prepared statements",
            "HARDCODED_SECRETS": "Move secrets to environment variables or secret manager",
            "BROKEN_AUTH": "Implement secure password hashing (bcrypt/Argon2)",
            "XSS": "Sanitize user input and use proper output encoding",
            "PATH_TRAVERSAL": "Validate and sanitize file paths, use allowlists",
            "INSECURE_CRYPTO": "Use modern algorithms (AES-256, SHA-256+)",
            "SSRF": "Validate URLs against allowlist, block internal IPs",
            "DESERIALIZATION": "Avoid deserializing untrusted data, use safe parsers",
        }
        return recommendations.get(
            vulnerability_class,
            "Review and apply security best practices"
        )
    
    def create_explanation(
        self,
        input_text: str,
        input_tokens: List[str],
        attention_weights: np.ndarray,
        predicted_classes: List[str],
        class_probabilities: Dict[str, float],
        feature_contributions: Optional[Dict[str, float]] = None
    ) -> PredictionExplanation:
        """Create full prediction explanation."""
        
        # Compute token importance
        token_importance = self.compute_token_importance(
            attention_weights, aggregation="rollout"
        )
        
        # Compute head importance
        head_importance = self.compute_head_importance(attention_weights)
        
        # Get top tokens
        token_scores = list(zip(input_tokens, token_importance.tolist()))
        top_tokens = sorted(token_scores, key=lambda x: x[1], reverse=True)[:10]
        
        # Create attention explanation
        attention_explanation = AttentionExplanation(
            input_tokens=input_tokens,
            attention_weights=attention_weights,
            head_importance=head_importance,
            token_importance=token_importance,
            top_tokens=top_tokens
        )
        
        # Generate reasoning
        reasoning = self.generate_reasoning(
            predicted_classes,
            class_probabilities,
            top_tokens
        )
        
        return PredictionExplanation(
            input_text=input_text,
            predicted_classes=predicted_classes,
            class_probabilities=class_probabilities,
            attention_explanation=attention_explanation,
            feature_contributions=feature_contributions or {},
            reasoning=reasoning
        )


# =============================================================================
# MODEL REGISTRY
# =============================================================================

class ModelRegistry:
    """
    Registry for framework-specific implementations.
    
    Allows switching between TensorFlow and MindSpore
    without changing application code.
    """
    
    _preprocessors: Dict[str, type] = {}
    _feature_extractors: Dict[str, type] = {}
    _classifiers: Dict[str, type] = {}
    _inference_engines: Dict[str, type] = {}
    
    @classmethod
    def register_preprocessor(cls, framework: str, preprocessor_cls: type):
        cls._preprocessors[framework] = preprocessor_cls
    
    @classmethod
    def register_feature_extractor(cls, framework: str, extractor_cls: type):
        cls._feature_extractors[framework] = extractor_cls
    
    @classmethod
    def register_classifier(cls, framework: str, classifier_cls: type):
        cls._classifiers[framework] = classifier_cls
    
    @classmethod
    def register_inference_engine(cls, framework: str, engine_cls: type):
        cls._inference_engines[framework] = engine_cls
    
    @classmethod
    def get_preprocessor(cls, framework: str) -> type:
        if framework not in cls._preprocessors:
            raise ValueError(f"No preprocessor registered for {framework}")
        return cls._preprocessors[framework]
    
    @classmethod
    def get_feature_extractor(cls, framework: str) -> type:
        if framework not in cls._feature_extractors:
            raise ValueError(f"No feature extractor registered for {framework}")
        return cls._feature_extractors[framework]
    
    @classmethod
    def get_classifier(cls, framework: str) -> type:
        if framework not in cls._classifiers:
            raise ValueError(f"No classifier registered for {framework}")
        return cls._classifiers[framework]
    
    @classmethod
    def get_inference_engine(cls, framework: str) -> type:
        if framework not in cls._inference_engines:
            raise ValueError(f"No inference engine registered for {framework}")
        return cls._inference_engines[framework]
    
    @classmethod
    def create_pipeline(
        cls,
        framework: str,
        config: ModelConfig
    ) -> Tuple[Preprocessor, FeatureExtractor, Classifier, InferenceEngine]:
        """Create complete pipeline for a framework."""
        preprocessor = cls.get_preprocessor(framework)(config)
        extractor = cls.get_feature_extractor(framework)(config)
        classifier = cls.get_classifier(framework)(config)
        engine = cls.get_inference_engine(framework)(
            preprocessor, extractor, classifier, config
        )
        return preprocessor, extractor, classifier, engine
    
    @classmethod
    def list_frameworks(cls) -> Dict[str, List[str]]:
        """List all registered frameworks and their components."""
        return {
            "preprocessors": list(cls._preprocessors.keys()),
            "feature_extractors": list(cls._feature_extractors.keys()),
            "classifiers": list(cls._classifiers.keys()),
            "inference_engines": list(cls._inference_engines.keys()),
        }
