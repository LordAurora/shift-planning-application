"""
Continuous Learning Module

Enables automated and manual improvement cycles:
- Misclassification logging and analysis
- Human feedback integration
- Automated retraining triggers
- Pipeline orchestration
"""

import numpy as np
import logging
import json
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# MISCLASSIFICATION LOGGER
# =============================================================================

class MisclassificationType(Enum):
    FALSE_POSITIVE = "false_positive"  # Flagged clean code
    FALSE_NEGATIVE = "false_negative"  # Missed vulnerability
    WRONG_CLASS = "wrong_class"        # Detected, but wrong type


@dataclass
class MisclassificationRecord:
    """Record of a single misclassification."""
    record_id: str
    timestamp: str
    code_snippet: str
    code_hash: str  # For deduplication
    
    # Classification details
    misclass_type: MisclassificationType
    predicted_classes: List[str]
    actual_classes: List[str]
    confidence_scores: Dict[str, float]
    
    # Context
    source_file: Optional[str] = None
    line_number: Optional[int] = None
    project_context: Optional[str] = None
    
    # Feedback
    human_verified: bool = False
    verified_by: Optional[str] = None
    verification_date: Optional[str] = None
    corrected_labels: Optional[List[str]] = None
    
    # Analysis
    pattern_category: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "code_snippet": self.code_snippet,
            "code_hash": self.code_hash,
            "misclass_type": self.misclass_type.value,
            "predicted_classes": self.predicted_classes,
            "actual_classes": self.actual_classes,
            "confidence_scores": self.confidence_scores,
            "source_file": self.source_file,
            "line_number": self.line_number,
            "project_context": self.project_context,
            "human_verified": self.human_verified,
            "verified_by": self.verified_by,
            "verification_date": self.verification_date,
            "corrected_labels": self.corrected_labels,
            "pattern_category": self.pattern_category,
            "notes": self.notes,
        }


class MisclassificationLogger:
    """
    Log and analyze model misclassifications.
    
    Features:
    - Automatic logging during inference
    - Deduplication by code hash
    - Pattern analysis
    - Export for retraining
    """
    
    def __init__(self, storage_path: str = "misclassifications"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.records: List[MisclassificationRecord] = []
        self.seen_hashes: set = set()
        
        # Load existing records
        self._load_records()
    
    def _load_records(self):
        """Load existing records from storage."""
        records_file = self.storage_path / "records.json"
        if records_file.exists():
            with open(records_file, 'r') as f:
                data = json.load(f)
                for item in data:
                    item["misclass_type"] = MisclassificationType(item["misclass_type"])
                    record = MisclassificationRecord(**item)
                    self.records.append(record)
                    self.seen_hashes.add(record.code_hash)
            
            logger.info(f"Loaded {len(self.records)} misclassification records")
    
    def _save_records(self):
        """Save records to storage."""
        records_file = self.storage_path / "records.json"
        with open(records_file, 'w') as f:
            json.dump([r.to_dict() for r in self.records], f, indent=2)
    
    def _hash_code(self, code: str) -> str:
        """Generate hash for code snippet."""
        normalized = code.strip().lower()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def log_misclassification(
        self,
        code: str,
        predicted_classes: List[str],
        actual_classes: List[str],
        confidence_scores: Dict[str, float],
        source_file: Optional[str] = None,
        line_number: Optional[int] = None,
        project_context: Optional[str] = None,
    ) -> Optional[MisclassificationRecord]:
        """
        Log a misclassification.
        
        Args:
            code: Code snippet
            predicted_classes: Model predictions
            actual_classes: Ground truth labels
            confidence_scores: Confidence per class
            source_file: Source file path
            line_number: Line number in file
            project_context: Project/context info
        
        Returns:
            MisclassificationRecord or None if duplicate
        """
        code_hash = self._hash_code(code)
        
        # Skip duplicates
        if code_hash in self.seen_hashes:
            logger.debug(f"Skipping duplicate misclassification: {code_hash}")
            return None
        
        # Determine type
        predicted_set = set(predicted_classes)
        actual_set = set(actual_classes)
        
        if actual_set and not predicted_set.intersection(actual_set):
            if predicted_set:
                misclass_type = MisclassificationType.WRONG_CLASS
            else:
                misclass_type = MisclassificationType.FALSE_NEGATIVE
        else:
            misclass_type = MisclassificationType.FALSE_POSITIVE
        
        record = MisclassificationRecord(
            record_id=f"mc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{code_hash[:8]}",
            timestamp=datetime.now().isoformat(),
            code_snippet=code[:2000],  # Limit size
            code_hash=code_hash,
            misclass_type=misclass_type,
            predicted_classes=predicted_classes,
            actual_classes=actual_classes,
            confidence_scores=confidence_scores,
            source_file=source_file,
            line_number=line_number,
            project_context=project_context,
        )
        
        self.records.append(record)
        self.seen_hashes.add(code_hash)
        self._save_records()
        
        logger.info(
            f"Logged {misclass_type.value}: "
            f"predicted={predicted_classes}, actual={actual_classes}"
        )
        
        return record
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze misclassification patterns."""
        analysis = {
            "total_records": len(self.records),
            "by_type": {
                "false_positive": 0,
                "false_negative": 0,
                "wrong_class": 0,
            },
            "by_class": {},
            "verified_count": 0,
            "pending_review": 0,
            "common_patterns": [],
        }
        
        # Count by type
        for record in self.records:
            analysis["by_type"][record.misclass_type.value] += 1
            
            if record.human_verified:
                analysis["verified_count"] += 1
            else:
                analysis["pending_review"] += 1
            
            # Count by class
            for cls in record.actual_classes:
                analysis["by_class"].setdefault(cls, {"fn": 0, "fp": 0})
                if record.misclass_type == MisclassificationType.FALSE_NEGATIVE:
                    analysis["by_class"][cls]["fn"] += 1
            
            for cls in record.predicted_classes:
                if cls not in record.actual_classes:
                    analysis["by_class"].setdefault(cls, {"fn": 0, "fp": 0})
                    analysis["by_class"][cls]["fp"] += 1
        
        # Find common patterns (classes with most errors)
        class_errors = [
            (cls, data["fn"] + data["fp"])
            for cls, data in analysis["by_class"].items()
        ]
        class_errors.sort(key=lambda x: x[1], reverse=True)
        analysis["common_patterns"] = class_errors[:5]
        
        return analysis
    
    def get_unverified(self) -> List[MisclassificationRecord]:
        """Get records pending human review."""
        return [r for r in self.records if not r.human_verified]
    
    def export_for_retraining(
        self,
        verified_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Export records for retraining dataset.
        
        Args:
            verified_only: Only include human-verified records
        
        Returns:
            List of training samples
        """
        samples = []
        
        for record in self.records:
            if verified_only and not record.human_verified:
                continue
            
            # Use corrected labels if available
            labels = record.corrected_labels or record.actual_classes
            
            samples.append({
                "code": record.code_snippet,
                "labels": labels,
                "source": "misclassification_feedback",
                "original_record_id": record.record_id,
            })
        
        logger.info(f"Exported {len(samples)} samples for retraining")
        return samples


# =============================================================================
# FEEDBACK COLLECTOR
# =============================================================================

@dataclass
class FeedbackEntry:
    """Human feedback on a prediction."""
    entry_id: str
    timestamp: str
    
    # Original prediction
    code: str
    predicted_classes: List[str]
    confidence_scores: Dict[str, float]
    
    # Human feedback
    correct: bool  # Was prediction correct?
    corrected_labels: Optional[List[str]] = None
    feedback_text: Optional[str] = None
    reviewer: Optional[str] = None
    
    # Metadata
    review_time_seconds: Optional[float] = None
    difficulty_rating: Optional[int] = None  # 1-5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "code": self.code,
            "predicted_classes": self.predicted_classes,
            "confidence_scores": self.confidence_scores,
            "correct": self.correct,
            "corrected_labels": self.corrected_labels,
            "feedback_text": self.feedback_text,
            "reviewer": self.reviewer,
            "review_time_seconds": self.review_time_seconds,
            "difficulty_rating": self.difficulty_rating,
        }


class FeedbackCollector:
    """
    Collect and manage human feedback on predictions.
    
    Enables:
    - Active learning by targeting uncertain predictions
    - Quality assurance through random sampling
    - Expert review of critical cases
    """
    
    def __init__(self, storage_path: str = "feedback"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.entries: List[FeedbackEntry] = []
        self._load_entries()
    
    def _load_entries(self):
        """Load existing feedback entries."""
        entries_file = self.storage_path / "feedback.json"
        if entries_file.exists():
            with open(entries_file, 'r') as f:
                data = json.load(f)
                for item in data:
                    self.entries.append(FeedbackEntry(**item))
    
    def _save_entries(self):
        """Save feedback entries."""
        entries_file = self.storage_path / "feedback.json"
        with open(entries_file, 'w') as f:
            json.dump([e.to_dict() for e in self.entries], f, indent=2)
    
    def submit_feedback(
        self,
        code: str,
        predicted_classes: List[str],
        confidence_scores: Dict[str, float],
        correct: bool,
        corrected_labels: Optional[List[str]] = None,
        feedback_text: Optional[str] = None,
        reviewer: Optional[str] = None,
        review_time_seconds: Optional[float] = None,
        difficulty_rating: Optional[int] = None,
    ) -> FeedbackEntry:
        """
        Submit human feedback on a prediction.
        
        Args:
            code: Code that was analyzed
            predicted_classes: Model's predictions
            confidence_scores: Model's confidence scores
            correct: Whether prediction was correct
            corrected_labels: Correct labels if incorrect
            feedback_text: Additional feedback
            reviewer: Reviewer identifier
            review_time_seconds: Time spent reviewing
            difficulty_rating: Difficulty 1-5
        
        Returns:
            FeedbackEntry
        """
        entry = FeedbackEntry(
            entry_id=f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.entries)}",
            timestamp=datetime.now().isoformat(),
            code=code[:2000],
            predicted_classes=predicted_classes,
            confidence_scores=confidence_scores,
            correct=correct,
            corrected_labels=corrected_labels,
            feedback_text=feedback_text,
            reviewer=reviewer,
            review_time_seconds=review_time_seconds,
            difficulty_rating=difficulty_rating,
        )
        
        self.entries.append(entry)
        self._save_entries()
        
        logger.info(f"Collected feedback: correct={correct}, entry_id={entry.entry_id}")
        return entry
    
    def get_accuracy_stats(self) -> Dict[str, Any]:
        """Get accuracy statistics from feedback."""
        if not self.entries:
            return {"total": 0, "correct": 0, "accuracy": 0.0}
        
        correct = sum(1 for e in self.entries if e.correct)
        
        return {
            "total": len(self.entries),
            "correct": correct,
            "incorrect": len(self.entries) - correct,
            "accuracy": correct / len(self.entries),
            "by_reviewer": self._stats_by_reviewer(),
        }
    
    def _stats_by_reviewer(self) -> Dict[str, Any]:
        """Get stats per reviewer."""
        by_reviewer = {}
        
        for entry in self.entries:
            reviewer = entry.reviewer or "unknown"
            if reviewer not in by_reviewer:
                by_reviewer[reviewer] = {"total": 0, "correct": 0}
            
            by_reviewer[reviewer]["total"] += 1
            if entry.correct:
                by_reviewer[reviewer]["correct"] += 1
        
        for reviewer, stats in by_reviewer.items():
            stats["accuracy"] = stats["correct"] / stats["total"]
        
        return by_reviewer
    
    def export_corrections(self) -> List[Dict[str, Any]]:
        """Export corrections for retraining."""
        corrections = []
        
        for entry in self.entries:
            if not entry.correct and entry.corrected_labels:
                corrections.append({
                    "code": entry.code,
                    "labels": entry.corrected_labels,
                    "source": "human_feedback",
                    "entry_id": entry.entry_id,
                })
        
        return corrections


# =============================================================================
# RETRAINING TRIGGER
# =============================================================================

@dataclass
class RetrainingTriggerConfig:
    """Configuration for retraining triggers."""
    # Threshold-based triggers
    min_feedback_count: int = 100          # Min feedback before retraining
    max_error_rate: float = 0.15           # Trigger if error rate exceeds
    min_critical_recall: float = 0.95      # Trigger if critical recall drops
    
    # Time-based triggers
    max_days_since_retrain: int = 30       # Force retrain after N days
    
    # Volume-based triggers
    min_new_samples: int = 500             # Min new samples for retrain
    
    # Drift detection
    drift_threshold: float = 0.1           # Feature drift threshold


class RetrainingTrigger:
    """
    Determine when model retraining is needed.
    
    Monitors:
    - Error rate from feedback
    - Critical vulnerability recall
    - Time since last training
    - Data drift
    """
    
    def __init__(
        self,
        config: Optional[RetrainingTriggerConfig] = None,
        last_retrain_date: Optional[str] = None,
    ):
        self.config = config or RetrainingTriggerConfig()
        self.last_retrain_date = (
            datetime.fromisoformat(last_retrain_date)
            if last_retrain_date
            else datetime.now()
        )
    
    def should_retrain(
        self,
        feedback_collector: FeedbackCollector,
        misclass_logger: MisclassificationLogger,
        critical_recall: Optional[float] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Check if retraining is needed.
        
        Args:
            feedback_collector: FeedbackCollector instance
            misclass_logger: MisclassificationLogger instance
            critical_recall: Current critical vulnerability recall
        
        Returns:
            (should_retrain, list of reasons)
        """
        reasons = []
        
        # 1. Check error rate from feedback
        stats = feedback_collector.get_accuracy_stats()
        if stats["total"] >= self.config.min_feedback_count:
            error_rate = 1 - stats["accuracy"]
            if error_rate > self.config.max_error_rate:
                reasons.append(
                    f"Error rate {error_rate:.2%} exceeds {self.config.max_error_rate:.2%}"
                )
        
        # 2. Check critical recall
        if critical_recall is not None:
            if critical_recall < self.config.min_critical_recall:
                reasons.append(
                    f"Critical recall {critical_recall:.2%} below "
                    f"{self.config.min_critical_recall:.2%}"
                )
        
        # 3. Check time since last retrain
        days_since = (datetime.now() - self.last_retrain_date).days
        if days_since > self.config.max_days_since_retrain:
            reasons.append(
                f"{days_since} days since last retrain "
                f"(max: {self.config.max_days_since_retrain})"
            )
        
        # 4. Check new samples available
        total_new = len(feedback_collector.export_corrections())
        total_new += len(misclass_logger.export_for_retraining())
        
        if total_new >= self.config.min_new_samples:
            reasons.append(
                f"{total_new} new samples available "
                f"(threshold: {self.config.min_new_samples})"
            )
        
        should_retrain = len(reasons) > 0
        
        if should_retrain:
            logger.warning(f"Retraining triggered: {reasons}")
        
        return should_retrain, reasons
    
    def record_retrain(self):
        """Record that retraining occurred."""
        self.last_retrain_date = datetime.now()


# =============================================================================
# CONTINUOUS LEARNING PIPELINE
# =============================================================================

class ContinuousLearningPipeline:
    """
    Orchestrate the continuous learning cycle.
    
    Workflow:
    1. Collect predictions and feedback
    2. Log misclassifications
    3. Monitor for retraining triggers
    4. Prepare retraining dataset
    5. Retrain and evaluate
    6. Deploy if improved
    """
    
    def __init__(
        self,
        misclass_logger: MisclassificationLogger,
        feedback_collector: FeedbackCollector,
        retrain_trigger: RetrainingTrigger,
        model_trainer: Any = None,  # TrainingLoop from training_loop.py
        model_evaluator: Any = None,  # ModelEvaluator from evaluation.py
    ):
        self.misclass_logger = misclass_logger
        self.feedback_collector = feedback_collector
        self.retrain_trigger = retrain_trigger
        self.model_trainer = model_trainer
        self.model_evaluator = model_evaluator
        
        self.cycle_history: List[Dict] = []
    
    def process_prediction(
        self,
        code: str,
        predicted_classes: List[str],
        confidence_scores: Dict[str, float],
        actual_classes: Optional[List[str]] = None,
        source_file: Optional[str] = None,
    ):
        """
        Process a prediction for continuous learning.
        
        Args:
            code: Analyzed code
            predicted_classes: Model predictions
            confidence_scores: Confidence scores
            actual_classes: Ground truth if known
            source_file: Source file path
        """
        # If we have ground truth, check for misclassification
        if actual_classes is not None:
            predicted_set = set(predicted_classes)
            actual_set = set(actual_classes)
            
            if predicted_set != actual_set:
                self.misclass_logger.log_misclassification(
                    code=code,
                    predicted_classes=predicted_classes,
                    actual_classes=actual_classes,
                    confidence_scores=confidence_scores,
                    source_file=source_file,
                )
    
    def check_retrain_needed(
        self,
        critical_recall: Optional[float] = None,
    ) -> Tuple[bool, List[str]]:
        """Check if retraining is needed."""
        return self.retrain_trigger.should_retrain(
            self.feedback_collector,
            self.misclass_logger,
            critical_recall,
        )
    
    def prepare_retraining_data(
        self,
        base_dataset: List[Dict],
    ) -> List[Dict]:
        """
        Prepare dataset for retraining.
        
        Args:
            base_dataset: Original training dataset
        
        Returns:
            Combined dataset with new samples
        """
        # Get corrections from feedback
        feedback_samples = self.feedback_collector.export_corrections()
        
        # Get verified misclassifications
        misclass_samples = self.misclass_logger.export_for_retraining(
            verified_only=True
        )
        
        # Combine
        combined = base_dataset.copy()
        combined.extend(feedback_samples)
        combined.extend(misclass_samples)
        
        logger.info(
            f"Prepared retraining data: {len(base_dataset)} base + "
            f"{len(feedback_samples)} feedback + "
            f"{len(misclass_samples)} misclass = {len(combined)} total"
        )
        
        return combined
    
    def run_retraining_cycle(
        self,
        base_dataset: List[Dict],
        current_model: Any,
        test_dataset: List[Dict],
    ) -> Dict[str, Any]:
        """
        Run a complete retraining cycle.
        
        Args:
            base_dataset: Original training data
            current_model: Current production model
            test_dataset: Held-out test data
        
        Returns:
            Cycle results
        """
        cycle_result = {
            "cycle_id": f"cycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "started": datetime.now().isoformat(),
            "success": False,
            "deployed": False,
        }
        
        try:
            # 1. Prepare data
            training_data = self.prepare_retraining_data(base_dataset)
            cycle_result["training_samples"] = len(training_data)
            
            # 2. Retrain (if trainer available)
            if self.model_trainer:
                new_model = self._retrain_model(training_data)
                cycle_result["retrained"] = True
            else:
                logger.warning("No model trainer configured")
                cycle_result["retrained"] = False
                return cycle_result
            
            # 3. Evaluate (if evaluator available)
            if self.model_evaluator:
                old_report = self._evaluate_model(current_model, test_dataset)
                new_report = self._evaluate_model(new_model, test_dataset)
                
                cycle_result["old_model_metrics"] = old_report.overall_metrics.to_dict()
                cycle_result["new_model_metrics"] = new_report.overall_metrics.to_dict()
                
                # 4. Check if new model is better
                improved = self._check_improvement(old_report, new_report)
                cycle_result["improved"] = improved
                
                if improved:
                    passes, failures = new_report.passes_security_requirements()
                    cycle_result["passes_requirements"] = passes
                    cycle_result["requirement_failures"] = failures
                    
                    if passes:
                        cycle_result["deployed"] = True
                        logger.info("New model deployed!")
                    else:
                        logger.warning(f"New model doesn't meet requirements: {failures}")
            
            cycle_result["success"] = True
            
        except Exception as e:
            cycle_result["error"] = str(e)
            logger.error(f"Retraining cycle failed: {e}")
        
        cycle_result["completed"] = datetime.now().isoformat()
        self.cycle_history.append(cycle_result)
        
        # Record retrain if successful
        if cycle_result["success"]:
            self.retrain_trigger.record_retrain()
        
        return cycle_result
    
    def _retrain_model(self, training_data: List[Dict]) -> Any:
        """Retrain model with new data."""
        # This would integrate with TrainingLoop
        # Placeholder for actual implementation
        logger.info(f"Retraining model with {len(training_data)} samples")
        return None
    
    def _evaluate_model(self, model: Any, test_data: List[Dict]) -> Any:
        """Evaluate model on test data."""
        # This would integrate with ModelEvaluator
        # Placeholder for actual implementation
        logger.info(f"Evaluating model on {len(test_data)} samples")
        return None
    
    def _check_improvement(self, old_report, new_report) -> bool:
        """Check if new model improves over old."""
        # Key criteria:
        # 1. Recall should not decrease
        # 2. F1 should improve or stay same
        # 3. FPR should not increase significantly
        
        old_m = old_report.overall_metrics
        new_m = new_report.overall_metrics
        
        recall_ok = new_m.recall >= old_m.recall - 0.01  # Allow 1% drop
        f1_ok = new_m.f1_score >= old_m.f1_score
        fpr_ok = new_m.false_positive_rate <= old_m.false_positive_rate + 0.02
        
        return recall_ok and f1_ok and fpr_ok
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status."""
        return {
            "misclassifications": {
                "total": len(self.misclass_logger.records),
                "unverified": len(self.misclass_logger.get_unverified()),
            },
            "feedback": self.feedback_collector.get_accuracy_stats(),
            "last_retrain": self.retrain_trigger.last_retrain_date.isoformat(),
            "cycles_run": len(self.cycle_history),
            "last_cycle": self.cycle_history[-1] if self.cycle_history else None,
        }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize components
    misclass_logger = MisclassificationLogger("./data/misclassifications")
    feedback_collector = FeedbackCollector("./data/feedback")
    retrain_trigger = RetrainingTrigger()
    
    # Create pipeline
    pipeline = ContinuousLearningPipeline(
        misclass_logger=misclass_logger,
        feedback_collector=feedback_collector,
        retrain_trigger=retrain_trigger,
    )
    
    # Example: Log a misclassification
    misclass_logger.log_misclassification(
        code='query = f"SELECT * FROM users WHERE id = {user_id}"',
        predicted_classes=[],  # Model missed it
        actual_classes=["sql_injection"],
        confidence_scores={"sql_injection": 0.3},
        source_file="app/models/user.py",
        line_number=42,
    )
    
    # Example: Submit feedback
    feedback_collector.submit_feedback(
        code='password = os.environ.get("PASSWORD")',
        predicted_classes=["hardcoded_credentials"],
        confidence_scores={"hardcoded_credentials": 0.6},
        correct=False,
        corrected_labels=[],  # It's clean
        reviewer="security_expert_1",
    )
    
    # Check if retraining needed
    should_retrain, reasons = pipeline.check_retrain_needed()
    print(f"Should retrain: {should_retrain}")
    print(f"Reasons: {reasons}")
    
    # Get pipeline status
    status = pipeline.get_status()
    print(f"Pipeline status: {json.dumps(status, indent=2)}")
