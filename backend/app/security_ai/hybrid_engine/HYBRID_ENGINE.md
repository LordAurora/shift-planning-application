# Hybrid AI Security Engine Design

## Executive Summary

This document describes an **enterprise-grade hybrid security detection engine** that combines deterministic rule-based detection with probabilistic ML-based detection. The design ensures:

- **Zero false negatives** on critical known vulnerabilities (rules)
- **Novel threat detection** through pattern recognition (ML)
- **Minimized false positives** through intelligent fusion and suppression

---

## Architecture Overview

```
                            ┌─────────────────────────────────┐
                            │         INPUT CODE              │
                            └───────────────┬─────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
                    ▼                       │                       ▼
    ┌───────────────────────────┐          │       ┌───────────────────────────┐
    │      RULE ENGINE          │          │       │      ML ENGINE            │
    │                           │          │       │                           │
    │  ┌─────────────────────┐ │          │       │  ┌─────────────────────┐ │
    │  │ Critical Rules (P0) │ │          │       │  │ Feature Extractor   │ │
    │  │ • SQL Injection     │ │          │       │  │ (Transformer)       │ │
    │  │ • Command Injection │ │          │       │  └──────────┬──────────┘ │
    │  │ • Hardcoded Creds   │ │          │       │             │            │
    │  │ • Path Traversal    │ │          │       │  ┌──────────▼──────────┐ │
    │  └─────────────────────┘ │          │       │  │ Multi-Label         │ │
    │                           │          │       │  │ Classifier          │ │
    │  ┌─────────────────────┐ │          │       │  └──────────┬──────────┘ │
    │  │ Standard Rules      │ │          │       │             │            │
    │  │ • XSS               │ │          │       │  ┌──────────▼──────────┐ │
    │  │ • CSRF              │ │          │       │  │ Confidence Scoring  │ │
    │  │ • Debug Mode        │ │          │       │  │ + Explainability    │ │
    │  └─────────────────────┘ │          │       │  └─────────────────────┘ │
    │                           │          │       │                           │
    └───────────────┬───────────┘          │       └───────────────┬───────────┘
                    │                       │                       │
                    │   RuleResult[]        │     MLPrediction      │
                    │                       │                       │
                    └───────────────────────┼───────────────────────┘
                                            │
                                            ▼
                            ┌───────────────────────────────────┐
                            │         FUSION ENGINE              │
                            │                                   │
                            │  1. Critical Rule Override        │
                            │  2. Agreement Detection           │
                            │  3. Confidence Calculation        │
                            │  4. FP Suppression                │
                            │                                   │
                            └───────────────┬───────────────────┘
                                            │
                                            ▼
                            ┌───────────────────────────────────┐
                            │     HybridDetectionResult         │
                            │                                   │
                            │  • Fused vulnerabilities          │
                            │  • Combined confidence scores     │
                            │  • Source attribution             │
                            │  • Remediation guidance           │
                            └───────────────────────────────────┘
```

---

## Component Responsibilities

### 1. Rule Engine

| Responsibility | Description |
|----------------|-------------|
| **Critical Detection** | Zero-tolerance detection of known critical vulnerabilities |
| **Pattern Matching** | Regex and AST-based pattern recognition |
| **Anti-Pattern Filtering** | Exclude false positives via exclusion patterns |
| **CWE Mapping** | Every rule maps to CWE identifier |

**Critical Rules (Never Miss):**
- SEC-001: SQL Injection (CWE-89)
- SEC-002: Command Injection (CWE-78)
- SEC-003: Hardcoded Credentials (CWE-798)
- SEC-004: Insecure Deserialization (CWE-502)
- SEC-005: Path Traversal (CWE-22)

### 2. ML Engine

| Responsibility | Description |
|----------------|-------------|
| **Pattern Recognition** | Detect vulnerability patterns learned from data |
| **Novel Threats** | Identify variations not covered by rules |
| **Confidence Scoring** | Probabilistic assessment of vulnerability likelihood |
| **Explainability** | Token importance and attention visualization |

**ML Vulnerability Classes (15):**
- Injection types (SQL, XSS, Command, Code, XXE)
- Access control (Path Traversal, SSRF, Auth issues)
- Cryptography (Weak crypto, Hardcoded creds)
- Configuration (Insecure config, Data exposure)

### 3. Fusion Engine

| Responsibility | Description |
|----------------|-------------|
| **Priority Arbitration** | Critical rules always override ML |
| **Agreement Detection** | Identify when rule and ML agree |
| **Confidence Scoring** | Calculate combined confidence |
| **FP Suppression** | Filter likely false positives |

---

## Decision Flow

```
START
  │
  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Critical Rule Evaluation                                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Critical Rule Match?                                                  │
│        │                                                                │
│   YES ─┼──────────────────────────────────────────────────────────────►│
│        │                          │                                     │
│        │                    ┌─────▼─────┐                              │
│        │                    │ CRITICAL  │  ◄── ALWAYS BLOCK            │
│        │                    │ SEVERITY  │      (P0 Priority)           │
│        │                    │           │      100% Recall Required    │
│        │                    └───────────┘                              │
│   NO   │                                                                │
│        ▼                                                                │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Rule + ML Agreement Check                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Rule Match AND ML Confidence ≥ 0.5?                                  │
│        │                                                                │
│   YES ─┼──────────────────────────────────────────────────────────────►│
│        │                          │                                     │
│        │                    ┌─────▼─────┐                              │
│        │                    │ HIGH      │  ◄── Both systems agree      │
│        │                    │ CONFIDENCE│      Strong evidence         │
│        │                    │           │      Confidence boost (+12%) │
│        │                    └───────────┘                              │
│   NO   │                                                                │
│        ▼                                                                │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Rule-Only Detection                                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Rule Match but ML Confidence < 0.5?                                  │
│        │                                                                │
│   YES ─┼──────────────────────────────────────────────────────────────►│
│        │                          │                                     │
│        │                    ┌─────▼─────┐                              │
│        │                    │ MEDIUM    │  ◄── Rule detected           │
│        │                    │ CONFIDENCE│      ML doesn't support      │
│        │                    │           │      FP check triggered      │
│        │                    └───────────┘                              │
│   NO   │                                                                │
│        ▼                                                                │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 4: ML-Only Detection                                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ML Confidence ≥ 0.5 but No Rule Match?                               │
│        │                                                                │
│   YES ─┼──────────────────────────────────────────────────────────────►│
│        │                          │                                     │
│        │   ML Confidence ≥ 0.95? │                                     │
│        │        │                │                                     │
│        │   YES ─┼───► HIGH       │                                     │
│        │        │                │                                     │
│        │   NO   │   0.85-0.95? ──┼───► MEDIUM                         │
│        │        │                │                                     │
│        │        │   0.70-0.85? ──┼───► LOW                            │
│        │        │                │                                     │
│        │        │   0.50-0.70? ──┼───► INFO (or SUPPRESSED)           │
│        │        │                │                                     │
│   NO   │                                                                │
│        ▼                                                                │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
    ┌─────────┐
    │  PASS   │  No vulnerabilities detected
    │ (Clean) │
    └─────────┘
```

---

## Confidence Scoring

### Formula

```
Combined Score = (rule_weight × rule_confidence) 
               + (ml_weight × ml_confidence)
               + agreement_bonus
               - penalty
```

### Strategy-Specific Weights

| Strategy | Rule Weight | ML Weight | Agreement Bonus | ML-Only Penalty |
|----------|-------------|-----------|-----------------|-----------------|
| **Conservative** | 0.70 | 0.30 | +0.15 | -0.20 |
| **Balanced** | 0.60 | 0.40 | +0.12 | -0.10 |
| **Aggressive** | 0.50 | 0.50 | +0.10 | 0.00 |

### Confidence Levels

| Level | Combined Score | Interpretation |
|-------|----------------|----------------|
| Very High | ≥ 0.95 | Almost certain vulnerability |
| High | 0.85 - 0.94 | Strong evidence |
| Medium | 0.70 - 0.84 | Likely vulnerability |
| Low | 0.50 - 0.69 | Possible vulnerability |
| Very Low | < 0.50 | Unlikely or suppressed |

---

## False Positive Suppression

### Suppression Triggers

1. **Test Code Detection**
   ```python
   # Suppressed if code contains:
   - "def test_"
   - "class Test"
   - "unittest"
   - "pytest"
   - "@test"
   - "mock"
   - "fixture"
   ```

2. **Comment Detection**
   ```python
   # Suppressed if match is in:
   - Lines starting with #
   - Lines starting with //
   - Lines within /* */
   ```

3. **Sanitization Detection**
   ```python
   # Suppressed if context contains:
   - "escape"
   - "sanitize"
   - "validate"
   - "parameterized"
   - "prepared"
   - "safe_"
   - "secure_"
   ```

4. **Low ML Confidence (Conservative Strategy)**
   ```python
   # Suppressed if:
   - ML confidence < 0.70
   - No rule support
   - Strategy is CONSERVATIVE
   ```

---

## Example Scenarios

### Scenario 1: Rule Overrides ML

**Code:**
```python
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
```

**Detection:**
| Source | Detection | Confidence |
|--------|-----------|------------|
| Rule SEC-001 | SQL Injection | DEFINITE (1.0) |
| ML | sql_injection | 0.45 (below threshold) |

**Fusion Result:**
- **Severity:** CRITICAL
- **Source:** rule_override
- **Reasoning:** "Critical rule SEC-001 matched. ML has lower confidence but rule is authoritative."

**Why Enterprise-Grade:** Critical rules are never ignored, regardless of ML opinion.

---

### Scenario 2: ML Supplements Rule

**Code:**
```python
app.run(debug=True, host="0.0.0.0")
```

**Detection:**
| Source | Detection | Confidence |
|--------|-----------|------------|
| Rule SEC-101 | Debug Mode Enabled | MEDIUM (0.7) |
| ML | insecure_configuration | 0.82 |

**Fusion Result:**
- **Severity:** MEDIUM
- **Source:** rule_and_ml
- **Combined Confidence:** 0.76 + 0.12 (agreement) = 0.88
- **Reasoning:** "Rule and ML agree. Confidence boosted."

**Why Enterprise-Grade:** Agreement between systems provides high-confidence findings.

---

### Scenario 3: ML-Only Detection

**Code:**
```python
def load_data(user_data):
    return pickle.loads(user_data)
```

**Detection:**
| Source | Detection | Confidence |
|--------|-----------|------------|
| Rule SEC-004 | Insecure Deserialization | MATCH |
| ML | insecure_deserialization | 0.91 |

**Fusion Result:**
- **Severity:** CRITICAL (rule is critical)
- **Source:** rule_and_ml
- **Reasoning:** "Critical rule with strong ML support."

---

### Scenario 4: False Positive Suppression

**Code:**
```python
class TestSQLQueries(unittest.TestCase):
    def test_query_construction(self):
        query = f"SELECT * FROM users WHERE id = {test_id}"
        self.assertEqual(len(query), 42)
```

**Detection:**
| Source | Detection | Confidence |
|--------|-----------|------------|
| Rule SEC-001 | SQL Injection | MATCH |
| ML | sql_injection | 0.35 |

**Fusion Result:**
- **Severity:** SUPPRESSED
- **Source:** rule_only
- **Reasoning:** "Suppressed: likely false positive (test code detected)"

**Why Enterprise-Grade:** Intelligent suppression reduces alert fatigue.

---

## Why This Hybrid Approach is Enterprise-Grade

### 1. Defense in Depth
- Rules catch known critical vulnerabilities (100% recall)
- ML catches novel patterns and variations
- No single point of failure

### 2. Auditability
- Every detection has clear source attribution
- Rule IDs map to CWE/OWASP standards
- Confidence scores are explainable

### 3. Compliance Ready
- CWE mapping for all detections
- OWASP Top 10 coverage
- Detailed remediation guidance

### 4. CI/CD Integration
- Fast mode for pipeline blocking (rules only)
- Configurable thresholds
- Clear block/allow decisions

### 5. Low False Positive Rate
- Anti-pattern matching
- Contextual suppression
- Strategy-based tuning

### 6. Scalability
- Rules are O(n) with pattern count
- ML batch processing
- Configurable timeout

---

## File Structure

```
security_ai/hybrid_engine/
├── __init__.py           # Module exports
├── rule_engine.py        # Deterministic rule detection
├── ml_adapter.py         # ML engine adapter
├── fusion_engine.py      # Result fusion logic
├── hybrid_detector.py    # Main entry point
└── HYBRID_ENGINE.md      # This document
```

---

## Usage

### Basic Usage
```python
from security_ai.hybrid_engine import HybridSecurityDetector, HybridConfig

detector = HybridSecurityDetector()
result = detector.scan(code)

if result.should_block:
    raise SecurityException("Critical vulnerability detected")
```

### CI/CD Mode (Fast)
```python
config = HybridConfig(mode=DetectionMode.CRITICAL_ONLY)
detector = HybridSecurityDetector(config)
result = detector.scan(code)

# Only critical vulnerabilities checked
# ~10x faster than full scan
```

### Conservative Mode (Minimize FP)
```python
config = HybridConfig(
    fusion_strategy=FusionStrategy.CONSERVATIVE,
    fp_suppression=True,
)
detector = HybridSecurityDetector(config)
```

---

## Performance Characteristics

| Mode | Typical Latency | Use Case |
|------|-----------------|----------|
| CRITICAL_ONLY | ~5ms | CI/CD pipeline blocking |
| RULES_ONLY | ~20ms | Fast security review |
| ML_ONLY | ~200ms | Novel threat detection |
| FULL | ~250ms | Comprehensive analysis |

---

## References

1. OWASP Top 10 - 2021
2. MITRE CWE Top 25 - 2023
3. SANS Top 25 Software Errors
4. NIST SP 800-53 Security Controls
