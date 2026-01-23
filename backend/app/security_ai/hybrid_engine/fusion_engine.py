"""
Fusion Engine

Intelligent combination of rule-based and ML-based detection results.
Implements enterprise-grade decision logic with:
- Priority arbitration (rules > ML for known threats)
- Confidence scoring (combined evidence)
- False positive suppression (contextual filtering)

Decision Flow:
    ┌─────────────────────────────────────────────────────────────────┐
    │                    FUSION DECISION FLOW                         │
    └─────────────────────────────────────────────────────────────────┘
    
    1. CRITICAL RULE MATCH? ──────────────────────────────────────────►
       │                                                    BLOCK (P0)
       │ No
       ▼
    2. HIGH RULE + ML AGREEMENT? ─────────────────────────────────────►
       │                                              HIGH CONFIDENCE
       │ No
       ▼
    3. ML ONLY (HIGH CONFIDENCE)? ────────────────────────────────────►
       │                                            MEDIUM CONFIDENCE
       │ No
       ▼
    4. RULE ONLY (NO ML SUPPORT)? ────────────────────────────────────►
       │                                  MEDIUM CONFIDENCE (FP check)
       │ No
       ▼
    5. ML ONLY (LOW CONFIDENCE)? ─────────────────────────────────────►
       │                                   LOW CONFIDENCE (suppressed)
       │ No
       ▼
    PASS (No vulnerabilities detected)
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum, auto
import numpy as np

from .rule_engine import RuleResult, RuleSeverity, RuleCategory, RuleConfidence
from .ml_adapter import MLPrediction, VulnerabilityPrediction, MLConfidence

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND CONFIGURATION
# =============================================================================

class DetectionSource(Enum):
    """Source of vulnerability detection."""
    RULE_ONLY = "rule_only"           # Detected only by rules
    ML_ONLY = "ml_only"               # Detected only by ML
    RULE_AND_ML = "rule_and_ml"       # Detected by both (high confidence)
    RULE_OVERRIDES_ML = "rule_override"  # Rule detected, ML missed
    ML_SUPPLEMENTS_RULE = "ml_supplement"  # ML adds context to rule


class FusionStrategy(Enum):
    """Strategy for combining results."""
    CONSERVATIVE = "conservative"     # Minimize false positives
    BALANCED = "balanced"             # Balance FP and FN
    AGGRESSIVE = "aggressive"         # Minimize false negatives


class FusedSeverity(Enum):
    """Final fused severity level."""
    CRITICAL = "critical"    # Immediate action required
    HIGH = "high"            # Address in current sprint
    MEDIUM = "medium"        # Address soon
    LOW = "low"              # Backlog
    INFO = "info"            # Informational only
    SUPPRESSED = "suppressed"  # False positive suppressed
    
    @property
    def priority(self) -> int:
        priorities = {
            FusedSeverity.CRITICAL: 6,
            FusedSeverity.HIGH: 5,
            FusedSeverity.MEDIUM: 4,
            FusedSeverity.LOW: 3,
            FusedSeverity.INFO: 2,
            FusedSeverity.SUPPRESSED: 1,
        }
        return priorities[self]


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ConfidenceScore:
    """
    Combined confidence score from multiple sources.
    
    Formula:
        final_score = rule_weight * rule_confidence + ml_weight * ml_confidence
        
    Where weights depend on fusion strategy and evidence type.
    """
    rule_confidence: float = 0.0     # 0.0 - 1.0
    ml_confidence: float = 0.0       # 0.0 - 1.0
    combined_score: float = 0.0      # Final fused score
    
    # Evidence counts
    rule_matches: int = 0
    ml_positive_classes: int = 0
    
    # Explanation
    factors: List[str] = field(default_factory=list)
    
    @property
    def confidence_level(self) -> str:
        """Human-readable confidence level."""
        if self.combined_score >= 0.95:
            return "very_high"
        elif self.combined_score >= 0.85:
            return "high"
        elif self.combined_score >= 0.70:
            return "medium"
        elif self.combined_score >= 0.50:
            return "low"
        else:
            return "very_low"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_confidence": round(self.rule_confidence, 4),
            "ml_confidence": round(self.ml_confidence, 4),
            "combined_score": round(self.combined_score, 4),
            "confidence_level": self.confidence_level,
            "rule_matches": self.rule_matches,
            "ml_positive_classes": self.ml_positive_classes,
            "factors": self.factors,
        }


@dataclass
class FusedVulnerability:
    """Single fused vulnerability finding."""
    vulnerability_id: str
    name: str
    severity: FusedSeverity
    source: DetectionSource
    confidence: ConfidenceScore
    cwe_id: str
    owasp_category: str
    
    # Details
    description: str
    remediation: str
    
    # Evidence
    rule_matches: List[Dict[str, Any]] = field(default_factory=list)
    ml_prediction: Optional[Dict[str, Any]] = None
    
    # Location info
    affected_lines: List[int] = field(default_factory=list)
    code_snippets: List[str] = field(default_factory=list)
    
    # Explainability
    important_tokens: List[Tuple[str, float]] = field(default_factory=list)
    reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "vulnerability_id": self.vulnerability_id,
            "name": self.name,
            "severity": self.severity.value,
            "source": self.source.value,
            "confidence": self.confidence.to_dict(),
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
            "description": self.description,
            "remediation": self.remediation,
            "rule_matches": self.rule_matches,
            "ml_prediction": self.ml_prediction,
            "affected_lines": self.affected_lines,
            "code_snippets": self.code_snippets[:3],  # Limit snippets
            "important_tokens": [
                {"token": t, "importance": round(s, 4)}
                for t, s in self.important_tokens[:10]
            ],
            "reasoning": self.reasoning,
        }


@dataclass
class HybridDetectionResult:
    """Complete result from hybrid detection."""
    vulnerabilities: List[FusedVulnerability]
    summary: Dict[str, Any]
    
    # Processing info
    rule_scan_time_ms: float
    ml_scan_time_ms: float
    fusion_time_ms: float
    
    # Raw results for debugging
    raw_rule_results: Optional[List[RuleResult]] = None
    raw_ml_prediction: Optional[MLPrediction] = None
    
    @property
    def has_critical(self) -> bool:
        return any(v.severity == FusedSeverity.CRITICAL for v in self.vulnerabilities)
    
    @property
    def has_high(self) -> bool:
        return any(v.severity == FusedSeverity.HIGH for v in self.vulnerabilities)
    
    @property
    def should_block(self) -> bool:
        """Whether this result should block CI/CD pipeline."""
        return self.has_critical
    
    @property
    def total_count(self) -> int:
        return len([v for v in self.vulnerabilities if v.severity != FusedSeverity.SUPPRESSED])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "summary": self.summary,
            "metrics": {
                "rule_scan_time_ms": round(self.rule_scan_time_ms, 2),
                "ml_scan_time_ms": round(self.ml_scan_time_ms, 2),
                "fusion_time_ms": round(self.fusion_time_ms, 2),
                "total_time_ms": round(
                    self.rule_scan_time_ms + self.ml_scan_time_ms + self.fusion_time_ms, 2
                ),
            },
            "should_block": self.should_block,
            "total_vulnerabilities": self.total_count,
        }


# =============================================================================
# CWE TO VULNERABILITY MAPPING
# =============================================================================

CWE_TO_VULN_CLASS = {
    "CWE-89": "sql_injection",
    "CWE-79": "xss",
    "CWE-78": "command_injection",
    "CWE-22": "path_traversal",
    "CWE-94": "code_injection",
    "CWE-918": "ssrf",
    "CWE-611": "xxe",
    "CWE-502": "insecure_deserialization",
    "CWE-798": "hardcoded_credentials",
    "CWE-327": "weak_cryptography",
    "CWE-120": "buffer_overflow",
    "CWE-362": "race_condition",
    "CWE-287": "improper_authentication",
    "CWE-200": "sensitive_data_exposure",
    "CWE-1188": "insecure_configuration",
    "CWE-352": "csrf",
    "CWE-614": "insecure_cookie",
    "CWE-489": "debug_enabled",
    "CWE-209": "verbose_error",
    "CWE-915": "mass_assignment",
}


# =============================================================================
# FUSION ENGINE
# =============================================================================

class FusionEngine:
    """
    Fuses rule-based and ML-based detection results.
    
    Design Philosophy:
    1. Rules are authoritative for known patterns (CRITICAL rules never overridden)
    2. ML supplements rules with pattern recognition
    3. Agreement between rule and ML increases confidence
    4. Disagreement triggers review (not automatic suppression)
    
    False Positive Suppression:
    - Contextual checks (is this test code? is this a comment?)
    - Anti-pattern matching (already sanitized?)
    - ML confidence below threshold with no rule support
    """
    
    def __init__(
        self,
        strategy: FusionStrategy = FusionStrategy.BALANCED,
        ml_threshold: float = 0.5,
        fp_suppression_enabled: bool = True,
    ):
        """
        Initialize fusion engine.
        
        Args:
            strategy: Fusion strategy (conservative/balanced/aggressive)
            ml_threshold: ML probability threshold for positive detection
            fp_suppression_enabled: Whether to enable FP suppression
        """
        self.strategy = strategy
        self.ml_threshold = ml_threshold
        self.fp_suppression_enabled = fp_suppression_enabled
        
        # Strategy-specific weights
        self._setup_weights()
        
        logger.info(f"Fusion engine initialized with strategy: {strategy.value}")
    
    def _setup_weights(self):
        """Set up confidence weights based on strategy."""
        if self.strategy == FusionStrategy.CONSERVATIVE:
            # Require strong evidence
            self.rule_weight = 0.7
            self.ml_weight = 0.3
            self.agreement_bonus = 0.15
            self.ml_only_penalty = 0.2
        elif self.strategy == FusionStrategy.AGGRESSIVE:
            # Trust all signals
            self.rule_weight = 0.5
            self.ml_weight = 0.5
            self.agreement_bonus = 0.1
            self.ml_only_penalty = 0.0
        else:  # BALANCED
            self.rule_weight = 0.6
            self.ml_weight = 0.4
            self.agreement_bonus = 0.12
            self.ml_only_penalty = 0.1
    
    def fuse(
        self,
        rule_results: List[RuleResult],
        ml_prediction: MLPrediction,
        code: str,
    ) -> HybridDetectionResult:
        """
        Fuse rule and ML results into unified detection result.
        
        Args:
            rule_results: Results from rule engine
            ml_prediction: Prediction from ML engine
            code: Original code (for context analysis)
        
        Returns:
            HybridDetectionResult with fused vulnerabilities
        """
        import time
        start_time = time.time()
        
        fused_vulns = []
        processed_cwes: Set[str] = set()
        
        # Step 1: Process critical rules (highest priority)
        for rule in rule_results:
            if rule.is_critical:
                fused = self._fuse_critical_rule(rule, ml_prediction, code)
                fused_vulns.append(fused)
                processed_cwes.add(rule.cwe_id)
        
        # Step 2: Process non-critical rules
        for rule in rule_results:
            if not rule.is_critical and rule.cwe_id not in processed_cwes:
                fused = self._fuse_rule_with_ml(rule, ml_prediction, code)
                if fused.severity != FusedSeverity.SUPPRESSED or not self.fp_suppression_enabled:
                    fused_vulns.append(fused)
                processed_cwes.add(rule.cwe_id)
        
        # Step 3: Process ML-only detections
        for ml_vuln in ml_prediction.detected_vulnerabilities:
            cwe_id = ml_vuln.cwe_id
            if cwe_id not in processed_cwes:
                fused = self._fuse_ml_only(ml_vuln, code)
                if fused.severity != FusedSeverity.SUPPRESSED or not self.fp_suppression_enabled:
                    fused_vulns.append(fused)
        
        # Sort by severity
        fused_vulns.sort(key=lambda v: v.severity.priority, reverse=True)
        
        # Generate summary
        summary = self._generate_summary(fused_vulns, rule_results, ml_prediction)
        
        fusion_time = (time.time() - start_time) * 1000
        
        return HybridDetectionResult(
            vulnerabilities=fused_vulns,
            summary=summary,
            rule_scan_time_ms=0.0,  # Set by caller
            ml_scan_time_ms=ml_prediction.processing_time_ms,
            fusion_time_ms=fusion_time,
            raw_rule_results=rule_results,
            raw_ml_prediction=ml_prediction,
        )
    
    def _fuse_critical_rule(
        self,
        rule: RuleResult,
        ml_prediction: MLPrediction,
        code: str,
    ) -> FusedVulnerability:
        """
        Fuse critical rule result.
        
        Critical rules ALWAYS result in CRITICAL severity.
        ML can only increase confidence, never decrease.
        """
        # Find matching ML prediction
        ml_vuln = self._find_ml_match(rule.cwe_id, ml_prediction)
        
        # Calculate confidence
        confidence = ConfidenceScore(
            rule_confidence=rule.confidence.value,
            ml_confidence=ml_vuln.probability if ml_vuln else 0.0,
            rule_matches=rule.match_count,
            ml_positive_classes=1 if ml_vuln and ml_vuln.is_positive else 0,
        )
        
        # Critical rules always get high combined score
        confidence.combined_score = max(0.95, confidence.rule_confidence)
        
        if ml_vuln and ml_vuln.is_positive:
            confidence.combined_score = min(1.0, confidence.combined_score + self.agreement_bonus)
            confidence.factors.append("Rule and ML agree (critical)")
            source = DetectionSource.RULE_AND_ML
        else:
            confidence.factors.append("Critical rule match (ML not required)")
            source = DetectionSource.RULE_OVERRIDES_ML
        
        return FusedVulnerability(
            vulnerability_id=f"VULN-{rule.rule_id}",
            name=rule.rule_name,
            severity=FusedSeverity.CRITICAL,
            source=source,
            confidence=confidence,
            cwe_id=rule.cwe_id,
            owasp_category=rule.category.value,
            description=rule.description,
            remediation=rule.remediation,
            rule_matches=[m.__dict__ for m in rule.matches],
            ml_prediction=ml_vuln.to_dict() if ml_vuln else None,
            affected_lines=[m.line_number for m in rule.matches],
            code_snippets=[m.matched_text for m in rule.matches],
            important_tokens=ml_vuln.important_tokens if ml_vuln else [],
            reasoning=f"Critical security rule {rule.rule_id} matched. Immediate remediation required.",
        )
    
    def _fuse_rule_with_ml(
        self,
        rule: RuleResult,
        ml_prediction: MLPrediction,
        code: str,
    ) -> FusedVulnerability:
        """
        Fuse non-critical rule with ML prediction.
        
        Decision matrix:
        - Rule HIGH + ML HIGH → HIGH (both agree)
        - Rule HIGH + ML LOW → MEDIUM (rule only, possible FP)
        - Rule MEDIUM + ML HIGH → MEDIUM/HIGH (ML supports)
        - Rule MEDIUM + ML LOW → LOW (weak signal)
        """
        ml_vuln = self._find_ml_match(rule.cwe_id, ml_prediction)
        
        # Calculate confidence
        rule_conf = rule.confidence.value
        ml_conf = ml_vuln.probability if ml_vuln else 0.0
        
        confidence = ConfidenceScore(
            rule_confidence=rule_conf,
            ml_confidence=ml_conf,
            rule_matches=rule.match_count,
            ml_positive_classes=1 if ml_vuln and ml_vuln.is_positive else 0,
        )
        
        # Check for agreement
        ml_agrees = ml_vuln and ml_vuln.probability >= self.ml_threshold
        
        if ml_agrees:
            # Agreement - boost confidence
            confidence.combined_score = (
                self.rule_weight * rule_conf +
                self.ml_weight * ml_conf +
                self.agreement_bonus
            )
            confidence.factors.append("Rule and ML agree")
            source = DetectionSource.RULE_AND_ML
        else:
            # Rule only - apply penalty
            confidence.combined_score = (
                self.rule_weight * rule_conf +
                self.ml_weight * 0.3 -
                self.ml_only_penalty
            )
            confidence.factors.append("Rule only (ML does not support)")
            source = DetectionSource.RULE_ONLY
        
        confidence.combined_score = max(0.0, min(1.0, confidence.combined_score))
        
        # Determine severity based on rule severity and confidence
        severity = self._determine_severity(rule.severity, confidence, ml_agrees)
        
        # FP suppression check
        if self.fp_suppression_enabled and not ml_agrees:
            if self._is_likely_false_positive(rule, code):
                severity = FusedSeverity.SUPPRESSED
                confidence.factors.append("Suppressed: likely false positive")
        
        return FusedVulnerability(
            vulnerability_id=f"VULN-{rule.rule_id}",
            name=rule.rule_name,
            severity=severity,
            source=source,
            confidence=confidence,
            cwe_id=rule.cwe_id,
            owasp_category=rule.category.value,
            description=rule.description,
            remediation=rule.remediation,
            rule_matches=[m.__dict__ for m in rule.matches],
            ml_prediction=ml_vuln.to_dict() if ml_vuln else None,
            affected_lines=[m.line_number for m in rule.matches],
            code_snippets=[m.matched_text for m in rule.matches],
            important_tokens=ml_vuln.important_tokens if ml_vuln else [],
            reasoning=self._generate_reasoning(rule, ml_vuln, ml_agrees),
        )
    
    def _fuse_ml_only(
        self,
        ml_vuln: VulnerabilityPrediction,
        code: str,
    ) -> FusedVulnerability:
        """
        Process ML-only detection (no rule match).
        
        ML-only detections have lower baseline confidence
        unless probability is very high.
        """
        confidence = ConfidenceScore(
            rule_confidence=0.0,
            ml_confidence=ml_vuln.probability,
            rule_matches=0,
            ml_positive_classes=1,
        )
        
        # ML-only penalty
        confidence.combined_score = (
            self.ml_weight * ml_vuln.probability -
            self.ml_only_penalty
        )
        confidence.combined_score = max(0.0, confidence.combined_score)
        confidence.factors.append("ML only (no rule match)")
        
        # Determine severity
        if ml_vuln.probability >= 0.95:
            severity = FusedSeverity.HIGH
            confidence.factors.append("Very high ML confidence")
        elif ml_vuln.probability >= 0.85:
            severity = FusedSeverity.MEDIUM
        elif ml_vuln.probability >= 0.70:
            severity = FusedSeverity.LOW
        else:
            severity = FusedSeverity.INFO
        
        # FP suppression for low-confidence ML-only
        if self.fp_suppression_enabled:
            if ml_vuln.probability < 0.70 and self.strategy == FusionStrategy.CONSERVATIVE:
                severity = FusedSeverity.SUPPRESSED
                confidence.factors.append("Suppressed: low ML confidence, no rule support")
        
        return FusedVulnerability(
            vulnerability_id=f"VULN-ML-{ml_vuln.class_id}",
            name=ml_vuln.class_name.replace("_", " ").title(),
            severity=severity,
            source=DetectionSource.ML_ONLY,
            confidence=confidence,
            cwe_id=ml_vuln.cwe_id,
            owasp_category="Unknown",  # ML doesn't provide OWASP mapping
            description=f"ML detected potential {ml_vuln.class_name.replace('_', ' ')} vulnerability",
            remediation=f"Review code for {ml_vuln.class_name.replace('_', ' ')} patterns",
            ml_prediction=ml_vuln.to_dict(),
            important_tokens=ml_vuln.important_tokens,
            reasoning=f"ML model detected {ml_vuln.class_name} with {ml_vuln.probability:.1%} confidence",
        )
    
    def _find_ml_match(
        self,
        cwe_id: str,
        ml_prediction: MLPrediction,
    ) -> Optional[VulnerabilityPrediction]:
        """Find ML prediction matching CWE."""
        vuln_class = CWE_TO_VULN_CLASS.get(cwe_id)
        if not vuln_class:
            return None
        
        for pred in ml_prediction.predictions:
            if pred.class_name == vuln_class:
                return pred
        
        return None
    
    def _determine_severity(
        self,
        rule_severity: RuleSeverity,
        confidence: ConfidenceScore,
        ml_agrees: bool,
    ) -> FusedSeverity:
        """Determine final severity based on rule severity and confidence."""
        if rule_severity == RuleSeverity.CRITICAL:
            return FusedSeverity.CRITICAL
        
        if rule_severity == RuleSeverity.HIGH:
            if ml_agrees or confidence.combined_score >= 0.85:
                return FusedSeverity.HIGH
            else:
                return FusedSeverity.MEDIUM
        
        if rule_severity == RuleSeverity.MEDIUM:
            if ml_agrees and confidence.combined_score >= 0.80:
                return FusedSeverity.MEDIUM
            elif confidence.combined_score >= 0.60:
                return FusedSeverity.LOW
            else:
                return FusedSeverity.INFO
        
        if rule_severity == RuleSeverity.LOW:
            return FusedSeverity.LOW
        
        return FusedSeverity.INFO
    
    def _is_likely_false_positive(
        self,
        rule: RuleResult,
        code: str,
    ) -> bool:
        """
        Check if detection is likely a false positive.
        
        Checks:
        1. Is this test code?
        2. Is the match in a comment?
        3. Is there sanitization nearby?
        """
        code_lower = code.lower()
        
        # Test code indicators
        test_indicators = [
            "def test_",
            "class test",
            "unittest",
            "pytest",
            "@test",
            "mock",
            "fixture",
        ]
        
        for indicator in test_indicators:
            if indicator in code_lower:
                return True
        
        # Check if match is in comment
        for match in rule.matches:
            line_idx = match.line_number - 1
            lines = code.split('\n')
            if line_idx < len(lines):
                line = lines[line_idx].strip()
                if line.startswith('#') or line.startswith('//') or line.startswith('/*'):
                    return True
        
        # Sanitization indicators near match
        sanitization_indicators = [
            "escape",
            "sanitize",
            "validate",
            "parameterized",
            "prepared",
            "safe_",
            "secure_",
        ]
        
        for match in rule.matches:
            context = match.context_before + match.context_after
            for indicator in sanitization_indicators:
                if indicator in context.lower():
                    return True
        
        return False
    
    def _generate_reasoning(
        self,
        rule: RuleResult,
        ml_vuln: Optional[VulnerabilityPrediction],
        ml_agrees: bool,
    ) -> str:
        """Generate human-readable reasoning for detection."""
        parts = []
        
        parts.append(f"Rule {rule.rule_id} ({rule.rule_name}) matched {rule.match_count} location(s).")
        
        if ml_agrees:
            parts.append(f"ML model supports detection with {ml_vuln.probability:.1%} confidence.")
        elif ml_vuln:
            parts.append(f"ML model has lower confidence ({ml_vuln.probability:.1%}).")
        else:
            parts.append("ML model did not specifically detect this vulnerability type.")
        
        if rule.is_critical:
            parts.append("This is a CRITICAL rule requiring immediate attention.")
        
        return " ".join(parts)
    
    def _generate_summary(
        self,
        fused_vulns: List[FusedVulnerability],
        rule_results: List[RuleResult],
        ml_prediction: MLPrediction,
    ) -> Dict[str, Any]:
        """Generate summary statistics."""
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
            "suppressed": 0,
        }
        
        source_counts = {
            "rule_only": 0,
            "ml_only": 0,
            "rule_and_ml": 0,
            "rule_override": 0,
            "ml_supplement": 0,
        }
        
        for vuln in fused_vulns:
            severity_counts[vuln.severity.value] += 1
            source_counts[vuln.source.value] += 1
        
        return {
            "total_vulnerabilities": len([v for v in fused_vulns if v.severity != FusedSeverity.SUPPRESSED]),
            "by_severity": severity_counts,
            "by_source": source_counts,
            "rule_matches": len(rule_results),
            "ml_detections": len(ml_prediction.detected_vulnerabilities),
            "agreement_rate": self._calculate_agreement_rate(rule_results, ml_prediction),
            "should_block_pipeline": any(v.severity == FusedSeverity.CRITICAL for v in fused_vulns),
            "requires_review": any(v.severity in [FusedSeverity.HIGH, FusedSeverity.MEDIUM] for v in fused_vulns),
        }
    
    def _calculate_agreement_rate(
        self,
        rule_results: List[RuleResult],
        ml_prediction: MLPrediction,
    ) -> float:
        """Calculate agreement rate between rules and ML."""
        if not rule_results:
            return 0.0
        
        agreements = 0
        for rule in rule_results:
            ml_vuln = self._find_ml_match(rule.cwe_id, ml_prediction)
            if ml_vuln and ml_vuln.probability >= self.ml_threshold:
                agreements += 1
        
        return agreements / len(rule_results)
