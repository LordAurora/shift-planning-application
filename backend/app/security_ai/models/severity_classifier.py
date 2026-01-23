"""
Severity Classifier Model

Multi-class classifier for determining vulnerability severity levels.
Works in conjunction with VulnerabilityDetector for fine-grained severity assessment.

Severity Levels:
- Critical: Immediate exploitation risk, direct impact on security
- High: Significant risk, should be addressed urgently
- Medium: Moderate risk, should be addressed in normal cycle
- Low: Minor risk, can be addressed when convenient
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import numpy as np

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

from ..config import (
    SecurityAIConfig,
    SeverityLevel,
    VulnerabilityCategory,
    MLFramework,
    get_config
)

logger = logging.getLogger(__name__)


@dataclass
class SeverityPrediction:
    """Severity classification result."""
    severity: SeverityLevel
    confidence: float
    probabilities: Dict[SeverityLevel, float]
    explanation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "confidence": self.confidence,
            "probabilities": {k.value: v for k, v in self.probabilities.items()},
            "explanation": self.explanation
        }


class SeverityClassifier:
    """
    Multi-class severity classifier.
    
    Features considered for classification:
    - Vulnerability category
    - Code context
    - Exploitation complexity
    - Impact scope
    - Authentication requirements
    
    Example:
        classifier = SeverityClassifier()
        result = classifier.classify(
            category=VulnerabilityCategory.INJECTION,
            code_snippet="cursor.execute(query + user_input)",
            context={"is_public_endpoint": True}
        )
        print(f"Severity: {result.severity.value} ({result.confidence:.2%})")
    """
    
    # Feature weights for rule-based classification
    CATEGORY_BASE_SEVERITY = {
        VulnerabilityCategory.INJECTION: SeverityLevel.CRITICAL,
        VulnerabilityCategory.HARDCODED_SECRETS: SeverityLevel.CRITICAL,
        VulnerabilityCategory.BROKEN_AUTH: SeverityLevel.CRITICAL,
        VulnerabilityCategory.SSRF: SeverityLevel.HIGH,
        VulnerabilityCategory.PATH_TRAVERSAL: SeverityLevel.HIGH,
        VulnerabilityCategory.INSECURE_DESERIALIZATION: SeverityLevel.HIGH,
        VulnerabilityCategory.BROKEN_ACCESS: SeverityLevel.HIGH,
        VulnerabilityCategory.XSS: SeverityLevel.MEDIUM,
        VulnerabilityCategory.MISCONFIG: SeverityLevel.MEDIUM,
        VulnerabilityCategory.SENSITIVE_DATA: SeverityLevel.MEDIUM,
        VulnerabilityCategory.INSECURE_CRYPTO: SeverityLevel.MEDIUM,
        VulnerabilityCategory.XXE: SeverityLevel.MEDIUM,
        VulnerabilityCategory.VULNERABLE_COMPONENTS: SeverityLevel.MEDIUM,
        VulnerabilityCategory.INSUFFICIENT_LOGGING: SeverityLevel.LOW,
        VulnerabilityCategory.RACE_CONDITION: SeverityLevel.MEDIUM,
    }
    
    # Context-based severity modifiers
    SEVERITY_MODIFIERS = {
        "is_public_endpoint": 1,  # Increase severity
        "is_authenticated": -1,   # Decrease severity
        "has_input_validation": -1,
        "in_production_code": 1,
        "in_test_code": -2,
        "uses_encryption": -1,
        "has_rate_limiting": -1,
    }
    
    def __init__(self, config: Optional[SecurityAIConfig] = None):
        """Initialize severity classifier."""
        self.config = config or get_config()
        self.model_config = self.config.severity_classifier
        self.model = None
        self._is_loaded = False
    
    def build_model(self) -> Any:
        """Build classification model."""
        if self.config.framework == MLFramework.TENSORFLOW:
            return self._build_tensorflow_model()
        else:
            raise NotImplementedError(f"Framework {self.config.framework} not supported")
    
    def _build_tensorflow_model(self):
        """Build TensorFlow classification model."""
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow not available")
        
        cfg = self.model_config
        num_categories = len(VulnerabilityCategory)
        num_context_features = len(self.SEVERITY_MODIFIERS)
        num_severity_levels = 4  # Critical, High, Medium, Low
        
        # Input: [category_embedding, context_features, code_embedding]
        category_input = keras.Input(shape=(num_categories,), name="category_input")
        context_input = keras.Input(shape=(num_context_features,), name="context_input")
        code_input = keras.Input(shape=(cfg.embedding_dim,), name="code_embedding")
        
        # Concatenate inputs
        x = layers.Concatenate()([category_input, context_input, code_input])
        
        # Dense layers
        x = layers.Dense(cfg.hidden_dim, activation="relu")(x)
        x = layers.Dropout(cfg.dropout_rate)(x)
        x = layers.Dense(cfg.hidden_dim // 2, activation="relu")(x)
        x = layers.Dropout(cfg.dropout_rate)(x)
        
        # Output: severity probabilities
        outputs = layers.Dense(num_severity_levels, activation="softmax", name="severity")(x)
        
        model = keras.Model(
            inputs=[category_input, context_input, code_input],
            outputs=outputs,
            name="severity_classifier"
        )
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=cfg.learning_rate),
            loss="categorical_crossentropy",
            metrics=["accuracy"]
        )
        
        return model
    
    def classify(
        self,
        category: VulnerabilityCategory,
        code_snippet: str,
        context: Optional[Dict[str, bool]] = None
    ) -> SeverityPrediction:
        """
        Classify vulnerability severity.
        
        Args:
            category: Vulnerability category
            code_snippet: Code containing the vulnerability
            context: Optional context flags
        
        Returns:
            SeverityPrediction with severity level and confidence
        """
        context = context or {}
        
        # Get base severity for category
        base_severity = self.CATEGORY_BASE_SEVERITY.get(category, SeverityLevel.MEDIUM)
        
        # Calculate severity modifier score
        modifier_score = 0
        for flag, modifier in self.SEVERITY_MODIFIERS.items():
            if context.get(flag, False):
                modifier_score += modifier
        
        # Adjust severity based on modifiers
        severity_order = [SeverityLevel.CRITICAL, SeverityLevel.HIGH, SeverityLevel.MEDIUM, SeverityLevel.LOW]
        base_index = severity_order.index(base_severity)
        
        # Apply modifier (negative makes more severe, positive makes less severe)
        adjusted_index = max(0, min(3, base_index - modifier_score))
        final_severity = severity_order[adjusted_index]
        
        # Calculate pseudo-probabilities
        probabilities = self._calculate_probabilities(adjusted_index)
        
        # Generate explanation
        explanation = self._generate_explanation(category, context, modifier_score)
        
        return SeverityPrediction(
            severity=final_severity,
            confidence=probabilities[final_severity],
            probabilities=probabilities,
            explanation=explanation
        )
    
    def _calculate_probabilities(self, severity_index: int) -> Dict[SeverityLevel, float]:
        """Calculate probability distribution around the predicted severity."""
        severity_order = [SeverityLevel.CRITICAL, SeverityLevel.HIGH, SeverityLevel.MEDIUM, SeverityLevel.LOW]
        
        # Create probability distribution centered on predicted severity
        probs = [0.05, 0.05, 0.05, 0.05]
        probs[severity_index] = 0.85
        
        return {severity: prob for severity, prob in zip(severity_order, probs)}
    
    def _generate_explanation(
        self,
        category: VulnerabilityCategory,
        context: Dict[str, bool],
        modifier_score: int
    ) -> str:
        """Generate human-readable explanation for severity decision."""
        explanations = []
        
        explanations.append(f"Base severity for {category.value}: {self.CATEGORY_BASE_SEVERITY.get(category, SeverityLevel.MEDIUM).value}")
        
        if context:
            active_modifiers = [flag for flag, value in context.items() if value and flag in self.SEVERITY_MODIFIERS]
            if active_modifiers:
                explanations.append(f"Context factors: {', '.join(active_modifiers)}")
        
        if modifier_score != 0:
            direction = "increased" if modifier_score < 0 else "decreased"
            explanations.append(f"Severity {direction} based on context")
        
        return ". ".join(explanations)
    
    def classify_batch(
        self,
        items: List[Tuple[VulnerabilityCategory, str, Dict[str, bool]]]
    ) -> List[SeverityPrediction]:
        """Classify multiple vulnerabilities."""
        return [
            self.classify(category, snippet, context)
            for category, snippet, context in items
        ]
    
    def load_model(self, path: str) -> None:
        """Load model from checkpoint."""
        if self.config.framework == MLFramework.TENSORFLOW and TF_AVAILABLE:
            self.model = keras.models.load_model(path)
            self._is_loaded = True
            logger.info(f"Severity classifier loaded from {path}")
    
    def save_model(self, path: str) -> None:
        """Save model to disk."""
        if self.model is not None and TF_AVAILABLE:
            self.model.save(path)
            logger.info(f"Severity classifier saved to {path}")
