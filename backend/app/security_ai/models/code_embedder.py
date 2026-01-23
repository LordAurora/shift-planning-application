"""
Code Embedder

Generates semantic embeddings for source code using transformer models.
Used as input for vulnerability detection and severity classification.

Supports:
- Multiple programming languages
- Code structure awareness
- Semantic similarity computation
"""

import logging
from typing import List, Optional, Dict, Any
import numpy as np

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

from ..config import SecurityAIConfig, get_config

logger = logging.getLogger(__name__)


class CodeEmbedder:
    """
    Code embedding model for semantic code representation.
    
    Uses a transformer encoder to generate fixed-size embeddings
    from variable-length code snippets.
    
    Example:
        embedder = CodeEmbedder()
        embedding = embedder.embed("def hello(): print('world')", language="python")
        similarity = embedder.compute_similarity(embedding1, embedding2)
    """
    
    # Language-specific tokens
    LANGUAGE_TOKENS = {
        "python": "<PYTHON>",
        "javascript": "<JAVASCRIPT>",
        "typescript": "<TYPESCRIPT>",
        "java": "<JAVA>",
        "go": "<GO>",
        "rust": "<RUST>",
        "c": "<C>",
        "cpp": "<CPP>",
    }
    
    def __init__(self, config: Optional[SecurityAIConfig] = None):
        """Initialize code embedder."""
        self.config = config or get_config()
        self.embedding_dim = self.config.vulnerability_detector.embedding_dim
        self.model = None
        self._vocab: Dict[str, int] = {}
        self._build_vocab()
    
    def _build_vocab(self) -> None:
        """Build basic vocabulary for tokenization."""
        # Special tokens
        special_tokens = ["<PAD>", "<UNK>", "<CLS>", "<SEP>", "<MASK>"]
        special_tokens.extend(self.LANGUAGE_TOKENS.values())
        
        # Common code tokens
        code_tokens = [
            "def", "class", "function", "return", "if", "else", "elif",
            "for", "while", "try", "except", "catch", "throw", "import",
            "from", "as", "in", "not", "and", "or", "True", "False", "None",
            "null", "undefined", "const", "let", "var", "async", "await",
            "public", "private", "protected", "static", "final", "override",
            "(", ")", "{", "}", "[", "]", ":", ";", ",", ".", "=", "==",
            "!=", "<", ">", "<=", ">=", "+", "-", "*", "/", "%", "**",
            "->", "=>", "::", "...", "@", "#", "//", "/*", "*/",
        ]
        
        for i, token in enumerate(special_tokens + code_tokens):
            self._vocab[token] = i
    
    def build_model(self) -> Any:
        """Build embedding model."""
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow not available")
        
        cfg = self.config.vulnerability_detector
        
        # Input
        inputs = keras.Input(shape=(cfg.max_sequence_length,), dtype=tf.int32)
        
        # Embedding layer
        x = layers.Embedding(
            input_dim=cfg.vocab_size,
            output_dim=self.embedding_dim
        )(inputs)
        
        # Transformer encoder (simplified)
        for _ in range(2):
            attention = layers.MultiHeadAttention(
                num_heads=4,
                key_dim=self.embedding_dim // 4
            )(x, x)
            x = layers.LayerNormalization()(x + attention)
            
            ffn = layers.Dense(self.embedding_dim * 2, activation="gelu")(x)
            ffn = layers.Dense(self.embedding_dim)(ffn)
            x = layers.LayerNormalization()(x + ffn)
        
        # Pooling to fixed size
        x = layers.GlobalAveragePooling1D()(x)
        
        # Final embedding projection
        outputs = layers.Dense(self.embedding_dim, name="code_embedding")(x)
        
        model = keras.Model(inputs=inputs, outputs=outputs, name="code_embedder")
        return model
    
    def tokenize(self, code: str, language: str = "python") -> List[int]:
        """
        Tokenize code into integer sequence.
        
        Args:
            code: Source code string
            language: Programming language
        
        Returns:
            List of token IDs
        """
        tokens = []
        max_len = self.config.vulnerability_detector.max_sequence_length
        
        # Add language token
        lang_token = self.LANGUAGE_TOKENS.get(language, "<UNK>")
        tokens.append(self._vocab.get(lang_token, self._vocab.get("<UNK>", 1)))
        
        # Simple tokenization (would use proper tokenizer in production)
        words = code.replace('\n', ' ').replace('\t', ' ').split()
        
        for word in words[:max_len - 2]:
            if word in self._vocab:
                tokens.append(self._vocab[word])
            else:
                # Character-level fallback for unknown tokens
                for char in word:
                    tokens.append(ord(char) % (self.config.vulnerability_detector.vocab_size - len(self._vocab)))
        
        # Pad or truncate
        if len(tokens) < max_len:
            tokens.extend([0] * (max_len - len(tokens)))
        else:
            tokens = tokens[:max_len]
        
        return tokens
    
    def embed(self, code: str, language: str = "python") -> np.ndarray:
        """
        Generate embedding for code snippet.
        
        Args:
            code: Source code to embed
            language: Programming language
        
        Returns:
            Embedding vector of shape (embedding_dim,)
        """
        if self.model is None:
            # Return random embedding if model not loaded
            logger.warning("Model not loaded, returning random embedding")
            return np.random.randn(self.embedding_dim).astype(np.float32)
        
        tokens = self.tokenize(code, language)
        input_array = np.array([tokens])
        
        embedding = self.model.predict(input_array, verbose=0)[0]
        return embedding
    
    def embed_batch(
        self,
        codes: List[str],
        languages: Optional[List[str]] = None
    ) -> np.ndarray:
        """
        Generate embeddings for multiple code snippets.
        
        Args:
            codes: List of code strings
            languages: List of languages (defaults to python)
        
        Returns:
            Embeddings array of shape (batch_size, embedding_dim)
        """
        if languages is None:
            languages = ["python"] * len(codes)
        
        if self.model is None:
            return np.random.randn(len(codes), self.embedding_dim).astype(np.float32)
        
        tokens_batch = [self.tokenize(code, lang) for code, lang in zip(codes, languages)]
        input_array = np.array(tokens_batch)
        
        embeddings = self.model.predict(input_array, verbose=0)
        return embeddings
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        
        Returns:
            Similarity score in range [-1, 1]
        """
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(embedding1, embedding2) / (norm1 * norm2))
    
    def find_similar(
        self,
        query_embedding: np.ndarray,
        corpus_embeddings: np.ndarray,
        top_k: int = 5
    ) -> List[tuple]:
        """
        Find most similar embeddings in corpus.
        
        Args:
            query_embedding: Query embedding
            corpus_embeddings: Matrix of corpus embeddings
            top_k: Number of results to return
        
        Returns:
            List of (index, similarity_score) tuples
        """
        similarities = []
        
        for i, embedding in enumerate(corpus_embeddings):
            sim = self.compute_similarity(query_embedding, embedding)
            similarities.append((i, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def load_model(self, path: str) -> None:
        """Load model from checkpoint."""
        if TF_AVAILABLE:
            self.model = keras.models.load_model(path)
            logger.info(f"Code embedder loaded from {path}")
    
    def save_model(self, path: str) -> None:
        """Save model to disk."""
        if self.model is not None and TF_AVAILABLE:
            self.model.save(path)
            logger.info(f"Code embedder saved to {path}")
