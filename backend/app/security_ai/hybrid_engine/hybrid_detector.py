"""
Hybrid Security Detector

Main entry point for hybrid (rule + ML) security detection.
Orchestrates rule engine, ML adapter, and fusion engine.
"""

import time
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

from .rule_engine import RuleEngine, RuleCategory, RuleSeverity
from .ml_adapter import MLEngineAdapter, MLPrediction
from .fusion_engine import FusionEngine, FusionStrategy, HybridDetectionResult

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class DetectionMode(Enum):
    """Detection mode configuration."""
    FULL = "full"               # Full rule + ML scan
    RULES_ONLY = "rules_only"   # Rules only (fast)
    ML_ONLY = "ml_only"         # ML only (pattern detection)
    CRITICAL_ONLY = "critical"  # Critical rules only (fastest, CI/CD)


@dataclass
class HybridConfig:
    """Configuration for hybrid detector."""
    # Detection mode
    mode: DetectionMode = DetectionMode.FULL
    
    # Rule engine config
    min_rule_severity: RuleSeverity = RuleSeverity.LOW
    categories: Optional[List[RuleCategory]] = None
    
    # ML engine config
    ml_threshold: float = 0.5
    use_gpu: bool = True
    
    # Fusion config
    fusion_strategy: FusionStrategy = FusionStrategy.BALANCED
    fp_suppression: bool = True
    
    # Performance
    timeout_seconds: float = 30.0
    batch_size: int = 32


# =============================================================================
# HYBRID DETECTOR
# =============================================================================

class HybridSecurityDetector:
    """
    Enterprise-grade hybrid security detector.
    
    Combines deterministic rule-based detection with probabilistic
    ML-based detection for comprehensive vulnerability coverage.
    
    Usage:
        detector = HybridSecurityDetector()
        result = detector.scan(code)
        
        if result.should_block:
            print("Critical vulnerability found!")
    
    Design Goals:
    1. Zero false negatives on critical vulnerabilities (rules)
    2. Novel vulnerability detection (ML)
    3. Minimized false positives (fusion + suppression)
    4. Fast enough for CI/CD integration
    """
    
    def __init__(self, config: Optional[HybridConfig] = None):
        """
        Initialize hybrid detector.
        
        Args:
            config: Detection configuration. Uses defaults if None.
        """
        self.config = config or HybridConfig()
        
        # Initialize components
        self.rule_engine = RuleEngine()
        self.ml_adapter = MLEngineAdapter(
            threshold=self.config.ml_threshold,
            use_gpu=self.config.use_gpu,
        )
        self.fusion_engine = FusionEngine(
            strategy=self.config.fusion_strategy,
            ml_threshold=self.config.ml_threshold,
            fp_suppression_enabled=self.config.fp_suppression,
        )
        
        logger.info(f"Hybrid detector initialized with mode: {self.config.mode.value}")
    
    def scan(
        self,
        code: str,
        filename: str = "<unknown>",
        mode: Optional[DetectionMode] = None,
    ) -> HybridDetectionResult:
        """
        Scan code for security vulnerabilities.
        
        Args:
            code: Source code to scan
            filename: Filename for reporting
            mode: Override detection mode
        
        Returns:
            HybridDetectionResult with fused vulnerabilities
        """
        mode = mode or self.config.mode
        
        if mode == DetectionMode.CRITICAL_ONLY:
            return self._scan_critical_only(code, filename)
        elif mode == DetectionMode.RULES_ONLY:
            return self._scan_rules_only(code, filename)
        elif mode == DetectionMode.ML_ONLY:
            return self._scan_ml_only(code, filename)
        else:
            return self._scan_full(code, filename)
    
    def _scan_full(self, code: str, filename: str) -> HybridDetectionResult:
        """Full hybrid scan (rules + ML + fusion)."""
        # Rule scan
        rule_start = time.time()
        rule_results = self.rule_engine.scan(
            code,
            filename,
            categories=self.config.categories,
            min_severity=self.config.min_rule_severity,
        )
        rule_time = (time.time() - rule_start) * 1000
        
        # ML scan
        ml_prediction = self.ml_adapter.predict(code, include_explanation=True)
        
        # Fusion
        result = self.fusion_engine.fuse(rule_results, ml_prediction, code)
        result.rule_scan_time_ms = rule_time
        
        return result
    
    def _scan_critical_only(self, code: str, filename: str) -> HybridDetectionResult:
        """
        Scan critical rules only (fast path for CI/CD).
        
        This is the fastest mode, designed for blocking pipelines
        on known critical vulnerabilities.
        """
        rule_start = time.time()
        rule_results = self.rule_engine.scan_critical_only(code)
        rule_time = (time.time() - rule_start) * 1000
        
        # Create minimal ML prediction (no actual scan)
        ml_prediction = MLPrediction(
            predictions=[],
            overall_confidence=None,
            processing_time_ms=0.0,
            model_version="skipped",
        )
        
        result = self.fusion_engine.fuse(rule_results, ml_prediction, code)
        result.rule_scan_time_ms = rule_time
        result.ml_scan_time_ms = 0.0
        
        return result
    
    def _scan_rules_only(self, code: str, filename: str) -> HybridDetectionResult:
        """Scan with rules only (no ML)."""
        rule_start = time.time()
        rule_results = self.rule_engine.scan(
            code,
            filename,
            categories=self.config.categories,
            min_severity=self.config.min_rule_severity,
        )
        rule_time = (time.time() - rule_start) * 1000
        
        # Create minimal ML prediction
        ml_prediction = MLPrediction(
            predictions=[],
            overall_confidence=None,
            processing_time_ms=0.0,
            model_version="skipped",
        )
        
        result = self.fusion_engine.fuse(rule_results, ml_prediction, code)
        result.rule_scan_time_ms = rule_time
        result.ml_scan_time_ms = 0.0
        
        return result
    
    def _scan_ml_only(self, code: str, filename: str) -> HybridDetectionResult:
        """Scan with ML only (no rules)."""
        ml_prediction = self.ml_adapter.predict(code, include_explanation=True)
        
        # No rule results
        rule_results = []
        
        result = self.fusion_engine.fuse(rule_results, ml_prediction, code)
        result.rule_scan_time_ms = 0.0
        
        return result
    
    def batch_scan(
        self,
        code_files: List[Dict[str, str]],
    ) -> List[HybridDetectionResult]:
        """
        Batch scan multiple files.
        
        Args:
            code_files: List of {"filename": str, "code": str}
        
        Returns:
            List of HybridDetectionResult
        """
        results = []
        
        for file_info in code_files:
            filename = file_info.get("filename", "<unknown>")
            code = file_info.get("code", "")
            
            try:
                result = self.scan(code, filename)
                results.append(result)
            except Exception as e:
                logger.error(f"Error scanning {filename}: {e}")
                # Return empty result for failed file
                results.append(self._create_error_result(str(e)))
        
        return results
    
    def _create_error_result(self, error_message: str) -> HybridDetectionResult:
        """Create error result when scanning fails."""
        return HybridDetectionResult(
            vulnerabilities=[],
            summary={
                "error": error_message,
                "total_vulnerabilities": 0,
            },
            rule_scan_time_ms=0.0,
            ml_scan_time_ms=0.0,
            fusion_time_ms=0.0,
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detector statistics."""
        return {
            "config": {
                "mode": self.config.mode.value,
                "fusion_strategy": self.config.fusion_strategy.value,
                "ml_threshold": self.config.ml_threshold,
                "fp_suppression": self.config.fp_suppression,
            },
            "rule_engine": self.rule_engine.get_statistics(),
            "ml_engine": self.ml_adapter.get_model_info(),
        }
    
    def add_custom_rule(self, rule_definition: Dict[str, Any]):
        """
        Add a custom rule to the detector.
        
        Args:
            rule_definition: Rule definition dict with:
                - rule_id: Unique identifier
                - name: Human-readable name
                - description: Description
                - severity: critical/high/medium/low
                - patterns: List of regex patterns
                - cwe_id: CWE identifier
        """
        from .rule_engine import SecurityRule, RuleSeverity, RuleCategory
        
        severity_map = {
            "critical": RuleSeverity.CRITICAL,
            "high": RuleSeverity.HIGH,
            "medium": RuleSeverity.MEDIUM,
            "low": RuleSeverity.LOW,
            "info": RuleSeverity.INFO,
        }
        
        rule = SecurityRule(
            rule_id=rule_definition["rule_id"],
            name=rule_definition["name"],
            description=rule_definition["description"],
            severity=severity_map.get(rule_definition["severity"], RuleSeverity.MEDIUM),
            category=RuleCategory.INJECTION,  # Default category
            cwe_id=rule_definition.get("cwe_id", "CWE-000"),
            patterns=rule_definition.get("patterns", []),
            anti_patterns=rule_definition.get("anti_patterns", []),
            remediation=rule_definition.get("remediation", ""),
            is_critical=rule_definition.get("is_critical", False),
        )
        
        self.rule_engine.add_rule(rule)
        logger.info(f"Added custom rule: {rule.rule_id}")


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

def demonstrate_hybrid_detection():
    """Demonstrate hybrid detection with example scenarios."""
    
    detector = HybridSecurityDetector(HybridConfig(
        mode=DetectionMode.FULL,
        fusion_strategy=FusionStrategy.BALANCED,
    ))
    
    # Scenario 1: Critical Rule Match (SQL Injection)
    # Rule: DEFINITE match
    # ML: May or may not detect
    # Result: CRITICAL (rule overrides)
    print("\n" + "="*60)
    print("SCENARIO 1: SQL Injection (Critical Rule)")
    print("="*60)
    
    code_sql_injection = '''
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
'''
    
    result1 = detector.scan(code_sql_injection, "user_service.py")
    print(f"Vulnerabilities found: {result1.total_count}")
    print(f"Should block CI/CD: {result1.should_block}")
    for vuln in result1.vulnerabilities:
        print(f"  - {vuln.name}: {vuln.severity.value} ({vuln.source.value})")
    
    # Scenario 2: ML Supplements Rule
    # Rule: MEDIUM match (debug enabled)
    # ML: HIGH confidence on insecure config
    # Result: MEDIUM+ (ML supports rule)
    print("\n" + "="*60)
    print("SCENARIO 2: Debug Mode + ML Support")
    print("="*60)
    
    code_debug = '''
from flask import Flask
app = Flask(__name__)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
'''
    
    result2 = detector.scan(code_debug, "app.py")
    print(f"Vulnerabilities found: {result2.total_count}")
    for vuln in result2.vulnerabilities:
        print(f"  - {vuln.name}: {vuln.severity.value} ({vuln.source.value})")
        print(f"    Confidence: {vuln.confidence.confidence_level}")
    
    # Scenario 3: ML-Only Detection
    # Rule: No match (pattern not in rules)
    # ML: Detects potential issue
    # Result: Depends on ML confidence
    print("\n" + "="*60)
    print("SCENARIO 3: ML-Only Detection (Pickle)")
    print("="*60)
    
    code_pickle = '''
import pickle

def load_user_data(data):
    # Load user-provided data
    return pickle.loads(data)
'''
    
    result3 = detector.scan(code_pickle, "data_loader.py")
    print(f"Vulnerabilities found: {result3.total_count}")
    for vuln in result3.vulnerabilities:
        print(f"  - {vuln.name}: {vuln.severity.value} ({vuln.source.value})")
        print(f"    ML Confidence: {vuln.confidence.ml_confidence:.2f}")
    
    # Scenario 4: False Positive Suppression
    # Rule: Match in test file
    # ML: Low confidence
    # Result: SUPPRESSED
    print("\n" + "="*60)
    print("SCENARIO 4: False Positive Suppression (Test Code)")
    print("="*60)
    
    code_test = '''
import unittest

class TestSQLQueries(unittest.TestCase):
    def test_query_construction(self):
        # Test that query formatting works
        query = f"SELECT * FROM users WHERE id = {test_id}"
        self.assertEqual(len(query), 42)
'''
    
    result4 = detector.scan(code_test, "test_queries.py")
    print(f"Vulnerabilities found: {result4.total_count}")
    print(f"Suppressed: {result4.summary.get('by_severity', {}).get('suppressed', 0)}")
    
    # Scenario 5: Clean Code
    print("\n" + "="*60)
    print("SCENARIO 5: Clean Code (No Vulnerabilities)")
    print("="*60)
    
    code_clean = '''
import os
from sqlalchemy.orm import Session

def get_user(db: Session, user_id: int):
    # Safe parameterized query
    return db.query(User).filter(User.id == user_id).first()

def get_config():
    # Safe environment variable usage
    return os.environ.get("DATABASE_URL")
'''
    
    result5 = detector.scan(code_clean, "clean_service.py")
    print(f"Vulnerabilities found: {result5.total_count}")
    print(f"Should block CI/CD: {result5.should_block}")


if __name__ == "__main__":
    demonstrate_hybrid_detection()
