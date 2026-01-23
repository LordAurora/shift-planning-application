"""
AI-Powered Security Analysis System
====================================

Enterprise-grade security vulnerability detection, classification, and mitigation system.

Architecture:
- Phase 1: Local TensorFlow-based inference
- Phase 2: Huawei Cloud ModelArts + MindSpore migration ready

Components:
- VulnerabilityDetector: Core ML model for vulnerability detection
- CodeAnalyzer: Static code analysis with ML enhancement
- APIScanner: API security configuration analysis
- SeverityClassifier: Multi-class severity classification (Critical/High/Medium/Low)
- MitigationEngine: AI-powered remediation guidance generator

Security Principles:
- No hardcoded secrets
- Secure-by-design outputs
- Auditable predictions with confidence scores
- Explainable AI (XAI) support
"""

__version__ = "1.0.0"
__author__ = "Security AI Team"

from .config import SecurityAIConfig, get_config, VulnerabilityCategory, SeverityLevel
from .models.vulnerability_detector import VulnerabilityDetector
from .models.severity_classifier import SeverityClassifier
from .models.code_embedder import CodeEmbedder
from .services.code_analyzer import CodeAnalyzer
from .services.api_scanner import APISecurityScanner
from .services.mitigation_engine import MitigationEngine
from .pipeline.inference import SecurityInferencePipeline
from .pipeline.training import SecurityTrainingPipeline

__all__ = [
    "SecurityAIConfig",
    "get_config",
    "VulnerabilityCategory",
    "SeverityLevel",
    "VulnerabilityDetector",
    "SeverityClassifier",
    "CodeEmbedder",
    "CodeAnalyzer",
    "APISecurityScanner",
    "MitigationEngine",
    "SecurityInferencePipeline",
    "SecurityTrainingPipeline",
]
