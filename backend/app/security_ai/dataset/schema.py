"""
Dataset Schema Definitions

Production-grade schema for AI security vulnerability detection datasets.
Fully aligned with CWE/OWASP standards and designed for:
- Traceability and auditability
- Incremental learning compatibility
- Local storage (Phase 1) → Huawei OBS portable (Phase 2)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime
import json
import hashlib
import uuid


# =============================================================================
# LABEL TAXONOMY - CWE/OWASP Aligned
# =============================================================================

class VulnerabilityDomain(Enum):
    """High-level vulnerability domain classification."""
    SOURCE_CODE = "source_code"
    CONFIGURATION = "configuration"
    API_SECURITY = "api_security"
    INFRASTRUCTURE = "infrastructure"
    AUTHENTICATION = "authentication"
    DATA_PROTECTION = "data_protection"


class CWECategory(Enum):
    """
    Common Weakness Enumeration (CWE) categories.
    Reference: https://cwe.mitre.org/
    """
    # Injection Flaws
    CWE_89 = "CWE-89"    # SQL Injection
    CWE_78 = "CWE-78"    # OS Command Injection
    CWE_94 = "CWE-94"    # Code Injection
    CWE_917 = "CWE-917"  # Expression Language Injection
    
    # Authentication/Authorization
    CWE_287 = "CWE-287"  # Improper Authentication
    CWE_306 = "CWE-306"  # Missing Authentication
    CWE_862 = "CWE-862"  # Missing Authorization
    CWE_863 = "CWE-863"  # Incorrect Authorization
    CWE_798 = "CWE-798"  # Hardcoded Credentials
    
    # Cryptographic Issues
    CWE_327 = "CWE-327"  # Broken/Risky Crypto Algorithm
    CWE_328 = "CWE-328"  # Weak Hash
    CWE_330 = "CWE-330"  # Insufficient Randomness
    CWE_311 = "CWE-311"  # Missing Encryption
    CWE_312 = "CWE-312"  # Cleartext Storage
    
    # Input Validation
    CWE_79 = "CWE-79"    # Cross-site Scripting (XSS)
    CWE_22 = "CWE-22"    # Path Traversal
    CWE_20 = "CWE-20"    # Improper Input Validation
    CWE_601 = "CWE-601"  # Open Redirect
    
    # Data Exposure
    CWE_200 = "CWE-200"  # Information Exposure
    CWE_209 = "CWE-209"  # Error Message Information Leak
    CWE_532 = "CWE-532"  # Log File Information Exposure
    
    # Deserialization
    CWE_502 = "CWE-502"  # Deserialization of Untrusted Data
    
    # SSRF
    CWE_918 = "CWE-918"  # Server-Side Request Forgery
    
    # Security Misconfiguration
    CWE_16 = "CWE-16"    # Configuration
    CWE_1188 = "CWE-1188"  # Insecure Default Initialization
    
    # Logging/Monitoring
    CWE_778 = "CWE-778"  # Insufficient Logging
    
    # Memory Safety (for C/C++)
    CWE_119 = "CWE-119"  # Buffer Overflow
    CWE_416 = "CWE-416"  # Use After Free
    CWE_476 = "CWE-476"  # NULL Pointer Dereference
    
    # Other
    CWE_OTHER = "CWE-OTHER"


class OWASPCategory(Enum):
    """
    OWASP Top 10 2021 Categories.
    Reference: https://owasp.org/Top10/
    """
    A01_BROKEN_ACCESS_CONTROL = "A01:2021"
    A02_CRYPTOGRAPHIC_FAILURES = "A02:2021"
    A03_INJECTION = "A03:2021"
    A04_INSECURE_DESIGN = "A04:2021"
    A05_SECURITY_MISCONFIGURATION = "A05:2021"
    A06_VULNERABLE_COMPONENTS = "A06:2021"
    A07_AUTH_FAILURES = "A07:2021"
    A08_DATA_INTEGRITY_FAILURES = "A08:2021"
    A09_LOGGING_FAILURES = "A09:2021"
    A10_SSRF = "A10:2021"


class SeverityLevel(Enum):
    """
    CVSS-aligned severity levels.
    """
    CRITICAL = "critical"  # CVSS 9.0-10.0
    HIGH = "high"          # CVSS 7.0-8.9
    MEDIUM = "medium"      # CVSS 4.0-6.9
    LOW = "low"            # CVSS 0.1-3.9
    INFO = "info"          # Informational only


@dataclass
class SeverityEncoding:
    """
    Detailed severity encoding with CVSS-like scoring.
    """
    level: SeverityLevel
    cvss_score: float  # 0.0 - 10.0
    exploitability: float  # 0.0 - 1.0 (ease of exploitation)
    impact: float  # 0.0 - 1.0 (potential damage)
    confidence: float  # 0.0 - 1.0 (detection confidence)
    
    # Attack vector characteristics
    requires_authentication: bool = False
    requires_user_interaction: bool = False
    network_exploitable: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "cvss_score": self.cvss_score,
            "exploitability": self.exploitability,
            "impact": self.impact,
            "confidence": self.confidence,
            "requires_authentication": self.requires_authentication,
            "requires_user_interaction": self.requires_user_interaction,
            "network_exploitable": self.network_exploitable
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SeverityEncoding":
        return cls(
            level=SeverityLevel(data["level"]),
            cvss_score=data["cvss_score"],
            exploitability=data["exploitability"],
            impact=data["impact"],
            confidence=data["confidence"],
            requires_authentication=data.get("requires_authentication", False),
            requires_user_interaction=data.get("requires_user_interaction", False),
            network_exploitable=data.get("network_exploitable", True)
        )
    
    @classmethod
    def critical(cls, confidence: float = 0.9) -> "SeverityEncoding":
        return cls(
            level=SeverityLevel.CRITICAL,
            cvss_score=9.5,
            exploitability=0.9,
            impact=0.95,
            confidence=confidence,
            network_exploitable=True
        )
    
    @classmethod
    def high(cls, confidence: float = 0.85) -> "SeverityEncoding":
        return cls(
            level=SeverityLevel.HIGH,
            cvss_score=7.5,
            exploitability=0.7,
            impact=0.8,
            confidence=confidence
        )
    
    @classmethod
    def medium(cls, confidence: float = 0.8) -> "SeverityEncoding":
        return cls(
            level=SeverityLevel.MEDIUM,
            cvss_score=5.0,
            exploitability=0.5,
            impact=0.6,
            confidence=confidence
        )
    
    @classmethod
    def low(cls, confidence: float = 0.75) -> "SeverityEncoding":
        return cls(
            level=SeverityLevel.LOW,
            cvss_score=2.5,
            exploitability=0.3,
            impact=0.3,
            confidence=confidence
        )


@dataclass
class LabelTaxonomy:
    """
    Complete label taxonomy for a vulnerability sample.
    Supports multi-label classification with hierarchical categories.
    """
    # Primary classification
    domain: VulnerabilityDomain
    cwe_ids: List[CWECategory]
    owasp_categories: List[OWASPCategory]
    
    # Severity
    severity: SeverityEncoding
    
    # Custom labels for fine-grained classification
    custom_labels: List[str] = field(default_factory=list)
    
    # Is this a true vulnerability or safe code?
    is_vulnerable: bool = True
    
    # Sub-type for more specific classification
    vulnerability_subtype: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain.value,
            "cwe_ids": [cwe.value for cwe in self.cwe_ids],
            "owasp_categories": [owasp.value for owasp in self.owasp_categories],
            "severity": self.severity.to_dict(),
            "custom_labels": self.custom_labels,
            "is_vulnerable": self.is_vulnerable,
            "vulnerability_subtype": self.vulnerability_subtype
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LabelTaxonomy":
        return cls(
            domain=VulnerabilityDomain(data["domain"]),
            cwe_ids=[CWECategory(cwe) for cwe in data["cwe_ids"]],
            owasp_categories=[OWASPCategory(owasp) for owasp in data["owasp_categories"]],
            severity=SeverityEncoding.from_dict(data["severity"]),
            custom_labels=data.get("custom_labels", []),
            is_vulnerable=data.get("is_vulnerable", True),
            vulnerability_subtype=data.get("vulnerability_subtype")
        )


# =============================================================================
# SAMPLE SCHEMA
# =============================================================================

class SampleType(Enum):
    """Type of sample for domain-specific analysis."""
    SOURCE_CODE = "source_code"
    CONFIG_FILE = "config_file"
    API_SPEC = "api_spec"
    API_ENDPOINT = "api_endpoint"
    INFRASTRUCTURE = "infrastructure"
    LOG_PATTERN = "log_pattern"


class AnalysisContext(Enum):
    """Context in which the code/config operates."""
    WEB_APPLICATION = "web_application"
    MOBILE_BACKEND = "mobile_backend"
    MICROSERVICE = "microservice"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    INFRASTRUCTURE = "infrastructure"
    DATABASE = "database"
    AUTHENTICATION_SERVICE = "authentication_service"


@dataclass
class CodeLocation:
    """Precise location of vulnerability in source code."""
    file_path: str
    start_line: int
    end_line: int
    start_column: Optional[int] = None
    end_column: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_column": self.start_column,
            "end_column": self.end_column,
            "function_name": self.function_name,
            "class_name": self.class_name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeLocation":
        return cls(**data)


@dataclass
class FeedbackRecord:
    """
    Feedback for false positive/negative tracking and model improvement.
    """
    feedback_id: str
    sample_id: str
    timestamp: str
    
    # Feedback type
    is_false_positive: bool = False
    is_false_negative: bool = False
    
    # Correction
    corrected_label: Optional[Dict[str, Any]] = None
    corrected_severity: Optional[str] = None
    
    # Reviewer info
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    
    # Model version that produced the original prediction
    model_version: Optional[str] = None
    
    # Was this used for retraining?
    used_for_retraining: bool = False
    retraining_batch_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "sample_id": self.sample_id,
            "timestamp": self.timestamp,
            "is_false_positive": self.is_false_positive,
            "is_false_negative": self.is_false_negative,
            "corrected_label": self.corrected_label,
            "corrected_severity": self.corrected_severity,
            "reviewer_id": self.reviewer_id,
            "reviewer_notes": self.reviewer_notes,
            "model_version": self.model_version,
            "used_for_retraining": self.used_for_retraining,
            "retraining_batch_id": self.retraining_batch_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeedbackRecord":
        return cls(**data)


@dataclass
class DatasetSample:
    """
    Single dataset sample with full traceability and audit support.
    
    Schema Version: 1.0.0
    Compatible with: Local storage, Huawei OBS, S3-compatible storage
    """
    # ==========================================================================
    # IDENTIFICATION (Required)
    # ==========================================================================
    sample_id: str  # UUID for unique identification
    schema_version: str = "1.0.0"
    
    # ==========================================================================
    # CONTENT (Required)
    # ==========================================================================
    sample_type: SampleType
    language: str  # python, javascript, java, yaml, json, etc.
    content: str  # The actual code/config content
    content_hash: str = ""  # SHA-256 hash for integrity verification
    
    # ==========================================================================
    # LABELS (Required)
    # ==========================================================================
    labels: LabelTaxonomy = None
    
    # ==========================================================================
    # CONTEXT (Optional but recommended)
    # ==========================================================================
    context: AnalysisContext = AnalysisContext.WEB_APPLICATION
    location: Optional[CodeLocation] = None
    
    # Additional context
    framework: Optional[str] = None  # fastapi, django, express, spring, etc.
    dependencies: List[str] = field(default_factory=list)
    
    # ==========================================================================
    # PROVENANCE & TRACEABILITY (Required for audit)
    # ==========================================================================
    source: str = "manual"  # manual, static_analysis, dynamic_analysis, cve_database
    source_url: Optional[str] = None  # Reference URL if from public source
    source_cve: Optional[str] = None  # CVE ID if applicable
    
    # Timestamps
    created_at: str = ""
    updated_at: str = ""
    
    # Creator/annotator info (anonymized IDs for privacy)
    created_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_status: str = "pending"  # pending, approved, rejected
    
    # ==========================================================================
    # INCREMENTAL LEARNING SUPPORT
    # ==========================================================================
    dataset_version: str = "1.0.0"  # Version of the dataset this belongs to
    batch_id: Optional[str] = None  # Batch identifier for incremental updates
    
    # Model prediction (for active learning)
    model_prediction: Optional[Dict[str, Any]] = None
    prediction_confidence: Optional[float] = None
    
    # ==========================================================================
    # FEEDBACK & QUALITY TRACKING
    # ==========================================================================
    feedback_history: List[FeedbackRecord] = field(default_factory=list)
    quality_score: float = 1.0  # 0.0 - 1.0, based on review quality
    
    # ==========================================================================
    # METADATA
    # ==========================================================================
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    extra_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate computed fields."""
        if not self.sample_id:
            self.sample_id = str(uuid.uuid4())
        if not self.content_hash and self.content:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON storage."""
        return {
            "sample_id": self.sample_id,
            "schema_version": self.schema_version,
            "sample_type": self.sample_type.value,
            "language": self.language,
            "content": self.content,
            "content_hash": self.content_hash,
            "labels": self.labels.to_dict() if self.labels else None,
            "context": self.context.value,
            "location": self.location.to_dict() if self.location else None,
            "framework": self.framework,
            "dependencies": self.dependencies,
            "source": self.source,
            "source_url": self.source_url,
            "source_cve": self.source_cve,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "reviewed_by": self.reviewed_by,
            "review_status": self.review_status,
            "dataset_version": self.dataset_version,
            "batch_id": self.batch_id,
            "model_prediction": self.model_prediction,
            "prediction_confidence": self.prediction_confidence,
            "feedback_history": [f.to_dict() for f in self.feedback_history],
            "quality_score": self.quality_score,
            "tags": self.tags,
            "notes": self.notes,
            "extra_metadata": self.extra_metadata
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetSample":
        """Deserialize from dictionary."""
        labels = LabelTaxonomy.from_dict(data["labels"]) if data.get("labels") else None
        location = CodeLocation.from_dict(data["location"]) if data.get("location") else None
        feedback_history = [
            FeedbackRecord.from_dict(f) for f in data.get("feedback_history", [])
        ]
        
        return cls(
            sample_id=data["sample_id"],
            schema_version=data.get("schema_version", "1.0.0"),
            sample_type=SampleType(data["sample_type"]),
            language=data["language"],
            content=data["content"],
            content_hash=data.get("content_hash", ""),
            labels=labels,
            context=AnalysisContext(data.get("context", "web_application")),
            location=location,
            framework=data.get("framework"),
            dependencies=data.get("dependencies", []),
            source=data.get("source", "manual"),
            source_url=data.get("source_url"),
            source_cve=data.get("source_cve"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            created_by=data.get("created_by"),
            reviewed_by=data.get("reviewed_by"),
            review_status=data.get("review_status", "pending"),
            dataset_version=data.get("dataset_version", "1.0.0"),
            batch_id=data.get("batch_id"),
            model_prediction=data.get("model_prediction"),
            prediction_confidence=data.get("prediction_confidence"),
            feedback_history=feedback_history,
            quality_score=data.get("quality_score", 1.0),
            tags=data.get("tags", []),
            notes=data.get("notes"),
            extra_metadata=data.get("extra_metadata", {})
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "DatasetSample":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def add_feedback(
        self,
        is_false_positive: bool = False,
        is_false_negative: bool = False,
        corrected_label: Optional[Dict[str, Any]] = None,
        reviewer_id: Optional[str] = None,
        reviewer_notes: Optional[str] = None,
        model_version: Optional[str] = None
    ) -> FeedbackRecord:
        """Add feedback record for this sample."""
        feedback = FeedbackRecord(
            feedback_id=str(uuid.uuid4()),
            sample_id=self.sample_id,
            timestamp=datetime.utcnow().isoformat(),
            is_false_positive=is_false_positive,
            is_false_negative=is_false_negative,
            corrected_label=corrected_label,
            reviewer_id=reviewer_id,
            reviewer_notes=reviewer_notes,
            model_version=model_version
        )
        self.feedback_history.append(feedback)
        self.updated_at = datetime.utcnow().isoformat()
        return feedback
    
    def verify_integrity(self) -> bool:
        """Verify content integrity using hash."""
        computed_hash = hashlib.sha256(self.content.encode()).hexdigest()
        return computed_hash == self.content_hash


# =============================================================================
# DATASET METADATA
# =============================================================================

@dataclass
class DatasetStatistics:
    """Statistics for a dataset."""
    total_samples: int = 0
    vulnerable_samples: int = 0
    safe_samples: int = 0
    
    # By domain
    by_domain: Dict[str, int] = field(default_factory=dict)
    
    # By severity
    by_severity: Dict[str, int] = field(default_factory=dict)
    
    # By CWE
    by_cwe: Dict[str, int] = field(default_factory=dict)
    
    # By language
    by_language: Dict[str, int] = field(default_factory=dict)
    
    # Quality metrics
    reviewed_samples: int = 0
    false_positive_count: int = 0
    false_negative_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_samples": self.total_samples,
            "vulnerable_samples": self.vulnerable_samples,
            "safe_samples": self.safe_samples,
            "by_domain": self.by_domain,
            "by_severity": self.by_severity,
            "by_cwe": self.by_cwe,
            "by_language": self.by_language,
            "reviewed_samples": self.reviewed_samples,
            "false_positive_count": self.false_positive_count,
            "false_negative_count": self.false_negative_count
        }


@dataclass
class DatasetMetadata:
    """
    Metadata for an entire dataset.
    Stored as dataset_metadata.json in the dataset root.
    """
    # Identity
    dataset_id: str
    name: str
    description: str
    version: str = "1.0.0"
    schema_version: str = "1.0.0"
    
    # Timestamps
    created_at: str = ""
    updated_at: str = ""
    
    # Creator info
    created_by: Optional[str] = None
    organization: Optional[str] = None
    license: str = "proprietary"
    
    # Statistics
    statistics: DatasetStatistics = field(default_factory=DatasetStatistics)
    
    # Incremental learning
    parent_version: Optional[str] = None  # Previous version this was derived from
    batch_ids: List[str] = field(default_factory=list)  # All batch IDs included
    
    # Quality
    min_quality_score: float = 0.0
    review_required: bool = True
    
    # Storage info (for portability)
    storage_format: str = "jsonl"  # jsonl, parquet, tfrecord
    compression: Optional[str] = None  # gzip, lz4, etc.
    
    # Tags and notes
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    
    def __post_init__(self):
        if not self.dataset_id:
            self.dataset_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "organization": self.organization,
            "license": self.license,
            "statistics": self.statistics.to_dict(),
            "parent_version": self.parent_version,
            "batch_ids": self.batch_ids,
            "min_quality_score": self.min_quality_score,
            "review_required": self.review_required,
            "storage_format": self.storage_format,
            "compression": self.compression,
            "tags": self.tags,
            "notes": self.notes
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DatasetMetadata":
        stats_data = data.get("statistics", {})
        statistics = DatasetStatistics(
            total_samples=stats_data.get("total_samples", 0),
            vulnerable_samples=stats_data.get("vulnerable_samples", 0),
            safe_samples=stats_data.get("safe_samples", 0),
            by_domain=stats_data.get("by_domain", {}),
            by_severity=stats_data.get("by_severity", {}),
            by_cwe=stats_data.get("by_cwe", {}),
            by_language=stats_data.get("by_language", {}),
            reviewed_samples=stats_data.get("reviewed_samples", 0),
            false_positive_count=stats_data.get("false_positive_count", 0),
            false_negative_count=stats_data.get("false_negative_count", 0)
        )
        
        return cls(
            dataset_id=data["dataset_id"],
            name=data["name"],
            description=data["description"],
            version=data.get("version", "1.0.0"),
            schema_version=data.get("schema_version", "1.0.0"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            created_by=data.get("created_by"),
            organization=data.get("organization"),
            license=data.get("license", "proprietary"),
            statistics=statistics,
            parent_version=data.get("parent_version"),
            batch_ids=data.get("batch_ids", []),
            min_quality_score=data.get("min_quality_score", 0.0),
            review_required=data.get("review_required", True),
            storage_format=data.get("storage_format", "jsonl"),
            compression=data.get("compression"),
            tags=data.get("tags", []),
            notes=data.get("notes")
        )
