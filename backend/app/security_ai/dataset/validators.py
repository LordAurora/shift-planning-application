"""
Dataset Validators

Validation utilities for dataset integrity and quality assurance.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .schema import (
    DatasetSample,
    DatasetMetadata,
    LabelTaxonomy,
    CWECategory,
    OWASPCategory,
    SeverityLevel,
    VulnerabilityDomain,
    SampleType,
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Single validation error."""
    sample_id: str
    field: str
    error_type: str
    message: str
    severity: str = "error"  # error, warning, info


@dataclass
class ValidationResult:
    """Result of dataset validation."""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    samples_validated: int = 0
    samples_passed: int = 0
    validation_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": [
                {"sample_id": e.sample_id, "field": e.field, "error_type": e.error_type, "message": e.message}
                for e in self.errors
            ],
            "warnings": [
                {"sample_id": w.sample_id, "field": w.field, "error_type": w.error_type, "message": w.message}
                for w in self.warnings
            ],
            "samples_validated": self.samples_validated,
            "samples_passed": self.samples_passed,
            "validation_time": self.validation_time
        }


class DatasetValidator:
    """
    Validates dataset samples for completeness, correctness, and quality.
    
    Validation Checks:
    - Required fields present
    - Field types correct
    - CWE/OWASP mappings valid
    - Severity encoding valid
    - Content hash integrity
    - Label consistency
    - Cross-references valid
    
    Example:
        validator = DatasetValidator()
        
        # Validate single sample
        result = validator.validate_sample(sample)
        
        # Validate entire dataset
        from .manager import DatasetManager
        manager = DatasetManager()
        result = validator.validate_dataset(manager, "security_vulns")
    """
    
    # Valid CWE to OWASP mappings
    CWE_TO_OWASP = {
        CWECategory.CWE_89: [OWASPCategory.A03_INJECTION],
        CWECategory.CWE_78: [OWASPCategory.A03_INJECTION],
        CWECategory.CWE_94: [OWASPCategory.A03_INJECTION],
        CWECategory.CWE_79: [OWASPCategory.A03_INJECTION],
        CWECategory.CWE_287: [OWASPCategory.A07_AUTH_FAILURES],
        CWECategory.CWE_306: [OWASPCategory.A07_AUTH_FAILURES],
        CWECategory.CWE_798: [OWASPCategory.A07_AUTH_FAILURES],
        CWECategory.CWE_862: [OWASPCategory.A01_BROKEN_ACCESS_CONTROL],
        CWECategory.CWE_863: [OWASPCategory.A01_BROKEN_ACCESS_CONTROL],
        CWECategory.CWE_327: [OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES],
        CWECategory.CWE_328: [OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES],
        CWECategory.CWE_311: [OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES],
        CWECategory.CWE_312: [OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES],
        CWECategory.CWE_22: [OWASPCategory.A01_BROKEN_ACCESS_CONTROL],
        CWECategory.CWE_502: [OWASPCategory.A08_DATA_INTEGRITY_FAILURES],
        CWECategory.CWE_918: [OWASPCategory.A10_SSRF],
        CWECategory.CWE_16: [OWASPCategory.A05_SECURITY_MISCONFIGURATION],
        CWECategory.CWE_778: [OWASPCategory.A09_LOGGING_FAILURES],
    }
    
    # Valid severity score ranges
    SEVERITY_SCORE_RANGES = {
        SeverityLevel.CRITICAL: (9.0, 10.0),
        SeverityLevel.HIGH: (7.0, 8.9),
        SeverityLevel.MEDIUM: (4.0, 6.9),
        SeverityLevel.LOW: (0.1, 3.9),
        SeverityLevel.INFO: (0.0, 0.0),
    }
    
    # Required fields for different sample types
    REQUIRED_FIELDS = {
        "all": ["sample_id", "sample_type", "language", "content", "content_hash"],
        "labeled": ["labels"],
        "reviewed": ["reviewed_by", "review_status"],
    }
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator.
        
        Args:
            strict_mode: If True, warnings become errors
        """
        self.strict_mode = strict_mode
    
    def validate_sample(self, sample: DatasetSample) -> ValidationResult:
        """
        Validate a single dataset sample.
        
        Args:
            sample: DatasetSample to validate
        
        Returns:
            ValidationResult with errors and warnings
        """
        import time
        start_time = time.time()
        
        errors = []
        warnings = []
        
        # Check required fields
        errors.extend(self._check_required_fields(sample))
        
        # Validate content hash
        if not sample.verify_integrity():
            errors.append(ValidationError(
                sample_id=sample.sample_id,
                field="content_hash",
                error_type="integrity",
                message="Content hash does not match computed hash"
            ))
        
        # Validate labels if present
        if sample.labels:
            label_errors, label_warnings = self._validate_labels(sample)
            errors.extend(label_errors)
            warnings.extend(label_warnings)
        else:
            warnings.append(ValidationError(
                sample_id=sample.sample_id,
                field="labels",
                error_type="missing",
                message="Sample has no labels",
                severity="warning"
            ))
        
        # Validate sample type and language consistency
        type_errors = self._validate_type_consistency(sample)
        errors.extend(type_errors)
        
        # Validate timestamps
        timestamp_errors = self._validate_timestamps(sample)
        errors.extend(timestamp_errors)
        
        # Convert warnings to errors in strict mode
        if self.strict_mode:
            errors.extend(warnings)
            warnings = []
        
        validation_time = time.time() - start_time
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            samples_validated=1,
            samples_passed=1 if len(errors) == 0 else 0,
            validation_time=validation_time
        )
    
    def validate_dataset(
        self,
        manager,  # DatasetManager
        dataset_name: str,
        max_samples: Optional[int] = None
    ) -> ValidationResult:
        """
        Validate an entire dataset.
        
        Args:
            manager: DatasetManager instance
            dataset_name: Name of dataset to validate
            max_samples: Maximum samples to validate (for testing)
        
        Returns:
            ValidationResult with aggregated results
        """
        import time
        start_time = time.time()
        
        all_errors = []
        all_warnings = []
        samples_validated = 0
        samples_passed = 0
        
        sample_ids_seen = set()
        
        for sample in manager.iterate_samples(dataset_name):
            if max_samples and samples_validated >= max_samples:
                break
            
            # Check for duplicate IDs
            if sample.sample_id in sample_ids_seen:
                all_errors.append(ValidationError(
                    sample_id=sample.sample_id,
                    field="sample_id",
                    error_type="duplicate",
                    message=f"Duplicate sample ID: {sample.sample_id}"
                ))
            sample_ids_seen.add(sample.sample_id)
            
            # Validate sample
            result = self.validate_sample(sample)
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            
            samples_validated += 1
            if result.is_valid:
                samples_passed += 1
        
        validation_time = time.time() - start_time
        
        # Validate metadata
        try:
            metadata = manager.load_metadata(dataset_name)
            metadata_errors = self._validate_metadata(metadata, samples_validated)
            all_errors.extend(metadata_errors)
        except Exception as e:
            all_errors.append(ValidationError(
                sample_id="dataset",
                field="metadata",
                error_type="load_error",
                message=f"Failed to load metadata: {str(e)}"
            ))
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            samples_validated=samples_validated,
            samples_passed=samples_passed,
            validation_time=validation_time
        )
    
    def _check_required_fields(self, sample: DatasetSample) -> List[ValidationError]:
        """Check that all required fields are present and non-empty."""
        errors = []
        
        for field_name in self.REQUIRED_FIELDS["all"]:
            value = getattr(sample, field_name, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(ValidationError(
                    sample_id=sample.sample_id or "unknown",
                    field=field_name,
                    error_type="required",
                    message=f"Required field '{field_name}' is missing or empty"
                ))
        
        return errors
    
    def _validate_labels(self, sample: DatasetSample) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate label taxonomy."""
        errors = []
        warnings = []
        labels = sample.labels
        
        # Check CWE IDs are valid
        for cwe in labels.cwe_ids:
            if not isinstance(cwe, CWECategory):
                errors.append(ValidationError(
                    sample_id=sample.sample_id,
                    field="labels.cwe_ids",
                    error_type="invalid_type",
                    message=f"Invalid CWE type: {type(cwe)}"
                ))
        
        # Check OWASP categories are valid
        for owasp in labels.owasp_categories:
            if not isinstance(owasp, OWASPCategory):
                errors.append(ValidationError(
                    sample_id=sample.sample_id,
                    field="labels.owasp_categories",
                    error_type="invalid_type",
                    message=f"Invalid OWASP type: {type(owasp)}"
                ))
        
        # Check CWE to OWASP mapping consistency
        for cwe in labels.cwe_ids:
            expected_owasp = self.CWE_TO_OWASP.get(cwe, [])
            if expected_owasp:
                has_match = any(o in labels.owasp_categories for o in expected_owasp)
                if not has_match:
                    warnings.append(ValidationError(
                        sample_id=sample.sample_id,
                        field="labels",
                        error_type="mapping_mismatch",
                        message=f"CWE {cwe.value} typically maps to {[o.value for o in expected_owasp]}, "
                                f"but found {[o.value for o in labels.owasp_categories]}",
                        severity="warning"
                    ))
        
        # Validate severity encoding
        severity = labels.severity
        
        # Check CVSS score is in valid range
        if not 0.0 <= severity.cvss_score <= 10.0:
            errors.append(ValidationError(
                sample_id=sample.sample_id,
                field="labels.severity.cvss_score",
                error_type="range",
                message=f"CVSS score {severity.cvss_score} is out of range [0.0, 10.0]"
            ))
        
        # Check severity level matches CVSS score
        expected_range = self.SEVERITY_SCORE_RANGES.get(severity.level)
        if expected_range:
            min_score, max_score = expected_range
            if severity.level != SeverityLevel.INFO and not (min_score <= severity.cvss_score <= max_score):
                warnings.append(ValidationError(
                    sample_id=sample.sample_id,
                    field="labels.severity",
                    error_type="inconsistent",
                    message=f"Severity level {severity.level.value} expects CVSS {min_score}-{max_score}, "
                            f"but score is {severity.cvss_score}",
                    severity="warning"
                ))
        
        # Check probability fields are in [0, 1]
        for prob_field in ["exploitability", "impact", "confidence"]:
            value = getattr(severity, prob_field)
            if not 0.0 <= value <= 1.0:
                errors.append(ValidationError(
                    sample_id=sample.sample_id,
                    field=f"labels.severity.{prob_field}",
                    error_type="range",
                    message=f"{prob_field} value {value} is out of range [0.0, 1.0]"
                ))
        
        # Check vulnerable samples have at least one CWE
        if labels.is_vulnerable and not labels.cwe_ids:
            errors.append(ValidationError(
                sample_id=sample.sample_id,
                field="labels.cwe_ids",
                error_type="missing",
                message="Vulnerable sample must have at least one CWE ID"
            ))
        
        # Check safe samples don't have critical severity
        if not labels.is_vulnerable and severity.level == SeverityLevel.CRITICAL:
            errors.append(ValidationError(
                sample_id=sample.sample_id,
                field="labels",
                error_type="inconsistent",
                message="Non-vulnerable sample cannot have CRITICAL severity"
            ))
        
        return errors, warnings
    
    def _validate_type_consistency(self, sample: DatasetSample) -> List[ValidationError]:
        """Validate sample type and language are consistent."""
        errors = []
        
        # Code samples should have code-like languages
        code_languages = ["python", "javascript", "typescript", "java", "go", "rust", "c", "cpp", "csharp"]
        config_languages = ["yaml", "json", "toml", "ini", "env", "xml"]
        
        if sample.sample_type == SampleType.SOURCE_CODE:
            if sample.language.lower() not in code_languages:
                errors.append(ValidationError(
                    sample_id=sample.sample_id,
                    field="language",
                    error_type="inconsistent",
                    message=f"Source code sample has unexpected language: {sample.language}"
                ))
        
        elif sample.sample_type == SampleType.CONFIG_FILE:
            if sample.language.lower() not in config_languages:
                errors.append(ValidationError(
                    sample_id=sample.sample_id,
                    field="language",
                    error_type="inconsistent",
                    message=f"Config file sample has unexpected language: {sample.language}"
                ))
        
        return errors
    
    def _validate_timestamps(self, sample: DatasetSample) -> List[ValidationError]:
        """Validate timestamp fields."""
        errors = []
        
        try:
            if sample.created_at:
                datetime.fromisoformat(sample.created_at.replace('Z', '+00:00'))
        except ValueError:
            errors.append(ValidationError(
                sample_id=sample.sample_id,
                field="created_at",
                error_type="format",
                message=f"Invalid timestamp format: {sample.created_at}"
            ))
        
        try:
            if sample.updated_at:
                datetime.fromisoformat(sample.updated_at.replace('Z', '+00:00'))
        except ValueError:
            errors.append(ValidationError(
                sample_id=sample.sample_id,
                field="updated_at",
                error_type="format",
                message=f"Invalid timestamp format: {sample.updated_at}"
            ))
        
        # Check updated_at >= created_at
        if sample.created_at and sample.updated_at:
            try:
                created = datetime.fromisoformat(sample.created_at.replace('Z', '+00:00'))
                updated = datetime.fromisoformat(sample.updated_at.replace('Z', '+00:00'))
                if updated < created:
                    errors.append(ValidationError(
                        sample_id=sample.sample_id,
                        field="updated_at",
                        error_type="temporal",
                        message="updated_at cannot be earlier than created_at"
                    ))
            except ValueError:
                pass  # Already reported above
        
        return errors
    
    def _validate_metadata(self, metadata: DatasetMetadata, actual_count: int) -> List[ValidationError]:
        """Validate dataset metadata consistency."""
        errors = []
        
        # Check sample count matches
        if metadata.statistics.total_samples != actual_count:
            errors.append(ValidationError(
                sample_id="dataset",
                field="statistics.total_samples",
                error_type="inconsistent",
                message=f"Metadata reports {metadata.statistics.total_samples} samples, "
                        f"but found {actual_count}"
            ))
        
        # Check version format
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', metadata.version):
            errors.append(ValidationError(
                sample_id="dataset",
                field="version",
                error_type="format",
                message=f"Version '{metadata.version}' does not follow semantic versioning"
            ))
        
        return errors
