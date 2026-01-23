# Security AI Dataset Schema

## Overview

Production-grade dataset schema for AI-based security vulnerability detection system.

**Schema Version:** 1.0.0  
**Compatible With:** Local storage (Phase 1), Huawei OBS (Phase 2)

---

## Directory Structure

```
datasets/
├── security_vulns_v1_0_0/
│   ├── dataset_metadata.json          # Dataset-level metadata
│   │
│   ├── samples/                        # Raw samples organized by type
│   │   ├── source_code/               # Source code vulnerabilities
│   │   │   ├── python/
│   │   │   │   ├── batch_20260126.jsonl
│   │   │   │   └── batch_20260127.jsonl
│   │   │   ├── javascript/
│   │   │   ├── java/
│   │   │   ├── go/
│   │   │   └── typescript/
│   │   │
│   │   ├── configuration/             # Config file vulnerabilities
│   │   │   ├── yaml/
│   │   │   ├── json/
│   │   │   └── env/
│   │   │
│   │   └── api_security/              # API security samples
│   │       ├── openapi/
│   │       └── endpoints/
│   │
│   ├── feedback/                       # False positive/negative tracking
│   │   └── feedback_log.jsonl
│   │
│   ├── indices/                        # Quick lookup indices
│   │   ├── by_cwe.json
│   │   ├── by_severity.json
│   │   ├── by_language.json
│   │   └── by_domain.json
│   │
│   └── exports/                        # Training-ready exports
│       ├── tensorflow/
│       │   ├── train.jsonl
│       │   ├── val.jsonl
│       │   ├── test.jsonl
│       │   └── export_metadata.json
│       └── mindspore/                  # Phase 2: Huawei Cloud
│
└── security_vulns_v1_1_0/             # Incremental version
    ├── dataset_metadata.json
    └── ...
```

---

## Sample-Level Schema

### DatasetSample Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sample_id` | string (UUID) | ✅ | Unique identifier |
| `schema_version` | string | ✅ | Schema version (e.g., "1.0.0") |
| `sample_type` | enum | ✅ | `source_code`, `config_file`, `api_spec`, `api_endpoint` |
| `language` | string | ✅ | Programming/config language |
| `content` | string | ✅ | The actual code/config |
| `content_hash` | string | ✅ | SHA-256 hash for integrity |
| `labels` | LabelTaxonomy | ✅ | Classification labels |
| `context` | enum | ❌ | `web_application`, `microservice`, etc. |
| `location` | CodeLocation | ❌ | File path, line numbers |
| `framework` | string | ❌ | Framework (fastapi, django, express) |
| `dependencies` | string[] | ❌ | Related dependencies |
| `source` | string | ✅ | `manual`, `static_analysis`, `cve_database` |
| `source_url` | string | ❌ | Reference URL |
| `source_cve` | string | ❌ | CVE ID if applicable |
| `created_at` | ISO8601 | ✅ | Creation timestamp |
| `updated_at` | ISO8601 | ✅ | Last update timestamp |
| `created_by` | string | ❌ | Creator ID (anonymized) |
| `reviewed_by` | string | ❌ | Reviewer ID |
| `review_status` | string | ❌ | `pending`, `approved`, `rejected` |
| `dataset_version` | string | ✅ | Dataset version |
| `batch_id` | string | ❌ | Batch for incremental learning |
| `model_prediction` | object | ❌ | Model's prediction (for active learning) |
| `prediction_confidence` | float | ❌ | Prediction confidence |
| `feedback_history` | FeedbackRecord[] | ❌ | FP/FN tracking |
| `quality_score` | float | ❌ | Sample quality (0.0-1.0) |
| `tags` | string[] | ❌ | Custom tags |
| `notes` | string | ❌ | Additional notes |
| `extra_metadata` | object | ❌ | Extensible metadata |

### Example Sample (JSON)

```json
{
  "sample_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "schema_version": "1.0.0",
  "sample_type": "source_code",
  "language": "python",
  "content": "query = f\"SELECT * FROM users WHERE id = {user_id}\"",
  "content_hash": "sha256:abc123...",
  "labels": {
    "domain": "source_code",
    "cwe_ids": ["CWE-89"],
    "owasp_categories": ["A03:2021"],
    "severity": {
      "level": "critical",
      "cvss_score": 9.5,
      "exploitability": 0.9,
      "impact": 0.95,
      "confidence": 0.92
    },
    "is_vulnerable": true,
    "vulnerability_subtype": "sql_injection_fstring"
  },
  "context": "web_application",
  "location": {
    "file_path": "app/database.py",
    "start_line": 42,
    "end_line": 42,
    "function_name": "get_user"
  },
  "framework": "fastapi",
  "source": "manual",
  "created_at": "2026-01-26T10:00:00Z",
  "updated_at": "2026-01-26T10:00:00Z",
  "review_status": "approved",
  "dataset_version": "1.0.0",
  "batch_id": "20260126",
  "quality_score": 1.0,
  "tags": ["injection", "sql", "critical", "easy_fix"]
}
```

---

## Label Taxonomy

### Vulnerability Domain

| Value | Description |
|-------|-------------|
| `source_code` | Code-level vulnerabilities |
| `configuration` | Config/settings issues |
| `api_security` | API endpoint vulnerabilities |
| `infrastructure` | Infrastructure security |
| `authentication` | Auth/identity issues |
| `data_protection` | Data handling issues |

### CWE Categories (Common Weakness Enumeration)

| CWE ID | Name | Typical Severity |
|--------|------|------------------|
| CWE-89 | SQL Injection | Critical |
| CWE-78 | OS Command Injection | Critical |
| CWE-79 | Cross-site Scripting (XSS) | High |
| CWE-22 | Path Traversal | High |
| CWE-287 | Improper Authentication | High |
| CWE-306 | Missing Authentication | Critical |
| CWE-862 | Missing Authorization | High |
| CWE-798 | Hardcoded Credentials | Critical |
| CWE-327 | Broken Crypto Algorithm | High |
| CWE-502 | Insecure Deserialization | Critical |
| CWE-918 | Server-Side Request Forgery | High |
| CWE-778 | Insufficient Logging | Medium |
| CWE-16 | Security Misconfiguration | Medium |

### OWASP Top 10 (2021)

| Code | Category |
|------|----------|
| A01:2021 | Broken Access Control |
| A02:2021 | Cryptographic Failures |
| A03:2021 | Injection |
| A04:2021 | Insecure Design |
| A05:2021 | Security Misconfiguration |
| A06:2021 | Vulnerable Components |
| A07:2021 | Authentication Failures |
| A08:2021 | Data Integrity Failures |
| A09:2021 | Logging Failures |
| A10:2021 | SSRF |

### CWE → OWASP Mapping

```python
CWE_TO_OWASP = {
    "CWE-89":  ["A03:2021"],  # SQL Injection → Injection
    "CWE-78":  ["A03:2021"],  # Command Injection → Injection
    "CWE-79":  ["A03:2021"],  # XSS → Injection
    "CWE-22":  ["A01:2021"],  # Path Traversal → Broken Access Control
    "CWE-287": ["A07:2021"],  # Improper Auth → Auth Failures
    "CWE-798": ["A07:2021"],  # Hardcoded Creds → Auth Failures
    "CWE-327": ["A02:2021"],  # Broken Crypto → Crypto Failures
    "CWE-502": ["A08:2021"],  # Deserialization → Data Integrity
    "CWE-918": ["A10:2021"],  # SSRF → SSRF
    "CWE-16":  ["A05:2021"],  # Misconfig → Security Misconfiguration
    "CWE-778": ["A09:2021"],  # Logging → Logging Failures
}
```

---

## Severity Encoding

### CVSS-Aligned Levels

| Level | CVSS Range | Description |
|-------|------------|-------------|
| `critical` | 9.0 - 10.0 | Immediate exploitation possible, severe impact |
| `high` | 7.0 - 8.9 | Easy to exploit, significant impact |
| `medium` | 4.0 - 6.9 | Moderate difficulty, moderate impact |
| `low` | 0.1 - 3.9 | Difficult to exploit, limited impact |
| `info` | 0.0 | Informational only, no security impact |

### Severity Encoding Fields

```json
{
  "level": "critical",
  "cvss_score": 9.5,
  "exploitability": 0.9,    // 0.0-1.0: How easy to exploit
  "impact": 0.95,           // 0.0-1.0: Potential damage
  "confidence": 0.92,       // 0.0-1.0: Detection confidence
  "requires_authentication": false,
  "requires_user_interaction": false,
  "network_exploitable": true
}
```

---

## False Positive / False Negative Tracking

### FeedbackRecord Schema

| Field | Type | Description |
|-------|------|-------------|
| `feedback_id` | UUID | Unique feedback identifier |
| `sample_id` | UUID | Associated sample |
| `timestamp` | ISO8601 | When feedback was recorded |
| `is_false_positive` | bool | Model predicted vulnerable, but it's safe |
| `is_false_negative` | bool | Model predicted safe, but it's vulnerable |
| `corrected_label` | object | Corrected classification |
| `corrected_severity` | string | Corrected severity level |
| `reviewer_id` | string | Who provided feedback |
| `reviewer_notes` | string | Additional context |
| `model_version` | string | Model that made prediction |
| `used_for_retraining` | bool | Incorporated into training |
| `retraining_batch_id` | string | Which retraining batch |

### Example Feedback

```json
{
  "feedback_id": "fb-123456",
  "sample_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2026-01-26T14:30:00Z",
  "is_false_positive": true,
  "is_false_negative": false,
  "corrected_label": {
    "is_vulnerable": false,
    "reason": "Input is already validated upstream"
  },
  "reviewer_id": "reviewer_001",
  "reviewer_notes": "User input is sanitized in middleware before reaching this function",
  "model_version": "1.2.0",
  "used_for_retraining": false
}
```

---

## Incremental Learning Support

### Batch-Based Updates

1. **Batch ID Format:** `YYYYMMDD` or `YYYYMMDD_HHMMSS`
2. **Samples stored in:** `samples/{domain}/{language}/batch_{batch_id}.jsonl`
3. **Metadata tracks:** `batch_ids` array in dataset metadata

### Versioning Strategy

```
v1.0.0 → v1.1.0 → v1.2.0  (incremental batches)
       ↘ v2.0.0           (major schema change)
```

- **Patch (1.0.x):** Bug fixes, no schema changes
- **Minor (1.x.0):** New samples, new categories
- **Major (x.0.0):** Schema breaking changes

### Creating Incremental Version

```python
from app.security_ai.dataset import DatasetManager

manager = DatasetManager("./datasets")

# Create v1.1.0 from v1.0.0
new_metadata = manager.create_incremental_version(
    dataset_name="security_vulns",
    new_version="1.1.0",
    description="Added 500 new injection samples"
)

# Add new samples to the new version
manager.add_sample("security_vulns", new_sample)
```

---

## Usage Examples

### Creating a Dataset

```python
from app.security_ai.dataset import DatasetManager, DatasetSample, LabelTaxonomy
from app.security_ai.dataset.schema import *

manager = DatasetManager("./datasets")

# Create new dataset
metadata = manager.create_dataset(
    name="security_vulns",
    description="Security vulnerability training data",
    version="1.0.0",
    organization="Security Team"
)

# Create a sample
sample = DatasetSample(
    sample_type=SampleType.SOURCE_CODE,
    language="python",
    content='query = f"SELECT * FROM users WHERE id = {user_id}"',
    labels=LabelTaxonomy(
        domain=VulnerabilityDomain.SOURCE_CODE,
        cwe_ids=[CWECategory.CWE_89],
        owasp_categories=[OWASPCategory.A03_INJECTION],
        severity=SeverityEncoding.critical(),
        is_vulnerable=True
    ),
    framework="fastapi",
    tags=["sql_injection", "critical"]
)

# Add to dataset
manager.add_sample("security_vulns", sample)
```

### Querying Samples

```python
# Get all critical SQL injection samples
samples = manager.query_samples(
    "security_vulns",
    cwe_ids=["CWE-89"],
    severity="critical",
    language="python",
    limit=100
)

# Iterate all samples
for sample in manager.iterate_samples("security_vulns"):
    if sample.labels.is_vulnerable:
        print(f"{sample.sample_id}: {sample.labels.cwe_ids}")
```

### Recording Feedback

```python
# Mark a false positive
feedback = manager.add_feedback(
    dataset_name="security_vulns",
    sample_id="abc123",
    is_false_positive=True,
    reviewer_id="reviewer_001",
    reviewer_notes="Input validated upstream",
    model_version="1.0.0"
)
```

### Exporting for Training

```python
# Export for TensorFlow
paths = manager.export_for_tensorflow(
    "security_vulns",
    output_path="./training_data",
    split_ratio=(0.8, 0.1, 0.1)  # train/val/test
)

print(f"Train: {paths['train']}")
print(f"Val: {paths['val']}")
print(f"Test: {paths['test']}")

# Export for Huawei OBS (Phase 2)
archive = manager.export_for_huawei_obs(
    "security_vulns",
    output_path="./obs_export",
    compress=True
)
```

### Validation

```python
from app.security_ai.dataset import DatasetValidator

validator = DatasetValidator(strict_mode=False)

# Validate single sample
result = validator.validate_sample(sample)
if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error.field} - {error.message}")

# Validate entire dataset
result = validator.validate_dataset(manager, "security_vulns")
print(f"Validated {result.samples_validated} samples")
print(f"Passed: {result.samples_passed}")
print(f"Errors: {len(result.errors)}")
```

---

## Storage Portability

### Local Storage (Phase 1)

```
./datasets/security_vulns_v1_0_0/
```

### Huawei OBS (Phase 2)

```
obs://bucket-name/datasets/security_vulns_v1_0_0/
```

**No schema changes required** - the same JSONL format works in both environments.

### Migration Script

```python
# Export for Huawei OBS
manager.export_for_huawei_obs(
    "security_vulns",
    output_path="./obs_upload"
)

# Then use OBS SDK to upload
# from obs import ObsClient
# client.putFile("bucket", "datasets/security_vulns.tar.gz", "./obs_upload/security_vulns.tar.gz")
```

---

## Constraints & Design Decisions

| Constraint | Implementation |
|------------|----------------|
| No cloud dependency (Phase 1) | Local filesystem storage |
| Auditable & traceable | Every sample has UUID, timestamps, creator ID |
| CWE/OWASP aligned | Enum-based categories with mappings |
| Incremental learning | Batch IDs, version tracking, parent references |
| Portable to Huawei OBS | Standard JSONL format, tar.gz archives |
| False positive tracking | FeedbackRecord with correction details |
| Quality assurance | Review status, quality scores, validators |
