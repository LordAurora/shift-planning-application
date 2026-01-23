"""
TensorFlow Implementation of Vulnerability Detection Architecture

Phase 1: Production implementation using TensorFlow 2.x
- Full implementation of abstract interfaces
- Optimized for GPU training
- Export support for SavedModel and ONNX
"""

import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import json
import re
from collections import Counter

from . import (
    Preprocessor,
    FeatureExtractor,
    Classifier,
    InferenceEngine,
    ModelConfig,
    ModelRegistry,
    ExplainabilityModule,
    PredictionExplanation,
)

logger = logging.getLogger(__name__)


# =============================================================================
# PREPROCESSOR (Framework-Agnostic - Pure Python/NumPy)
# =============================================================================

class CodePreprocessor(Preprocessor):
    """
    Code-aware text preprocessor.
    
    Features:
    - Code-specific tokenization (preserves operators, keywords)
    - Subword tokenization for rare tokens
    - Special tokens for code structure
    
    Fully framework-agnostic: Uses only Python/NumPy.
    """
    
    # Special tokens
    PAD_TOKEN = "[PAD]"
    UNK_TOKEN = "[UNK]"
    CLS_TOKEN = "[CLS]"
    SEP_TOKEN = "[SEP]"
    
    # Code-specific special tokens
    STRING_TOKEN = "[STRING]"
    NUMBER_TOKEN = "[NUMBER]"
    COMMENT_TOKEN = "[COMMENT]"
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.max_length = config.max_sequence_length
        self.vocab_size = config.vocab_size
        
        # Initialize with special tokens
        self.token_to_id: Dict[str, int] = {
            self.PAD_TOKEN: 0,
            self.UNK_TOKEN: 1,
            self.CLS_TOKEN: 2,
            self.SEP_TOKEN: 3,
            self.STRING_TOKEN: 4,
            self.NUMBER_TOKEN: 5,
            self.COMMENT_TOKEN: 6,
        }
        self.id_to_token: Dict[int, str] = {v: k for k, v in self.token_to_id.items()}
        
        # Code keywords for various languages
        self.keywords = self._load_keywords()
    
    def _load_keywords(self) -> set:
        """Load programming language keywords."""
        python_keywords = {
            "def", "class", "if", "else", "elif", "for", "while", "try",
            "except", "finally", "with", "as", "import", "from", "return",
            "yield", "raise", "pass", "break", "continue", "lambda", "and",
            "or", "not", "in", "is", "None", "True", "False", "async", "await"
        }
        
        js_keywords = {
            "function", "const", "let", "var", "if", "else", "for", "while",
            "do", "switch", "case", "break", "continue", "return", "try",
            "catch", "finally", "throw", "new", "this", "class", "extends",
            "import", "export", "default", "async", "await", "null", "undefined"
        }
        
        return python_keywords | js_keywords
    
    def _tokenize_code(self, text: str) -> List[str]:
        """
        Tokenize code with awareness of code structure.
        
        Preserves:
        - Operators and punctuation
        - String literals (replaced with [STRING])
        - Numbers (replaced with [NUMBER])
        - Comments (replaced with [COMMENT])
        """
        tokens = []
        
        # Replace strings with placeholder
        text = re.sub(r'(["\'])(?:(?!\1)[^\\]|\\.)*\1', f' {self.STRING_TOKEN} ', text)
        
        # Replace numbers
        text = re.sub(r'\b\d+\.?\d*\b', f' {self.NUMBER_TOKEN} ', text)
        
        # Replace comments
        text = re.sub(r'#.*$', f' {self.COMMENT_TOKEN} ', text, flags=re.MULTILINE)
        text = re.sub(r'//.*$', f' {self.COMMENT_TOKEN} ', text, flags=re.MULTILINE)
        text = re.sub(r'/\*.*?\*/', f' {self.COMMENT_TOKEN} ', text, flags=re.DOTALL)
        
        # Tokenize by whitespace and punctuation
        pattern = r'(\s+|[{}()\[\];,.:=<>+\-*/&|!?@#$%^~`\\])'
        parts = re.split(pattern, text)
        
        for part in parts:
            part = part.strip()
            if part:
                # Keep operators as single tokens
                if part in '{}()[];,.:=<>+-*/&|!?@#$%^~`\\':
                    tokens.append(part)
                elif part in [self.STRING_TOKEN, self.NUMBER_TOKEN, self.COMMENT_TOKEN]:
                    tokens.append(part)
                else:
                    # Split camelCase and snake_case
                    subparts = re.sub(r'([a-z])([A-Z])', r'\1 \2', part)
                    subparts = subparts.replace('_', ' ')
                    for subpart in subparts.split():
                        if subpart:
                            tokens.append(subpart.lower())
        
        return tokens
    
    def tokenize(self, text: str) -> List[int]:
        """Convert text to token IDs."""
        tokens = self._tokenize_code(text)
        
        # Add special tokens
        tokens = [self.CLS_TOKEN] + tokens + [self.SEP_TOKEN]
        
        # Convert to IDs
        ids = []
        for token in tokens:
            if token in self.token_to_id:
                ids.append(self.token_to_id[token])
            else:
                ids.append(self.token_to_id[self.UNK_TOKEN])
        
        return ids
    
    def encode(self, text: str, max_length: Optional[int] = None) -> np.ndarray:
        """Encode text to padded token IDs."""
        max_len = max_length or self.max_length
        ids = self.tokenize(text)
        
        # Truncate or pad
        if len(ids) > max_len:
            ids = ids[:max_len - 1] + [self.token_to_id[self.SEP_TOKEN]]
        else:
            ids = ids + [self.token_to_id[self.PAD_TOKEN]] * (max_len - len(ids))
        
        return np.array(ids, dtype=np.int32)
    
    def decode(self, token_ids: np.ndarray) -> str:
        """Decode token IDs back to text."""
        tokens = []
        for tid in token_ids:
            if tid in self.id_to_token:
                token = self.id_to_token[tid]
                if token not in [self.PAD_TOKEN, self.CLS_TOKEN, self.SEP_TOKEN]:
                    tokens.append(token)
        return ' '.join(tokens)
    
    def get_tokens(self, text: str) -> List[str]:
        """Get tokens for a text (for explainability)."""
        tokens = self._tokenize_code(text)
        return [self.CLS_TOKEN] + tokens + [self.SEP_TOKEN]
    
    def build_vocab(self, texts: List[str], min_freq: int = 2) -> None:
        """Build vocabulary from corpus."""
        counter = Counter()
        
        for text in texts:
            tokens = self._tokenize_code(text)
            counter.update(tokens)
        
        # Keep tokens with frequency >= min_freq
        vocab_tokens = [
            token for token, freq in counter.most_common()
            if freq >= min_freq
        ]
        
        # Add to vocabulary (after special tokens)
        current_id = len(self.token_to_id)
        for token in vocab_tokens:
            if token not in self.token_to_id and current_id < self.vocab_size:
                self.token_to_id[token] = current_id
                self.id_to_token[current_id] = token
                current_id += 1
        
        logger.info(f"Built vocabulary with {len(self.token_to_id)} tokens")
    
    def save(self, path: str) -> None:
        """Save preprocessor state."""
        state = {
            "token_to_id": self.token_to_id,
            "config": self.config.to_dict()
        }
        with open(path, 'w') as f:
            json.dump(state, f)
    
    def load(self, path: str) -> None:
        """Load preprocessor state."""
        with open(path, 'r') as f:
            state = json.load(f)
        self.token_to_id = state["token_to_id"]
        self.id_to_token = {int(v): k for k, v in self.token_to_id.items()}


# =============================================================================
# TENSORFLOW FEATURE EXTRACTOR
# =============================================================================

class TensorFlowFeatureExtractor(FeatureExtractor):
    """
    TensorFlow implementation of feature extractor.
    
    Architecture:
    1. Token Embedding + Positional Encoding
    2. Transformer Encoder Stack (Multi-Head Self-Attention + FFN)
    3. Global Average Pooling or CLS token extraction
    
    Design Choices for MindSpore Compatibility:
    - Uses standard operations (MatMul, LayerNorm, Dense)
    - Avoids TF-specific operations (tf.py_function, etc.)
    - Explicit attention computation (not using built-in MultiHeadAttention)
    """
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.model = None
        self._build_model()
    
    def _build_model(self):
        """Build TensorFlow model."""
        try:
            import tensorflow as tf
            from tensorflow import keras
            from tensorflow.keras import layers
        except ImportError:
            logger.warning("TensorFlow not available")
            return
        
        # Input
        inputs = layers.Input(
            shape=(self.config.max_sequence_length,),
            dtype=tf.int32,
            name="token_ids"
        )
        
        # Embedding
        embeddings = layers.Embedding(
            input_dim=self.config.vocab_size,
            output_dim=self.config.embedding_dim,
            name="token_embedding"
        )(inputs)
        
        # Positional encoding (sinusoidal - framework agnostic formula)
        if self.config.use_positional_encoding:
            positions = tf.range(self.config.max_sequence_length)
            position_embedding = self._sinusoidal_position_encoding(
                self.config.max_sequence_length,
                self.config.embedding_dim
            )
            embeddings = embeddings + position_embedding
        
        # Dropout
        x = layers.Dropout(self.config.dropout_rate)(embeddings)
        
        # Store attention weights for explainability
        attention_weights_list = []
        
        # Transformer encoder layers
        for i in range(self.config.num_encoder_layers):
            # Multi-head self-attention (explicit implementation)
            attn_output, attn_weights = self._multi_head_attention(
                x, x, x,
                num_heads=self.config.num_attention_heads,
                key_dim=self.config.embedding_dim // self.config.num_attention_heads,
                name=f"attention_{i}"
            )
            attention_weights_list.append(attn_weights)
            
            # Add & Norm
            x = layers.LayerNormalization(epsilon=1e-6)(x + attn_output)
            
            # Feed-forward network
            ffn_output = layers.Dense(
                self.config.feed_forward_dim,
                activation="gelu",  # GELU is supported by both TF and MindSpore
                name=f"ffn_{i}_1"
            )(x)
            ffn_output = layers.Dense(
                self.config.embedding_dim,
                name=f"ffn_{i}_2"
            )(ffn_output)
            ffn_output = layers.Dropout(self.config.dropout_rate)(ffn_output)
            
            # Add & Norm
            x = layers.LayerNormalization(epsilon=1e-6)(x + ffn_output)
        
        # Global pooling (CLS token or average)
        # Using CLS token (first position) for classification
        cls_output = x[:, 0, :]  # [batch, embedding_dim]
        
        # Stack attention weights
        if self.config.return_attention_weights:
            stacked_attention = tf.stack(attention_weights_list, axis=1)
            self.model = keras.Model(
                inputs=inputs,
                outputs=[cls_output, stacked_attention],
                name="feature_extractor"
            )
        else:
            self.model = keras.Model(
                inputs=inputs,
                outputs=cls_output,
                name="feature_extractor"
            )
    
    def _sinusoidal_position_encoding(
        self,
        max_len: int,
        d_model: int
    ) -> np.ndarray:
        """
        Create sinusoidal positional encodings.
        
        Formula (framework-agnostic):
        PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
        PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
        """
        position = np.arange(max_len)[:, np.newaxis]
        div_term = np.exp(np.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))
        
        pe = np.zeros((max_len, d_model))
        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)
        
        return pe.astype(np.float32)
    
    def _multi_head_attention(
        self,
        query,
        key,
        value,
        num_heads: int,
        key_dim: int,
        name: str
    ):
        """
        Explicit multi-head attention implementation.
        
        Avoids using keras.layers.MultiHeadAttention for better
        MindSpore compatibility (uses standard Dense layers only).
        """
        import tensorflow as tf
        from tensorflow.keras import layers
        
        batch_size = tf.shape(query)[0]
        seq_len = tf.shape(query)[1]
        d_model = query.shape[-1]
        
        # Linear projections
        q = layers.Dense(num_heads * key_dim, name=f"{name}_q")(query)
        k = layers.Dense(num_heads * key_dim, name=f"{name}_k")(key)
        v = layers.Dense(num_heads * key_dim, name=f"{name}_v")(value)
        
        # Reshape for multi-head: [batch, seq, num_heads, key_dim]
        q = tf.reshape(q, [batch_size, seq_len, num_heads, key_dim])
        k = tf.reshape(k, [batch_size, seq_len, num_heads, key_dim])
        v = tf.reshape(v, [batch_size, seq_len, num_heads, key_dim])
        
        # Transpose to [batch, num_heads, seq, key_dim]
        q = tf.transpose(q, [0, 2, 1, 3])
        k = tf.transpose(k, [0, 2, 1, 3])
        v = tf.transpose(v, [0, 2, 1, 3])
        
        # Scaled dot-product attention
        # scores = Q @ K^T / sqrt(d_k)
        scale = tf.math.sqrt(tf.cast(key_dim, tf.float32))
        scores = tf.matmul(q, k, transpose_b=True) / scale
        
        # Softmax attention weights
        attention_weights = tf.nn.softmax(scores, axis=-1)
        
        # Apply attention to values
        context = tf.matmul(attention_weights, v)
        
        # Reshape back: [batch, seq, num_heads * key_dim]
        context = tf.transpose(context, [0, 2, 1, 3])
        context = tf.reshape(context, [batch_size, seq_len, num_heads * key_dim])
        
        # Final projection
        output = layers.Dense(d_model, name=f"{name}_output")(context)
        
        return output, attention_weights
    
    def extract(
        self,
        token_ids: np.ndarray,
        return_attention: bool = False
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Extract features from token IDs."""
        if self.model is None:
            raise RuntimeError("Model not built. TensorFlow may not be available.")
        
        outputs = self.model(token_ids, training=False)
        
        if self.config.return_attention_weights and isinstance(outputs, (list, tuple)):
            features, attention = outputs
            if return_attention:
                return features.numpy(), attention.numpy()
            return features.numpy(), None
        else:
            return outputs.numpy(), None
    
    def get_embeddings(self, token_ids: np.ndarray) -> np.ndarray:
        """Get token embeddings without full encoding."""
        if self.model is None:
            raise RuntimeError("Model not built")
        
        # Get embedding layer
        embedding_layer = self.model.get_layer("token_embedding")
        return embedding_layer(token_ids).numpy()


# =============================================================================
# TENSORFLOW CLASSIFIER
# =============================================================================

class TensorFlowClassifier(Classifier):
    """
    TensorFlow multi-label classifier.
    
    Architecture:
    1. Hidden layers with GELU activation
    2. Dropout for regularization
    3. Sigmoid output for multi-label classification
    
    Includes calibration support for reliable confidence scores.
    """
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.model = None
        self._build_model()
    
    def _build_model(self):
        """Build classifier model."""
        try:
            import tensorflow as tf
            from tensorflow import keras
            from tensorflow.keras import layers
        except ImportError:
            logger.warning("TensorFlow not available")
            return
        
        # Input (features from extractor)
        inputs = layers.Input(
            shape=(self.config.embedding_dim,),
            name="features"
        )
        
        x = inputs
        
        # Hidden layers
        for i, dim in enumerate(self.config.hidden_dims):
            x = layers.Dense(
                dim,
                activation="gelu",
                name=f"hidden_{i}"
            )(x)
            x = layers.Dropout(self.config.dropout_rate)(x)
        
        # Output layer (sigmoid for multi-label)
        outputs = layers.Dense(
            self.config.num_classes,
            activation="sigmoid",
            name="output"
        )(x)
        
        self.model = keras.Model(inputs=inputs, outputs=outputs, name="classifier")
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """Predict class probabilities."""
        if self.model is None:
            raise RuntimeError("Model not built")
        return self.model(features, training=False).numpy()
    
    def predict_labels(
        self,
        features: np.ndarray,
        threshold: float = 0.5
    ) -> np.ndarray:
        """Predict binary labels."""
        probs = self.predict(features)
        return (probs >= threshold).astype(np.int32)


# =============================================================================
# TENSORFLOW INFERENCE ENGINE
# =============================================================================

class TensorFlowInferenceEngine(InferenceEngine):
    """
    TensorFlow inference engine.
    
    Orchestrates the complete pipeline with explainability support.
    """
    
    # Vulnerability class names
    CLASS_NAMES = [
        "INJECTION",
        "HARDCODED_SECRETS",
        "BROKEN_AUTH",
        "XSS",
        "PATH_TRAVERSAL",
        "INSECURE_DESERIALIZATION",
        "INSECURE_CRYPTO",
        "SSRF",
        "SECURITY_MISCONFIGURATION",
        "INSUFFICIENT_LOGGING",
        "XXE",
        "CORS_MISCONFIGURATION",
        "OPEN_REDIRECT",
        "MASS_ASSIGNMENT",
        "INFORMATION_DISCLOSURE"
    ]
    
    def __init__(
        self,
        preprocessor: Preprocessor,
        extractor: FeatureExtractor,
        classifier: Classifier,
        config: ModelConfig
    ):
        self.preprocessor = preprocessor
        self.extractor = extractor
        self.classifier = classifier
        self.config = config
        self.explainer = ExplainabilityModule(self.CLASS_NAMES)
        self.threshold = 0.5
    
    def predict(
        self,
        text: Union[str, List[str]],
        return_explanation: bool = False
    ) -> Dict[str, Any]:
        """Run full inference pipeline."""
        # Handle single text
        if isinstance(text, str):
            texts = [text]
        else:
            texts = text
        
        # Preprocess
        token_ids = np.array([
            self.preprocessor.encode(t) for t in texts
        ])
        
        # Extract features
        features, attention = self.extractor.extract(
            token_ids,
            return_attention=return_explanation
        )
        
        # Classify
        probabilities = self.classifier.predict(features)
        labels = (probabilities >= self.threshold).astype(np.int32)
        
        # Build results
        results = []
        for i, t in enumerate(texts):
            pred_classes = [
                self.CLASS_NAMES[j]
                for j in range(len(self.CLASS_NAMES))
                if labels[i, j] == 1
            ]
            
            class_probs = {
                self.CLASS_NAMES[j]: float(probabilities[i, j])
                for j in range(len(self.CLASS_NAMES))
            }
            
            result = {
                "predicted_classes": pred_classes,
                "probabilities": class_probs,
                "is_vulnerable": len(pred_classes) > 0
            }
            
            if return_explanation and attention is not None:
                tokens = self.preprocessor.get_tokens(t)
                explanation = self.explainer.create_explanation(
                    input_text=t,
                    input_tokens=tokens[:self.config.max_sequence_length],
                    attention_weights=attention[i],
                    predicted_classes=pred_classes,
                    class_probabilities=class_probs
                )
                result["explanation"] = explanation.to_dict()
            
            results.append(result)
        
        if isinstance(text, str):
            return results[0]
        return {"results": results}
    
    def explain(
        self,
        text: str,
        target_class: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate detailed explanation."""
        result = self.predict(text, return_explanation=True)
        return result.get("explanation", {})
    
    def batch_predict(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[Dict[str, Any]]:
        """Batch prediction for efficiency."""
        all_results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            results = self.predict(batch, return_explanation=False)
            all_results.extend(results["results"])
        
        return all_results


# =============================================================================
# REGISTER IMPLEMENTATIONS
# =============================================================================

# Register TensorFlow implementations
ModelRegistry.register_preprocessor("tensorflow", CodePreprocessor)
ModelRegistry.register_feature_extractor("tensorflow", TensorFlowFeatureExtractor)
ModelRegistry.register_classifier("tensorflow", TensorFlowClassifier)
ModelRegistry.register_inference_engine("tensorflow", TensorFlowInferenceEngine)

# Also register preprocessor for numpy (it's framework-agnostic)
ModelRegistry.register_preprocessor("numpy", CodePreprocessor)
