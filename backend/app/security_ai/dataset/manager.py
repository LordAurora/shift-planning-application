"""
Dataset Manager

Handles dataset CRUD operations, versioning, and storage.
Supports local storage (Phase 1) and Huawei OBS (Phase 2).
"""

import os
import json
import gzip
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator, Callable
from datetime import datetime
import uuid

from .schema import (
    DatasetSample,
    DatasetMetadata,
    DatasetStatistics,
    LabelTaxonomy,
    SeverityEncoding,
    FeedbackRecord,
    VulnerabilityDomain,
    CWECategory,
    OWASPCategory,
    SeverityLevel,
    SampleType,
)

logger = logging.getLogger(__name__)


class DatasetManager:
    """
    Production-grade dataset manager for security vulnerability datasets.
    
    Directory Structure:
    ```
    datasets/
    ├── security_vulns_v1/
    │   ├── dataset_metadata.json
    │   ├── samples/
    │   │   ├── source_code/
    │   │   │   ├── python/
    │   │   │   │   ├── batch_001.jsonl
    │   │   │   │   └── batch_002.jsonl
    │   │   │   ├── javascript/
    │   │   │   └── java/
    │   │   ├── configuration/
    │   │   │   ├── yaml/
    │   │   │   └── json/
    │   │   └── api_security/
    │   │       └── openapi/
    │   ├── feedback/
    │   │   └── feedback_log.jsonl
    │   ├── indices/
    │   │   ├── by_cwe.json
    │   │   ├── by_severity.json
    │   │   └── by_language.json
    │   └── exports/
    │       └── tensorflow/
    └── security_vulns_v2/
        └── ...
    ```
    
    Example:
        manager = DatasetManager("./datasets")
        
        # Create new dataset
        manager.create_dataset("security_vulns", "Security vulnerability samples")
        
        # Add samples
        sample = DatasetSample(...)
        manager.add_sample("security_vulns", sample)
        
        # Query samples
        samples = manager.query_samples(
            "security_vulns",
            cwe_ids=["CWE-89"],
            severity="critical"
        )
        
        # Export for training
        manager.export_for_tensorflow("security_vulns", "./exports")
    """
    
    def __init__(self, base_path: str = "./datasets"):
        """
        Initialize dataset manager.
        
        Args:
            base_path: Root directory for all datasets
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DatasetManager initialized at {self.base_path}")
    
    # =========================================================================
    # DATASET LIFECYCLE
    # =========================================================================
    
    def create_dataset(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        created_by: Optional[str] = None,
        organization: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> DatasetMetadata:
        """
        Create a new dataset with proper directory structure.
        
        Args:
            name: Dataset name (used as directory name)
            description: Dataset description
            version: Semantic version
            created_by: Creator identifier
            organization: Organization name
            tags: Dataset tags
        
        Returns:
            DatasetMetadata for the created dataset
        """
        dataset_path = self.base_path / f"{name}_v{version.replace('.', '_')}"
        
        if dataset_path.exists():
            raise ValueError(f"Dataset already exists: {dataset_path}")
        
        # Create directory structure
        directories = [
            dataset_path / "samples" / "source_code" / "python",
            dataset_path / "samples" / "source_code" / "javascript",
            dataset_path / "samples" / "source_code" / "java",
            dataset_path / "samples" / "source_code" / "go",
            dataset_path / "samples" / "source_code" / "typescript",
            dataset_path / "samples" / "configuration" / "yaml",
            dataset_path / "samples" / "configuration" / "json",
            dataset_path / "samples" / "configuration" / "env",
            dataset_path / "samples" / "api_security" / "openapi",
            dataset_path / "samples" / "api_security" / "endpoints",
            dataset_path / "feedback",
            dataset_path / "indices",
            dataset_path / "exports" / "tensorflow",
            dataset_path / "exports" / "mindspore",  # Phase 2
        ]
        
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create metadata
        metadata = DatasetMetadata(
            dataset_id=str(uuid.uuid4()),
            name=name,
            description=description,
            version=version,
            created_by=created_by,
            organization=organization,
            tags=tags or []
        )
        
        # Save metadata
        metadata_path = dataset_path / "dataset_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write(metadata.to_json())
        
        # Create empty index files
        for index_name in ["by_cwe", "by_severity", "by_language", "by_domain"]:
            index_path = dataset_path / "indices" / f"{index_name}.json"
            with open(index_path, 'w') as f:
                json.dump({}, f)
        
        logger.info(f"Created dataset: {name} v{version} at {dataset_path}")
        
        return metadata
    
    def get_dataset_path(self, name: str, version: Optional[str] = None) -> Path:
        """Get path to a dataset directory."""
        if version:
            return self.base_path / f"{name}_v{version.replace('.', '_')}"
        
        # Find latest version
        pattern = f"{name}_v*"
        matches = sorted(self.base_path.glob(pattern))
        if not matches:
            raise ValueError(f"Dataset not found: {name}")
        return matches[-1]
    
    def load_metadata(self, name: str, version: Optional[str] = None) -> DatasetMetadata:
        """Load dataset metadata."""
        dataset_path = self.get_dataset_path(name, version)
        metadata_path = dataset_path / "dataset_metadata.json"
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return DatasetMetadata.from_dict(data)
    
    def save_metadata(self, name: str, metadata: DatasetMetadata) -> None:
        """Save updated dataset metadata."""
        dataset_path = self.get_dataset_path(name, metadata.version)
        metadata_path = dataset_path / "dataset_metadata.json"
        
        metadata.updated_at = datetime.utcnow().isoformat()
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write(metadata.to_json())
    
    def list_datasets(self) -> List[Dict[str, Any]]:
        """List all available datasets."""
        datasets = []
        
        for path in self.base_path.iterdir():
            if path.is_dir():
                metadata_file = path / "dataset_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        data = json.load(f)
                    datasets.append({
                        "name": data["name"],
                        "version": data["version"],
                        "description": data["description"],
                        "total_samples": data.get("statistics", {}).get("total_samples", 0),
                        "path": str(path)
                    })
        
        return datasets
    
    # =========================================================================
    # SAMPLE MANAGEMENT
    # =========================================================================
    
    def add_sample(
        self,
        dataset_name: str,
        sample: DatasetSample,
        batch_id: Optional[str] = None
    ) -> str:
        """
        Add a sample to the dataset.
        
        Args:
            dataset_name: Name of the dataset
            sample: DatasetSample to add
            batch_id: Optional batch identifier for incremental updates
        
        Returns:
            Sample ID
        """
        metadata = self.load_metadata(dataset_name)
        dataset_path = self.get_dataset_path(dataset_name, metadata.version)
        
        # Determine storage path
        sample_dir = self._get_sample_directory(dataset_path, sample)
        
        # Generate batch ID if not provided
        if not batch_id:
            batch_id = datetime.utcnow().strftime("%Y%m%d")
        
        sample.batch_id = batch_id
        sample.dataset_version = metadata.version
        
        # Append to batch file (JSONL format)
        batch_file = sample_dir / f"batch_{batch_id}.jsonl"
        with open(batch_file, 'a', encoding='utf-8') as f:
            f.write(sample.to_json().replace('\n', ' ') + '\n')
        
        # Update indices
        self._update_indices(dataset_path, sample)
        
        # Update statistics
        self._update_statistics(metadata, sample)
        self.save_metadata(dataset_name, metadata)
        
        logger.debug(f"Added sample {sample.sample_id} to {dataset_name}")
        
        return sample.sample_id
    
    def add_samples_batch(
        self,
        dataset_name: str,
        samples: List[DatasetSample],
        batch_id: Optional[str] = None
    ) -> List[str]:
        """Add multiple samples in a batch for efficiency."""
        if not batch_id:
            batch_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        sample_ids = []
        for sample in samples:
            sample_id = self.add_sample(dataset_name, sample, batch_id)
            sample_ids.append(sample_id)
        
        logger.info(f"Added batch of {len(samples)} samples to {dataset_name}")
        return sample_ids
    
    def get_sample(self, dataset_name: str, sample_id: str) -> Optional[DatasetSample]:
        """Retrieve a specific sample by ID."""
        for sample in self.iterate_samples(dataset_name):
            if sample.sample_id == sample_id:
                return sample
        return None
    
    def iterate_samples(
        self,
        dataset_name: str,
        filter_fn: Optional[Callable[[DatasetSample], bool]] = None
    ) -> Iterator[DatasetSample]:
        """
        Iterate through all samples in a dataset.
        
        Args:
            dataset_name: Name of the dataset
            filter_fn: Optional filter function
        
        Yields:
            DatasetSample objects
        """
        metadata = self.load_metadata(dataset_name)
        dataset_path = self.get_dataset_path(dataset_name, metadata.version)
        samples_dir = dataset_path / "samples"
        
        for jsonl_file in samples_dir.rglob("*.jsonl"):
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        sample = DatasetSample.from_json(line)
                        if filter_fn is None or filter_fn(sample):
                            yield sample
    
    def query_samples(
        self,
        dataset_name: str,
        cwe_ids: Optional[List[str]] = None,
        owasp_categories: Optional[List[str]] = None,
        severity: Optional[str] = None,
        language: Optional[str] = None,
        domain: Optional[str] = None,
        is_vulnerable: Optional[bool] = None,
        review_status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[DatasetSample]:
        """
        Query samples with filters.
        
        Args:
            dataset_name: Name of the dataset
            cwe_ids: Filter by CWE IDs
            owasp_categories: Filter by OWASP categories
            severity: Filter by severity level
            language: Filter by programming language
            domain: Filter by vulnerability domain
            is_vulnerable: Filter by vulnerability status
            review_status: Filter by review status
            limit: Maximum number of results
        
        Returns:
            List of matching DatasetSample objects
        """
        def filter_fn(sample: DatasetSample) -> bool:
            if cwe_ids and sample.labels:
                sample_cwes = [cwe.value for cwe in sample.labels.cwe_ids]
                if not any(cwe in sample_cwes for cwe in cwe_ids):
                    return False
            
            if owasp_categories and sample.labels:
                sample_owasp = [o.value for o in sample.labels.owasp_categories]
                if not any(o in sample_owasp for o in owasp_categories):
                    return False
            
            if severity and sample.labels:
                if sample.labels.severity.level.value != severity:
                    return False
            
            if language and sample.language != language:
                return False
            
            if domain and sample.labels:
                if sample.labels.domain.value != domain:
                    return False
            
            if is_vulnerable is not None and sample.labels:
                if sample.labels.is_vulnerable != is_vulnerable:
                    return False
            
            if review_status and sample.review_status != review_status:
                return False
            
            return True
        
        results = []
        for sample in self.iterate_samples(dataset_name, filter_fn):
            results.append(sample)
            if limit and len(results) >= limit:
                break
        
        return results
    
    def _get_sample_directory(self, dataset_path: Path, sample: DatasetSample) -> Path:
        """Determine the appropriate directory for a sample."""
        samples_dir = dataset_path / "samples"
        
        if sample.sample_type == SampleType.SOURCE_CODE:
            return samples_dir / "source_code" / sample.language
        elif sample.sample_type == SampleType.CONFIG_FILE:
            lang = sample.language if sample.language in ["yaml", "json", "env"] else "other"
            return samples_dir / "configuration" / lang
        elif sample.sample_type in [SampleType.API_SPEC, SampleType.API_ENDPOINT]:
            return samples_dir / "api_security" / "endpoints"
        else:
            return samples_dir / "other"
    
    def _update_indices(self, dataset_path: Path, sample: DatasetSample) -> None:
        """Update index files with new sample."""
        indices_dir = dataset_path / "indices"
        
        if not sample.labels:
            return
        
        # Update CWE index
        cwe_index_path = indices_dir / "by_cwe.json"
        with open(cwe_index_path, 'r') as f:
            cwe_index = json.load(f)
        
        for cwe in sample.labels.cwe_ids:
            if cwe.value not in cwe_index:
                cwe_index[cwe.value] = []
            cwe_index[cwe.value].append(sample.sample_id)
        
        with open(cwe_index_path, 'w') as f:
            json.dump(cwe_index, f, indent=2)
        
        # Update severity index
        severity_index_path = indices_dir / "by_severity.json"
        with open(severity_index_path, 'r') as f:
            severity_index = json.load(f)
        
        severity = sample.labels.severity.level.value
        if severity not in severity_index:
            severity_index[severity] = []
        severity_index[severity].append(sample.sample_id)
        
        with open(severity_index_path, 'w') as f:
            json.dump(severity_index, f, indent=2)
        
        # Update language index
        lang_index_path = indices_dir / "by_language.json"
        with open(lang_index_path, 'r') as f:
            lang_index = json.load(f)
        
        if sample.language not in lang_index:
            lang_index[sample.language] = []
        lang_index[sample.language].append(sample.sample_id)
        
        with open(lang_index_path, 'w') as f:
            json.dump(lang_index, f, indent=2)
    
    def _update_statistics(self, metadata: DatasetMetadata, sample: DatasetSample) -> None:
        """Update dataset statistics."""
        stats = metadata.statistics
        stats.total_samples += 1
        
        if sample.labels:
            if sample.labels.is_vulnerable:
                stats.vulnerable_samples += 1
            else:
                stats.safe_samples += 1
            
            # By domain
            domain = sample.labels.domain.value
            stats.by_domain[domain] = stats.by_domain.get(domain, 0) + 1
            
            # By severity
            severity = sample.labels.severity.level.value
            stats.by_severity[severity] = stats.by_severity.get(severity, 0) + 1
            
            # By CWE
            for cwe in sample.labels.cwe_ids:
                stats.by_cwe[cwe.value] = stats.by_cwe.get(cwe.value, 0) + 1
        
        # By language
        stats.by_language[sample.language] = stats.by_language.get(sample.language, 0) + 1
    
    # =========================================================================
    # FEEDBACK MANAGEMENT
    # =========================================================================
    
    def add_feedback(
        self,
        dataset_name: str,
        sample_id: str,
        is_false_positive: bool = False,
        is_false_negative: bool = False,
        corrected_label: Optional[Dict[str, Any]] = None,
        reviewer_id: Optional[str] = None,
        reviewer_notes: Optional[str] = None,
        model_version: Optional[str] = None
    ) -> FeedbackRecord:
        """
        Add feedback for a sample (false positive/negative tracking).
        
        Args:
            dataset_name: Name of the dataset
            sample_id: ID of the sample
            is_false_positive: Was this a false positive?
            is_false_negative: Was this a false negative?
            corrected_label: Corrected label if any
            reviewer_id: Reviewer identifier
            reviewer_notes: Additional notes
            model_version: Model version that made the prediction
        
        Returns:
            FeedbackRecord
        """
        metadata = self.load_metadata(dataset_name)
        dataset_path = self.get_dataset_path(dataset_name, metadata.version)
        
        feedback = FeedbackRecord(
            feedback_id=str(uuid.uuid4()),
            sample_id=sample_id,
            timestamp=datetime.utcnow().isoformat(),
            is_false_positive=is_false_positive,
            is_false_negative=is_false_negative,
            corrected_label=corrected_label,
            reviewer_id=reviewer_id,
            reviewer_notes=reviewer_notes,
            model_version=model_version
        )
        
        # Append to feedback log
        feedback_file = dataset_path / "feedback" / "feedback_log.jsonl"
        with open(feedback_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback.to_dict()) + '\n')
        
        # Update statistics
        if is_false_positive:
            metadata.statistics.false_positive_count += 1
        if is_false_negative:
            metadata.statistics.false_negative_count += 1
        
        self.save_metadata(dataset_name, metadata)
        
        logger.info(f"Added feedback {feedback.feedback_id} for sample {sample_id}")
        
        return feedback
    
    def get_feedback_history(self, dataset_name: str) -> List[FeedbackRecord]:
        """Get all feedback records for a dataset."""
        metadata = self.load_metadata(dataset_name)
        dataset_path = self.get_dataset_path(dataset_name, metadata.version)
        feedback_file = dataset_path / "feedback" / "feedback_log.jsonl"
        
        feedback_records = []
        if feedback_file.exists():
            with open(feedback_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        feedback_records.append(FeedbackRecord.from_dict(data))
        
        return feedback_records
    
    # =========================================================================
    # EXPORT & VERSIONING
    # =========================================================================
    
    def export_for_tensorflow(
        self,
        dataset_name: str,
        output_path: Optional[str] = None,
        split_ratio: tuple = (0.8, 0.1, 0.1),
        include_safe_samples: bool = True
    ) -> Dict[str, str]:
        """
        Export dataset in TensorFlow-compatible format.
        
        Args:
            dataset_name: Name of the dataset
            output_path: Output directory (defaults to dataset exports dir)
            split_ratio: Train/val/test split ratio
            include_safe_samples: Include non-vulnerable samples
        
        Returns:
            Dictionary with paths to train/val/test files
        """
        metadata = self.load_metadata(dataset_name)
        dataset_path = self.get_dataset_path(dataset_name, metadata.version)
        
        if not output_path:
            output_path = dataset_path / "exports" / "tensorflow"
        else:
            output_path = Path(output_path)
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Collect all samples
        all_samples = []
        for sample in self.iterate_samples(dataset_name):
            if not include_safe_samples and sample.labels and not sample.labels.is_vulnerable:
                continue
            all_samples.append(sample)
        
        # Shuffle
        import random
        random.shuffle(all_samples)
        
        # Split
        n = len(all_samples)
        train_end = int(n * split_ratio[0])
        val_end = train_end + int(n * split_ratio[1])
        
        train_samples = all_samples[:train_end]
        val_samples = all_samples[train_end:val_end]
        test_samples = all_samples[val_end:]
        
        # Write files
        paths = {}
        for split_name, samples in [("train", train_samples), ("val", val_samples), ("test", test_samples)]:
            file_path = output_path / f"{split_name}.jsonl"
            with open(file_path, 'w', encoding='utf-8') as f:
                for sample in samples:
                    f.write(sample.to_json().replace('\n', ' ') + '\n')
            paths[split_name] = str(file_path)
        
        # Write metadata
        export_meta = {
            "dataset_name": dataset_name,
            "dataset_version": metadata.version,
            "exported_at": datetime.utcnow().isoformat(),
            "total_samples": len(all_samples),
            "train_samples": len(train_samples),
            "val_samples": len(val_samples),
            "test_samples": len(test_samples),
            "split_ratio": split_ratio
        }
        
        with open(output_path / "export_metadata.json", 'w') as f:
            json.dump(export_meta, f, indent=2)
        
        logger.info(f"Exported {len(all_samples)} samples for TensorFlow training")
        
        return paths
    
    def create_incremental_version(
        self,
        dataset_name: str,
        new_version: str,
        description: Optional[str] = None
    ) -> DatasetMetadata:
        """
        Create a new version of the dataset for incremental updates.
        
        Args:
            dataset_name: Name of the existing dataset
            new_version: New semantic version
            description: Description of changes
        
        Returns:
            DatasetMetadata for the new version
        """
        current_metadata = self.load_metadata(dataset_name)
        current_path = self.get_dataset_path(dataset_name, current_metadata.version)
        
        # Create new dataset with reference to parent
        new_metadata = self.create_dataset(
            name=dataset_name,
            description=description or current_metadata.description,
            version=new_version,
            created_by=current_metadata.created_by,
            organization=current_metadata.organization,
            tags=current_metadata.tags
        )
        
        new_metadata.parent_version = current_metadata.version
        new_metadata.batch_ids = current_metadata.batch_ids.copy()
        
        new_path = self.get_dataset_path(dataset_name, new_version)
        
        # Copy samples from parent (create symlinks for efficiency)
        src_samples = current_path / "samples"
        dst_samples = new_path / "samples"
        
        if dst_samples.exists():
            shutil.rmtree(dst_samples)
        shutil.copytree(src_samples, dst_samples)
        
        # Copy indices
        src_indices = current_path / "indices"
        dst_indices = new_path / "indices"
        
        if dst_indices.exists():
            shutil.rmtree(dst_indices)
        shutil.copytree(src_indices, dst_indices)
        
        # Copy statistics
        new_metadata.statistics = current_metadata.statistics
        
        self.save_metadata(dataset_name, new_metadata)
        
        logger.info(f"Created incremental version {new_version} from {current_metadata.version}")
        
        return new_metadata
    
    # =========================================================================
    # HUAWEI OBS COMPATIBILITY (Phase 2)
    # =========================================================================
    
    def export_for_huawei_obs(
        self,
        dataset_name: str,
        output_path: str,
        compress: bool = True
    ) -> str:
        """
        Export dataset in Huawei OBS compatible format.
        Phase 2: Will be uploaded to OBS bucket.
        
        Args:
            dataset_name: Name of the dataset
            output_path: Output directory
            compress: Whether to compress the output
        
        Returns:
            Path to exported archive
        """
        metadata = self.load_metadata(dataset_name)
        dataset_path = self.get_dataset_path(dataset_name, metadata.version)
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        archive_name = f"{dataset_name}_v{metadata.version.replace('.', '_')}"
        
        if compress:
            archive_path = output_path / f"{archive_name}.tar.gz"
            shutil.make_archive(
                str(output_path / archive_name),
                'gztar',
                dataset_path
            )
        else:
            archive_path = output_path / archive_name
            shutil.copytree(dataset_path, archive_path)
        
        logger.info(f"Exported dataset for Huawei OBS: {archive_path}")
        
        return str(archive_path)
