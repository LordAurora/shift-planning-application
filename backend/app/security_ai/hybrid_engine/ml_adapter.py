"""
ML Engine Adapter

Adapter layer connecting the ML architecture to the hybrid engine.
Provides a consistent interface for ML predictions with confidence scoring.
"""

import numpy as np
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# ML CONFIDENCE LEVELS
# =============================================================================

class MLConfidence(Enum):
    """
    ML prediction confidence levels.
    
    Mapped from raw probability scores:
    - VERY_HIGH: p >= 0.95 (model is very certain)
    - HIGH: 0.85 <= p < 0.95
    - MEDIUM: 0.70 <= p < 0.85
    - LOW: 0.50 <= p < 0.70 (uncertain)
    - VERY_LOW: p < 0.50 (likely negative)
    """
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"
    
    @classmethod
    def from_probability(cls, prob: float) -> "MLConfidence":
        """Convert probability to confidence level."""
        if prob >= 0.95:
            return cls.VERY_HIGH
        elif prob >= 0.85:
            return cls.HIGH
        elif prob >= 0.70:
            return cls.MEDIUM
        elif prob >= 0.50:
            return cls.LOW
        else:
            return cls.VERY_LOW
    
    @property
    def numeric_score(self) -> float:
        """Get numeric score for confidence level."""
        scores = {
            MLConfidence.VERY_HIGH: 0.95,
            MLConfidence.HIGH: 0.85,
            MLConfidence.MEDIUM: 0.70,
            MLConfidence.LOW: 0.50,
            MLConfidence.VERY_LOW: 0.25,
        }
        return scores[self]


# =============================================================================
# ML PREDICTION DATA STRUCTURES
# =============================================================================

@dataclass
class VulnerabilityPrediction:
    """Single vulnerability class prediction."""
    class_id: int
    class_name: str
    probability: float
    confidence: MLConfidence
    cwe_id: str
    
    # Explainability
    important_tokens: List[Tuple[str, float]] = field(default_factory=list)
    attention_pattern: Optional[str] = None  # Description of attention
    
    @property
    def is_positive(self) -> bool:
        """Whether this is a positive prediction (above threshold)."""
        return self.probability >= 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "probability": round(self.probability, 4),
            "confidence": self.confidence.value,
            "cwe_id": self.cwe_id,
            "is_detected": self.is_positive,
            "important_tokens": [
                {"token": t, "importance": round(s, 4)}
                for t, s in self.important_tokens[:10]
            ],
        }


@dataclass
class MLPrediction:
    """Complete ML prediction result."""
    predictions: List[VulnerabilityPrediction]
    overall_confidence: MLConfidence
    processing_time_ms: float
    model_version: str
    
    # Aggregated explainability
    top_important_tokens: List[Tuple[str, float]] = field(default_factory=list)
    reasoning: str = ""
    
    # Raw data for fusion
    raw_probabilities: Optional[np.ndarray] = None
    attention_weights: Optional[np.ndarray] = None
    
    @property
    def detected_vulnerabilities(self) -> List[VulnerabilityPrediction]:
        """Get only positive predictions."""
        return [p for p in self.predictions if p.is_positive]
    
    @property
    def has_vulnerabilities(self) -> bool:
        """Whether any vulnerability was detected."""
        return len(self.detected_vulnerabilities) > 0
    
    @property
    def max_probability(self) -> float:
        """Get highest probability among all predictions."""
        return max(p.probability for p in self.predictions) if self.predictions else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected_count": len(self.detected_vulnerabilities),
            "vulnerabilities": [p.to_dict() for p in self.detected_vulnerabilities],
            "all_predictions": [p.to_dict() for p in self.predictions],
            "overall_confidence": self.overall_confidence.value,
            "processing_time_ms": round(self.processing_time_ms, 2),
            "model_version": self.model_version,
            "top_important_tokens": [
                {"token": t, "importance": round(s, 4)}
                for t, s in self.top_important_tokens[:15]
            ],
            "reasoning": self.reasoning,
        }


# =============================================================================
# VULNERABILITY CLASS DEFINITIONS
# =============================================================================

VULNERABILITY_CLASSES = [
    {"id": 0, "name": "sql_injection", "cwe": "CWE-89"},
    {"id": 1, "name": "xss", "cwe": "CWE-79"},
    {"id": 2, "name": "command_injection", "cwe": "CWE-78"},
    {"id": 3, "name": "path_traversal", "cwe": "CWE-22"},
    {"id": 4, "name": "code_injection", "cwe": "CWE-94"},
    {"id": 5, "name": "ssrf", "cwe": "CWE-918"},
    {"id": 6, "name": "xxe", "cwe": "CWE-611"},
    {"id": 7, "name": "insecure_deserialization", "cwe": "CWE-502"},
    {"id": 8, "name": "hardcoded_credentials", "cwe": "CWE-798"},
    {"id": 9, "name": "weak_cryptography", "cwe": "CWE-327"},
    {"id": 10, "name": "buffer_overflow", "cwe": "CWE-120"},
    {"id": 11, "name": "race_condition", "cwe": "CWE-362"},
    {"id": 12, "name": "improper_authentication", "cwe": "CWE-287"},
    {"id": 13, "name": "sensitive_data_exposure", "cwe": "CWE-200"},
    {"id": 14, "name": "insecure_configuration", "cwe": "CWE-1188"},
]


# =============================================================================
# ML ENGINE ADAPTER
# =============================================================================

class MLEngineAdapter:
    """
    Adapter for ML-based vulnerability detection.
    
    Provides a consistent interface between the ML architecture
    (TensorFlow/MindSpore) and the hybrid fusion engine.
    
    Features:
    - Lazy loading of ML models
    - Confidence calibration
    - Explainability extraction
    - Batch processing support
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        threshold: float = 0.5,
        use_gpu: bool = True,
    ):
        """
        Initialize ML adapter.
        
        Args:
            model_path: Path to trained model. If None, uses default.
            threshold: Classification threshold for positive predictions.
            use_gpu: Whether to use GPU acceleration.
        """
        self.model_path = model_path
        self.threshold = threshold
        self.use_gpu = use_gpu
        
        self._inference_engine = None
        self._model_version = "1.0.0"
        self._loaded = False
        
        logger.info("ML Engine Adapter initialized")
    
    def _lazy_load(self):
        """Lazy load the inference engine."""
        if self._loaded:
            return
        
        try:
            from ..architecture import ModelConfig, ModelRegistry
            from ..architecture.tensorflow_impl import CodePreprocessor
            
            config = ModelConfig()
            
            # Get implementations from registry
            preprocessor = CodePreprocessor(config)
            extractor = ModelRegistry.get_feature_extractor("tensorflow")(config)
            classifier = ModelRegistry.get_classifier("tensorflow")(config)
            
            self._inference_engine = ModelRegistry.get_inference_engine("tensorflow")(
                preprocessor, extractor, classifier, config
            )
            
            # Load weights if path provided
            if self.model_path:
                # TODO: Load trained weights
                pass
            
            self._loaded = True
            logger.info("ML inference engine loaded")
            
        except ImportError as e:
            logger.warning(f"Could not load ML engine: {e}")
            logger.warning("Using mock predictions")
            self._loaded = True
    
    def predict(
        self,
        code: str,
        include_explanation: bool = True,
    ) -> MLPrediction:
        """
        Predict vulnerabilities in code.
        
        Args:
            code: Source code to analyze
            include_explanation: Whether to include explainability data
        
        Returns:
            MLPrediction with vulnerability predictions
        """
        import time
        start_time = time.time()
        
        self._lazy_load()
        
        # Use actual inference engine if available
        if self._inference_engine:
            try:
                result = self._inference_engine.predict(
                    code, 
                    return_explanation=include_explanation
                )
                return self._convert_engine_result(result, time.time() - start_time)
            except Exception as e:
                logger.error(f"Inference failed: {e}")
                # Fall back to mock
        
        # Mock prediction for development/testing
        return self._mock_predict(code, time.time() - start_time)
    
    def batch_predict(
        self,
        codes: List[str],
        batch_size: int = 32,
    ) -> List[MLPrediction]:
        """
        Batch prediction for multiple code snippets.
        
        Args:
            codes: List of code snippets
            batch_size: Processing batch size
        
        Returns:
            List of MLPrediction results
        """
        import time
        start_time = time.time()
        
        self._lazy_load()
        
        results = []
        for i in range(0, len(codes), batch_size):
            batch = codes[i:i + batch_size]
            
            if self._inference_engine:
                try:
                    batch_results = self._inference_engine.batch_predict(
                        batch, batch_size=batch_size
                    )
                    results.extend([
                        self._convert_engine_result(r, (time.time() - start_time) / len(batch))
                        for r in batch_results
                    ])
                    continue
                except Exception as e:
                    logger.error(f"Batch inference failed: {e}")
            
            # Fall back to individual mock predictions
            results.extend([
                self._mock_predict(code, (time.time() - start_time) / len(batch))
                for code in batch
            ])
        
        return results
    
    def _convert_engine_result(
        self,
        result: Dict[str, Any],
        processing_time: float,
    ) -> MLPrediction:
        """Convert inference engine result to MLPrediction."""
        predictions = []
        
        for class_info in VULNERABILITY_CLASSES:
            class_name = class_info["name"]
            
            if class_name in result.get("predictions", {}):
                pred_data = result["predictions"][class_name]
                prob = pred_data.get("probability", 0.0)
            else:
                prob = 0.0
            
            predictions.append(VulnerabilityPrediction(
                class_id=class_info["id"],
                class_name=class_name,
                probability=prob,
                confidence=MLConfidence.from_probability(prob),
                cwe_id=class_info["cwe"],
                important_tokens=result.get("explanation", {}).get("important_tokens", []),
            ))
        
        # Calculate overall confidence
        detected = [p for p in predictions if p.is_positive]
        if detected:
            avg_confidence = np.mean([p.probability for p in detected])
            overall_confidence = MLConfidence.from_probability(avg_confidence)
        else:
            overall_confidence = MLConfidence.VERY_LOW
        
        return MLPrediction(
            predictions=predictions,
            overall_confidence=overall_confidence,
            processing_time_ms=processing_time * 1000,
            model_version=self._model_version,
            top_important_tokens=result.get("explanation", {}).get("important_tokens", []),
            reasoning=result.get("explanation", {}).get("reasoning", ""),
            raw_probabilities=result.get("raw_probabilities"),
            attention_weights=result.get("attention_weights"),
        )
    
    def _mock_predict(
        self,
        code: str,
        processing_time: float,
    ) -> MLPrediction:
        """
        Mock prediction for development/testing.
        
        Uses simple heuristics to generate realistic-looking predictions.
        """
        predictions = []
        code_lower = code.lower()
        
        # Simple heuristic scoring based on keywords
        heuristic_scores = {
            "sql_injection": 0.3 if "select" in code_lower and ("+" in code or "format" in code_lower) else 0.1,
            "xss": 0.3 if "innerhtml" in code_lower or "document.write" in code_lower else 0.1,
            "command_injection": 0.4 if "os.system" in code_lower or "subprocess" in code_lower else 0.1,
            "path_traversal": 0.3 if "open(" in code_lower and ("+" in code or "format" in code_lower) else 0.1,
            "code_injection": 0.5 if "eval(" in code_lower or "exec(" in code_lower else 0.1,
            "ssrf": 0.3 if "requests." in code_lower and ("+" in code or "format" in code_lower) else 0.1,
            "xxe": 0.2 if "xml" in code_lower and "parse" in code_lower else 0.05,
            "insecure_deserialization": 0.5 if "pickle" in code_lower or "yaml.load" in code_lower else 0.1,
            "hardcoded_credentials": 0.4 if "password" in code_lower and "=" in code else 0.1,
            "weak_cryptography": 0.4 if "md5" in code_lower or "sha1" in code_lower else 0.1,
            "buffer_overflow": 0.1,
            "race_condition": 0.2 if "thread" in code_lower and "shared" in code_lower else 0.05,
            "improper_authentication": 0.2 if "login" in code_lower and "password" in code_lower else 0.1,
            "sensitive_data_exposure": 0.2 if "print" in code_lower and "password" in code_lower else 0.1,
            "insecure_configuration": 0.3 if "debug" in code_lower and "true" in code_lower else 0.1,
        }
        
        # Add some noise for realism
        np.random.seed(hash(code) % 2**32)
        
        for class_info in VULNERABILITY_CLASSES:
            base_score = heuristic_scores.get(class_info["name"], 0.1)
            noise = np.random.uniform(-0.1, 0.1)
            prob = max(0.0, min(1.0, base_score + noise))
            
            predictions.append(VulnerabilityPrediction(
                class_id=class_info["id"],
                class_name=class_info["name"],
                probability=prob,
                confidence=MLConfidence.from_probability(prob),
                cwe_id=class_info["cwe"],
                important_tokens=[],  # No tokens in mock
            ))
        
        # Calculate overall confidence
        detected = [p for p in predictions if p.is_positive]
        if detected:
            avg_confidence = np.mean([p.probability for p in detected])
            overall_confidence = MLConfidence.from_probability(avg_confidence)
        else:
            overall_confidence = MLConfidence.VERY_LOW
        
        return MLPrediction(
            predictions=predictions,
            overall_confidence=overall_confidence,
            processing_time_ms=processing_time * 1000,
            model_version=f"{self._model_version}-mock",
            top_important_tokens=[],
            reasoning="Mock prediction based on keyword heuristics",
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_path": self.model_path,
            "model_version": self._model_version,
            "threshold": self.threshold,
            "use_gpu": self.use_gpu,
            "loaded": self._loaded,
            "num_classes": len(VULNERABILITY_CLASSES),
            "classes": [c["name"] for c in VULNERABILITY_CLASSES],
        }
    
    def calibrate_threshold(
        self,
        validation_data: List[Tuple[str, List[int]]],
        target_recall: float = 0.95,
    ) -> float:
        """
        Calibrate classification threshold for target recall.
        
        Args:
            validation_data: List of (code, ground_truth_labels) tuples
            target_recall: Target recall to achieve
        
        Returns:
            Calibrated threshold
        """
        # Collect predictions and labels
        all_probs = []
        all_labels = []
        
        for code, labels in validation_data:
            prediction = self.predict(code, include_explanation=False)
            probs = [p.probability for p in prediction.predictions]
            all_probs.append(probs)
            all_labels.append(labels)
        
        all_probs = np.array(all_probs)
        all_labels = np.array(all_labels)
        
        # Find threshold that achieves target recall
        thresholds = np.arange(0.1, 0.9, 0.05)
        for thresh in thresholds:
            predictions = (all_probs >= thresh).astype(int)
            
            # Calculate recall
            true_positives = np.sum((predictions == 1) & (all_labels == 1))
            false_negatives = np.sum((predictions == 0) & (all_labels == 1))
            
            if true_positives + false_negatives > 0:
                recall = true_positives / (true_positives + false_negatives)
                
                if recall >= target_recall:
                    self.threshold = thresh
                    logger.info(f"Calibrated threshold: {thresh:.2f} (recall: {recall:.2f})")
                    return thresh
        
        logger.warning("Could not achieve target recall, using default threshold")
        return self.threshold
