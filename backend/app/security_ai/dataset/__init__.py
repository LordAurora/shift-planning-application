"""
Security AI Dataset Package

Production-grade dataset management for vulnerability detection training.
Supports:
- Source code analysis datasets
- Configuration analysis datasets
- API security analysis datasets
- CWE/OWASP aligned labeling
- Incremental learning support
- Audit trail and traceability
"""

from .schema import (
    DatasetSample,
    DatasetMetadata,
    LabelTaxonomy,
    SeverityEncoding,
    FeedbackRecord,
    DatasetStatistics,
)
from .manager import DatasetManager
from .validators import DatasetValidator

__all__ = [
    "DatasetSample",
    "DatasetMetadata",
    "LabelTaxonomy",
    "SeverityEncoding",
    "FeedbackRecord",
    "DatasetStatistics",
    "DatasetManager",
    "DatasetValidator",
]
