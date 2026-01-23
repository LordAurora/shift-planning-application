# ML Architecture for Security Vulnerability Detection

## Executive Summary

This document describes a **modular, framework-agnostic ML architecture** for detecting and classifying security vulnerabilities in source code. The architecture is designed for:

1. **Phase 1**: Local TensorFlow training and inference
2. **Phase 2**: Migration to Huawei Cloud ModelArts with MindSpore/Ascend NPU

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INFERENCE PIPELINE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐   │
│  │             │    │                  │    │                 │   │
│  │ Preprocessor├───►│ Feature Extractor├───►│   Classifier    │   │
│  │             │    │                  │    │                 │   │
│  └─────────────┘    └────────┬─────────┘    └────────┬────────┘   │
│        │                     │                       │             │
│        │                     ▼                       ▼             │
│        │           ┌─────────────────┐     ┌────────────────┐     │
│        │           │   Attention     │     │  Predictions   │     │
│        │           │   Weights       │     │  (Multi-label) │     │
│        │           └────────┬────────┘     └───────┬────────┘     │
│        │                    │                      │               │
│        │                    ▼                      │               │
│        │           ┌────────────────────┐         │               │
│        └──────────►│  Explainability    │◄────────┘               │
│                    │  Module            │                          │
│                    └────────┬───────────┘                          │
│                             │                                      │
│                             ▼                                      │
│                    ┌────────────────────┐                          │
│                    │ Human-Readable     │                          │
│                    │ Explanation        │                          │
│                    └────────────────────┘                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

| Component | Interface | Responsibility | Framework-Agnostic? |
|-----------|-----------|----------------|---------------------|
| **Preprocessor** | `Preprocessor` | Code tokenization, vocabulary management, sequence encoding | ✅ Pure Python/NumPy |
| **Feature Extractor** | `FeatureExtractor` | Transformer encoding, attention computation | ❌ Framework-specific |
| **Classifier** | `Classifier` | Multi-label vulnerability prediction | ❌ Framework-specific |
| **Inference Engine** | `InferenceEngine` | Pipeline orchestration, batch processing | ✅ Wraps framework code |
| **Explainability** | `ExplainabilityModule` | Attention rollout, token importance, reasoning | ✅ Pure NumPy |
| **Model Registry** | `ModelRegistry` | Framework switching at runtime | ✅ Pure Python |

---

## Design Rationale

### 1. Why Transformer Architecture?

**Problem**: Code has both local patterns (variable names, operators) and long-range dependencies (function calls, control flow).

**Solution**: Self-attention mechanism naturally captures:
- Local patterns through positional encoding
- Long-range dependencies through global attention
- Contextual meaning through multi-head attention

**Evidence**: CodeBERT, GraphCodeBERT, and other code models demonstrate transformer superiority for code understanding tasks.

### 2. Why Multi-Head Attention?

```python
# Single attention: one "perspective"
attention = softmax(Q @ K.T) @ V

# Multi-head: multiple perspectives combined
head_1 = softmax(Q_1 @ K_1.T) @ V_1  # syntactic patterns
head_2 = softmax(Q_2 @ K_2.T) @ V_2  # semantic patterns
head_3 = softmax(Q_3 @ K_3.T) @ V_3  # vulnerability patterns
...
output = Concat(head_1, ..., head_n) @ W_o
```

Security vulnerabilities have multiple dimensions:
- **Syntactic**: SQL concatenation patterns
- **Semantic**: Untrusted data flow
- **Contextual**: Missing validation

Multi-head attention (8 heads by default) allows the model to learn specialized attention patterns for each dimension.

### 3. Why Explicit Attention Implementation?

**Problem**: `keras.MultiHeadAttention` is a black-box that doesn't return intermediate attention weights easily.

**Solution**: Explicit implementation with separate Q, K, V projections:

```python
# Explicit (our implementation)
Q = self.query_dense(x)
K = self.key_dense(x)
V = self.value_dense(x)
attention_weights = softmax(Q @ K.T / sqrt(d_k))  # ← Accessible!
output = attention_weights @ V
```

**Benefits**:
1. **Explainability**: Direct access to attention weights for each head and layer
2. **MindSpore Compatibility**: Maps directly to MindSpore's `nn.Dense` and `ops.MatMul`
3. **Customization**: Easy to add relative position encoding, sparse attention, etc.

### 4. Why GELU Activation?

```python
# ReLU: Sharp cutoff at 0
relu(x) = max(0, x)

# GELU: Smooth probabilistic masking
gelu(x) = x * Φ(x)  # Φ = Gaussian CDF
```

**Advantages for security analysis**:
1. **Gradient preservation**: No dead neurons for edge cases
2. **Smooth decision boundary**: Better for subtle vulnerability patterns
3. **Framework support**: Both TensorFlow (`tf.nn.gelu`) and MindSpore (`nn.GELU`)

### 5. Why Multi-Label Classification?

**Problem**: A single code snippet can have multiple vulnerabilities:

```python
def process(user_input):
    query = f"SELECT * FROM users WHERE id = {user_input}"  # SQL Injection
    password = "admin123"  # Hardcoded Credentials
    exec(user_input)  # Code Injection
```

**Solution**: Sigmoid output with independent probability for each class:

```
Output: [0.95, 0.87, 0.92, 0.12, ...]
        │     │     │     │
        SQL   Cred  Code  XSS
        Inj   Exp   Inj   ✗
```

**Alternative (rejected)**: Softmax forces single class, missing co-occurring vulnerabilities.

### 6. Why Attention Rollout for Explainability?

**Problem**: Deep transformers have multiple attention layers. Raw attention from the last layer doesn't show the full picture.

**Solution**: Attention rollout combines attention across all layers:

```python
def attention_rollout(attention_weights_per_layer):
    # attention_weights_per_layer: [layer_1, layer_2, ..., layer_n]
    # Each layer: [batch, heads, seq, seq]
    
    # Average across heads
    rollout = np.mean(attention_weights_per_layer[0], axis=1)
    
    # Add residual connection (identity)
    rollout = 0.5 * rollout + 0.5 * np.eye(seq_len)
    
    # Propagate through layers
    for layer_attention in attention_weights_per_layer[1:]:
        layer_avg = np.mean(layer_attention, axis=1)
        layer_avg = 0.5 * layer_avg + 0.5 * np.eye(seq_len)
        rollout = layer_avg @ rollout  # Matrix multiplication
    
    # Return attention from [CLS] to all tokens
    return rollout[:, 0, :]
```

This gives a global view of which tokens contributed to the final classification.

---

## Framework-Agnostic Design Principles

### Principle 1: Abstract Interfaces

```python
# Define behavior, not implementation
class FeatureExtractor(ABC):
    @abstractmethod
    def extract(self, token_ids: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        pass

# TensorFlow implementation
class TensorFlowFeatureExtractor(FeatureExtractor):
    def extract(self, token_ids):
        return self.model(token_ids)  # TF operations

# MindSpore implementation
class MindSporeFeatureExtractor(FeatureExtractor):
    def extract(self, token_ids):
        return self.model(Tensor(token_ids))  # MS operations
```

### Principle 2: NumPy as Lingua Franca

All data exchange uses NumPy arrays:
- Input: `np.ndarray` (from preprocessor)
- Output: `np.ndarray` (to downstream components)
- Conversion happens inside framework-specific code

### Principle 3: ModelRegistry for Runtime Switching

```python
# Configuration-driven framework selection
config = ModelConfig(framework="tensorflow")  # or "mindspore"

# Runtime instantiation
extractor_cls = ModelRegistry.get_feature_extractor(config.framework)
extractor = extractor_cls(config)
```

### Principle 4: Avoid Framework-Specific Operations

| Avoid (TF-only) | Use Instead |
|-----------------|-------------|
| `tf.py_function` | Pure Python preprocessing |
| `keras.MultiHeadAttention` | Explicit Q/K/V with Dense |
| `tf.einsum` (complex) | Standard MatMul operations |
| `tf.data.Dataset` in model | NumPy arrays as input |

---

## MindSpore Migration Guide

### Step 1: Weight Transfer

```
TensorFlow Layer         →    MindSpore Layer
────────────────────────────────────────────────
Dense.kernel (shape [in, out])  →  Dense.weight (shape [out, in]) + TRANSPOSE
Dense.bias                      →  Dense.bias (direct copy)
Embedding.embeddings            →  Embedding.embedding_table
LayerNorm.gamma                 →  LayerNorm.gamma
LayerNorm.beta                  →  LayerNorm.beta
```

### Step 2: Operator Mapping

```python
# TensorFlow                     # MindSpore
tf.matmul(A, B)                  ops.BatchMatMul()(A, B)
tf.transpose(x, [0, 2, 1, 3])    ops.Transpose()(x, (0, 2, 1, 3))
tf.nn.softmax(x, axis=-1)        ops.Softmax(axis=-1)(x)
tf.nn.gelu(x)                    nn.GELU()(x)
tf.keras.layers.Dense            nn.Dense
tf.keras.layers.Embedding        nn.Embedding
tf.keras.layers.LayerNormalization  nn.LayerNorm
```

### Step 3: Training Loop

```python
# TensorFlow
model.fit(x, y, epochs=10)

# MindSpore
from mindspore import Model
from mindspore.nn import Adam, SoftmaxCrossEntropyWithLogits

optimizer = Adam(model.trainable_params(), learning_rate=1e-4)
loss_fn = nn.BCELoss()  # For multi-label

ms_model = Model(network=model, loss_fn=loss_fn, optimizer=optimizer)
ms_model.train(epoch=10, train_dataset=dataset)
```

---

## Ascend NPU Considerations

### Memory Budget (Ascend 910)

| Component | Memory (fp32) | Memory (fp16) |
|-----------|---------------|---------------|
| Embeddings (50k × 256) | 51 MB | 26 MB |
| Transformer (4 layers) | ~200 MB | ~100 MB |
| Classifier | ~10 MB | ~5 MB |
| **Total** | ~261 MB | ~131 MB |

Ascend 910 has 32 GB HBM → ample headroom for batch processing.

### Operator Optimization

```python
# Prefer fused operations
# Instead of: LayerNorm(Dropout(GELU(Dense(x))))
# Use: Ascend automatically fuses when in GRAPH_MODE

ms.set_context(mode=ms.GRAPH_MODE, device_target="Ascend")
```

### Recommended Batch Sizes

| Hardware | Training Batch | Inference Batch |
|----------|----------------|-----------------|
| Ascend 910 | 32-64 | 64-128 |
| Ascend 310 | N/A | 8-16 |
| V100 (baseline) | 16-32 | 32-64 |

---

## Vulnerability Classes

The model classifies 15 vulnerability types aligned with CWE/OWASP:

| Index | Class | CWE | OWASP Top 10 |
|-------|-------|-----|--------------|
| 0 | SQL Injection | CWE-89 | A03:2021 |
| 1 | XSS | CWE-79 | A03:2021 |
| 2 | Command Injection | CWE-78 | A03:2021 |
| 3 | Path Traversal | CWE-22 | A01:2021 |
| 4 | Code Injection | CWE-94 | A03:2021 |
| 5 | SSRF | CWE-918 | A10:2021 |
| 6 | XXE | CWE-611 | A05:2021 |
| 7 | Insecure Deserialization | CWE-502 | A08:2021 |
| 8 | Hardcoded Credentials | CWE-798 | A07:2021 |
| 9 | Weak Cryptography | CWE-327 | A02:2021 |
| 10 | Buffer Overflow | CWE-120 | A06:2021 |
| 11 | Race Condition | CWE-362 | A04:2021 |
| 12 | Improper Auth | CWE-287 | A07:2021 |
| 13 | Sensitive Data Exposure | CWE-200 | A02:2021 |
| 14 | Insecure Configuration | CWE-1188 | A05:2021 |

---

## File Structure

```
security_ai/architecture/
├── __init__.py           # Abstract interfaces, ExplainabilityModule, ModelRegistry
├── tensorflow_impl.py    # TensorFlow implementations (Phase 1)
├── mindspore_stub.py     # MindSpore stubs + migration guide (Phase 2)
└── ARCHITECTURE.md       # This document
```

---

## API Reference

### ModelConfig

```python
@dataclass
class ModelConfig:
    max_seq_length: int = 512
    vocab_size: int = 50000
    embedding_dim: int = 256
    num_heads: int = 8
    num_encoder_layers: int = 4
    ff_dim: int = 1024
    dropout_rate: float = 0.1
    num_classes: int = 15
```

### Preprocessor

```python
class Preprocessor(ABC):
    def tokenize(self, text: str) -> List[str]: ...
    def encode(self, tokens: List[str], max_length: int) -> np.ndarray: ...
    def decode(self, token_ids: np.ndarray) -> List[str]: ...
    def build_vocab(self, texts: List[str], vocab_size: int) -> Dict: ...
    def save(self, path: str) -> None: ...
    def load(self, path: str) -> None: ...
```

### FeatureExtractor

```python
class FeatureExtractor(ABC):
    def extract(
        self,
        token_ids: np.ndarray,
        return_attention: bool = False
    ) -> Tuple[np.ndarray, Optional[np.ndarray]]: ...
```

### Classifier

```python
class Classifier(ABC):
    def predict(self, features: np.ndarray) -> np.ndarray: ...
    def predict_labels(self, features: np.ndarray, threshold: float) -> np.ndarray: ...
```

### InferenceEngine

```python
class InferenceEngine(ABC):
    def predict(
        self,
        text: Union[str, List[str]],
        return_explanation: bool = False
    ) -> Dict[str, Any]: ...
    
    def explain(
        self,
        text: str,
        target_class: Optional[int] = None
    ) -> Dict[str, Any]: ...
    
    def batch_predict(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[Dict[str, Any]]: ...
```

---

## Usage Example

```python
from security_ai.architecture import ModelConfig, ModelRegistry
from security_ai.architecture.tensorflow_impl import CodePreprocessor

# Initialize
config = ModelConfig()
preprocessor = CodePreprocessor(config)

# Get framework-specific implementations
extractor = ModelRegistry.get_feature_extractor("tensorflow")(config)
classifier = ModelRegistry.get_classifier("tensorflow")(config)
engine = ModelRegistry.get_inference_engine("tensorflow")(
    preprocessor, extractor, classifier, config
)

# Inference
result = engine.predict("""
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}'"
    return db.execute(query)
""", return_explanation=True)

# Output
# {
#   "predictions": {
#     "sql_injection": {"probability": 0.95, "detected": True},
#     ...
#   },
#   "explanation": {
#     "important_tokens": [("SELECT", 0.23), ("username", 0.18), ...],
#     "reasoning": "High attention on 'SELECT' and 'username' suggests SQL query..."
#   }
# }
```

---

## Future Enhancements

1. **Pre-trained Code Models**: Initialize from CodeBERT/GraphCodeBERT
2. **Relative Position Encoding**: Better for variable-length code
3. **Sparse Attention**: Handle longer code files (>2048 tokens)
4. **Contrastive Learning**: Learn vulnerability vs. safe code representations
5. **Graph Neural Networks**: Incorporate AST/CFG structure

---

## References

1. Vaswani, A., et al. "Attention Is All You Need" (2017)
2. Feng, Z., et al. "CodeBERT: A Pre-Trained Model for Programming and Natural Languages" (2020)
3. OWASP Top 10 - 2021
4. MITRE CWE Top 25 - 2023
5. MindSpore Documentation - https://www.mindspore.cn/
6. Huawei Ascend Documentation - https://www.hiascend.com/
