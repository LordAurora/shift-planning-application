"""
Security AI Models Package

Contains ML models for:
- Vulnerability Detection (transformer-based)
- Severity Classification (multi-class)
- Code Embedding (for semantic understanding)
"""

from .vulnerability_detector import VulnerabilityDetector
from .severity_classifier import SeverityClassifier
from .code_embedder import CodeEmbedder

__all__ = [
    "VulnerabilityDetector",
    "SeverityClassifier", 
    "CodeEmbedder"
]
