"""
Model Evaluation Module

Comprehensive evaluation for security vulnerability detection:
- Standard ML metrics
- Security-specific benchmarks
- Regression testing
- Report generation
"""

import numpy as np
import logging
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from .metrics import (
    SecurityMetrics,
    MetricsCalculator,
    ClasswiseMetrics,
    ConfusionMatrixAnalyzer,
)

logger = logging.getLogger(__name__)


# =============================================================================
# EVALUATION REPORT
# =============================================================================

@dataclass
class EvaluationReport:
    """
    Complete evaluation report for a model.
    """
    # Model info
    model_name: str
    model_version: str
    evaluation_date: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Overall metrics
    overall_metrics: Optional[SecurityMetrics] = None
    
    # Per-class metrics
    classwise_metrics: List[ClasswiseMetrics] = field(default_factory=list)
    
    # Critical vulnerability performance
    critical_class_metrics: List[ClasswiseMetrics] = field(default_factory=list)
    
    # Threshold analysis
    optimal_threshold: float = 0.5
    threshold_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Error analysis
    confusion_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Security-specific checks
    security_checks: Dict[str, bool] = field(default_factory=dict)
    
    # Dataset info
    dataset_info: Dict[str, Any] = field(default_factory=dict)
    
    def passes_security_requirements(
        self,
        min_recall: float = 0.95,
        max_fpr: float = 0.10,
        min_critical_recall: float = 0.99,
    ) -> Tuple[bool, List[str]]:
        """
        Check if model meets security requirements.
        
        Args:
            min_recall: Minimum overall recall
            max_fpr: Maximum false positive rate
            min_critical_recall: Minimum recall for critical vulnerabilities
        
        Returns:
            (passes, list of failures)
        """
        failures = []
        
        # Overall metrics check
        if self.overall_metrics:
            if self.overall_metrics.recall < min_recall:
                failures.append(
                    f"Overall recall {self.overall_metrics.recall:.2%} < {min_recall:.2%}"
                )
            if self.overall_metrics.false_positive_rate > max_fpr:
                failures.append(
                    f"FPR {self.overall_metrics.false_positive_rate:.2%} > {max_fpr:.2%}"
                )
        
        # Critical class check
        for cm in self.critical_class_metrics:
            if cm.metrics.recall < min_critical_recall:
                failures.append(
                    f"Critical class '{cm.class_name}' recall "
                    f"{cm.metrics.recall:.2%} < {min_critical_recall:.2%}"
                )
        
        return len(failures) == 0, failures
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "evaluation_date": self.evaluation_date,
            "overall_metrics": self.overall_metrics.to_dict() if self.overall_metrics else None,
            "classwise_metrics": [cm.to_dict() for cm in self.classwise_metrics],
            "critical_class_metrics": [cm.to_dict() for cm in self.critical_class_metrics],
            "optimal_threshold": self.optimal_threshold,
            "threshold_analysis": self.threshold_analysis,
            "confusion_analysis": self.confusion_analysis,
            "security_checks": self.security_checks,
            "dataset_info": self.dataset_info,
        }
    
    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            f"# Evaluation Report: {self.model_name}",
            f"**Version:** {self.model_version}",
            f"**Date:** {self.evaluation_date}",
            "",
            "## Overall Metrics",
        ]
        
        if self.overall_metrics:
            lines.extend([
                f"| Metric | Value |",
                f"|--------|-------|",
                f"| Precision | {self.overall_metrics.precision:.4f} |",
                f"| Recall | {self.overall_metrics.recall:.4f} |",
                f"| F1 Score | {self.overall_metrics.f1_score:.4f} |",
                f"| False Positive Rate | {self.overall_metrics.false_positive_rate:.4f} |",
                f"| Matthews Correlation | {self.overall_metrics.matthews_correlation:.4f} |",
                "",
            ])
        
        # Security checks
        lines.extend([
            "## Security Requirements",
            "",
        ])
        
        passes, failures = self.passes_security_requirements()
        if passes:
            lines.append("✅ **All security requirements PASSED**")
        else:
            lines.append("❌ **Security requirements FAILED:**")
            for f in failures:
                lines.append(f"  - {f}")
        
        lines.append("")
        
        # Critical vulnerabilities
        lines.extend([
            "## Critical Vulnerability Detection",
            "",
            "| Class | Recall | Precision | F1 | Support |",
            "|-------|--------|-----------|-------|---------|",
        ])
        
        for cm in self.critical_class_metrics:
            lines.append(
                f"| {cm.class_name} | {cm.metrics.recall:.4f} | "
                f"{cm.metrics.precision:.4f} | {cm.metrics.f1_score:.4f} | "
                f"{cm.support} |"
            )
        
        return "\n".join(lines)


# =============================================================================
# MODEL EVALUATOR
# =============================================================================

class ModelEvaluator:
    """
    Evaluate models for security vulnerability detection.
    
    Features:
    - Comprehensive metrics calculation
    - Threshold optimization
    - Error analysis
    - Report generation
    """
    
    CRITICAL_CLASSES = [
        "sql_injection",
        "command_injection",
        "path_traversal",
        "code_injection",
        "insecure_deserialization",
        "hardcoded_credentials",
        "buffer_overflow",
    ]
    
    def __init__(self, num_classes: int = 15):
        self.num_classes = num_classes
        self.metrics_calculator = MetricsCalculator(num_classes)
    
    def evaluate(
        self,
        model,
        X_test: np.ndarray,
        y_test: np.ndarray,
        model_name: str = "security_model",
        model_version: str = "1.0.0",
    ) -> EvaluationReport:
        """
        Complete model evaluation.
        
        Args:
            model: Trained model
            X_test: Test features
            y_test: Test labels
            model_name: Name for report
            model_version: Version for report
        
        Returns:
            EvaluationReport
        """
        logger.info(f"Evaluating model: {model_name} v{model_version}")
        
        # Get predictions
        y_prob = model.predict(X_test)
        y_pred = (y_prob >= 0.5).astype(int)
        
        # Overall metrics
        overall_metrics = self.metrics_calculator.calculate(
            y_test, y_pred, y_prob, threshold=0.5
        )
        
        # Classwise metrics
        classwise_metrics = self.metrics_calculator.calculate_classwise(
            y_test, y_pred, threshold=0.5
        )
        
        # Critical class metrics
        critical_class_metrics = [
            cm for cm in classwise_metrics 
            if cm.class_name in self.CRITICAL_CLASSES
        ]
        
        # Threshold optimization
        optimal_threshold, optimal_metrics = self.metrics_calculator.find_optimal_threshold(
            y_test, y_prob, metric="f1", min_recall=0.95
        )
        
        # Threshold analysis at different points
        threshold_analysis = self._analyze_thresholds(y_test, y_prob)
        
        # Confusion analysis
        class_names = [cm.class_name for cm in classwise_metrics]
        analyzer = ConfusionMatrixAnalyzer(class_names)
        confusion_matrix = analyzer.build_matrix(y_test, y_pred)
        confusion_analysis = analyzer.analyze_errors(confusion_matrix)
        
        # Security checks
        security_checks = self._run_security_checks(
            overall_metrics, critical_class_metrics
        )
        
        return EvaluationReport(
            model_name=model_name,
            model_version=model_version,
            overall_metrics=overall_metrics,
            classwise_metrics=classwise_metrics,
            critical_class_metrics=critical_class_metrics,
            optimal_threshold=optimal_threshold,
            threshold_analysis=threshold_analysis,
            confusion_analysis=confusion_analysis,
            security_checks=security_checks,
            dataset_info={
                "test_samples": len(X_test),
                "positive_samples": int(y_test.sum()),
                "class_distribution": {
                    i: int(y_test[:, i].sum()) 
                    for i in range(y_test.shape[1])
                },
            },
        )
    
    def _analyze_thresholds(
        self,
        y_true: np.ndarray,
        y_prob: np.ndarray,
    ) -> Dict[str, Any]:
        """Analyze metrics at different thresholds."""
        thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        analysis = {}
        
        for thresh in thresholds:
            y_pred = (y_prob >= thresh).astype(int)
            metrics = self.metrics_calculator.calculate(
                y_true, y_pred, threshold=thresh
            )
            
            analysis[f"threshold_{thresh}"] = {
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1": metrics.f1_score,
                "fpr": metrics.false_positive_rate,
            }
        
        return analysis
    
    def _run_security_checks(
        self,
        overall: SecurityMetrics,
        critical: List[ClasswiseMetrics],
    ) -> Dict[str, bool]:
        """Run security-specific checks."""
        checks = {
            "overall_recall_95": overall.recall >= 0.95,
            "overall_fpr_below_10": overall.false_positive_rate <= 0.10,
            "critical_recall_99": all(
                cm.metrics.recall >= 0.99 for cm in critical
            ),
            "no_critical_missed": overall.false_negatives == 0,  # Ideal
            "balanced_accuracy_above_90": overall.balanced_accuracy >= 0.90,
        }
        
        return checks


# =============================================================================
# SECURITY BENCHMARK
# =============================================================================

class SecurityBenchmark:
    """
    Benchmark suite for security models.
    
    Tests model against known vulnerability patterns
    to ensure critical detections work.
    """
    
    # Benchmark cases (code, expected_classes)
    BENCHMARK_CASES = [
        # SQL Injection
        {
            "name": "sql_injection_fstring",
            "code": 'query = f"SELECT * FROM users WHERE id = {user_id}"',
            "expected": ["sql_injection"],
            "critical": True,
        },
        {
            "name": "sql_injection_format",
            "code": 'query = "SELECT * FROM users WHERE id = {}".format(user_id)',
            "expected": ["sql_injection"],
            "critical": True,
        },
        # Command Injection
        {
            "name": "command_injection_system",
            "code": 'os.system(f"ls {user_dir}")',
            "expected": ["command_injection"],
            "critical": True,
        },
        # Hardcoded Credentials
        {
            "name": "hardcoded_password",
            "code": 'password = "admin123"',
            "expected": ["hardcoded_credentials"],
            "critical": True,
        },
        # Path Traversal
        {
            "name": "path_traversal",
            "code": 'open(f"/data/{filename}")',
            "expected": ["path_traversal"],
            "critical": True,
        },
        # Clean code (should not trigger)
        {
            "name": "clean_parameterized",
            "code": 'cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))',
            "expected": [],
            "critical": False,
        },
        {
            "name": "clean_env_var",
            "code": 'password = os.environ.get("DB_PASSWORD")',
            "expected": [],
            "critical": False,
        },
    ]
    
    def __init__(self, model, preprocessor):
        self.model = model
        self.preprocessor = preprocessor
    
    def run_benchmark(self) -> Dict[str, Any]:
        """
        Run benchmark suite.
        
        Returns:
            Benchmark results with pass/fail for each case
        """
        results = {
            "total_cases": len(self.BENCHMARK_CASES),
            "passed": 0,
            "failed": 0,
            "critical_passed": 0,
            "critical_failed": 0,
            "cases": [],
        }
        
        for case in self.BENCHMARK_CASES:
            case_result = self._run_case(case)
            results["cases"].append(case_result)
            
            if case_result["passed"]:
                results["passed"] += 1
                if case["critical"]:
                    results["critical_passed"] += 1
            else:
                results["failed"] += 1
                if case["critical"]:
                    results["critical_failed"] += 1
        
        results["pass_rate"] = results["passed"] / results["total_cases"]
        results["critical_pass_rate"] = (
            results["critical_passed"] / 
            sum(1 for c in self.BENCHMARK_CASES if c["critical"])
        )
        
        return results
    
    def _run_case(self, case: Dict) -> Dict[str, Any]:
        """Run a single benchmark case."""
        # Preprocess
        tokens = self.preprocessor.tokenize(case["code"])
        encoded = self.preprocessor.encode(tokens, max_length=512)
        
        # Predict
        prediction = self.model.predict(encoded.reshape(1, -1))[0]
        predicted_classes = [
            MetricsCalculator.VULNERABILITY_CLASSES[i]["name"]
            for i, p in enumerate(prediction) if p >= 0.5
        ]
        
        # Check if expected classes are detected
        expected_set = set(case["expected"])
        predicted_set = set(predicted_classes)
        
        if case["expected"]:
            # Should detect vulnerabilities
            passed = expected_set.issubset(predicted_set)
        else:
            # Should be clean
            passed = len(predicted_set) == 0
        
        return {
            "name": case["name"],
            "code": case["code"][:100],
            "expected": case["expected"],
            "predicted": predicted_classes,
            "passed": passed,
            "critical": case["critical"],
        }


# =============================================================================
# REGRESSION TESTER
# =============================================================================

class RegressionTester:
    """
    Regression testing for model updates.
    
    Ensures new model versions don't regress on:
    - Known vulnerability patterns
    - Previous false negative cases
    - Critical detection capabilities
    """
    
    def __init__(
        self,
        regression_cases_path: Optional[str] = None,
    ):
        self.regression_cases: List[Dict] = []
        
        if regression_cases_path:
            self.load_cases(regression_cases_path)
    
    def load_cases(self, path: str):
        """Load regression test cases from file."""
        with open(path, 'r') as f:
            self.regression_cases = json.load(f)
        logger.info(f"Loaded {len(self.regression_cases)} regression cases")
    
    def add_case(
        self,
        code: str,
        expected_classes: List[str],
        description: str,
        source: str = "manual",
    ):
        """Add a regression test case."""
        self.regression_cases.append({
            "code": code,
            "expected_classes": expected_classes,
            "description": description,
            "source": source,
            "added_date": datetime.now().isoformat(),
        })
    
    def run_regression_tests(
        self,
        new_model,
        old_model,
        preprocessor,
    ) -> Dict[str, Any]:
        """
        Run regression tests comparing new and old model.
        
        Args:
            new_model: New model version
            old_model: Previous model version
            preprocessor: Code preprocessor
        
        Returns:
            Regression test results
        """
        results = {
            "total_cases": len(self.regression_cases),
            "new_model_passed": 0,
            "old_model_passed": 0,
            "regressions": [],
            "improvements": [],
        }
        
        for case in self.regression_cases:
            # Preprocess
            tokens = preprocessor.tokenize(case["code"])
            encoded = preprocessor.encode(tokens, max_length=512)
            X = encoded.reshape(1, -1)
            
            # Predict with both models
            new_pred = new_model.predict(X)[0]
            old_pred = old_model.predict(X)[0]
            
            new_classes = self._get_predicted_classes(new_pred)
            old_classes = self._get_predicted_classes(old_pred)
            
            expected = set(case["expected_classes"])
            
            new_passed = expected.issubset(set(new_classes))
            old_passed = expected.issubset(set(old_classes))
            
            if new_passed:
                results["new_model_passed"] += 1
            if old_passed:
                results["old_model_passed"] += 1
            
            # Check for regression
            if old_passed and not new_passed:
                results["regressions"].append({
                    "case": case["description"],
                    "expected": case["expected_classes"],
                    "new_predicted": new_classes,
                    "old_predicted": old_classes,
                })
            
            # Check for improvement
            if not old_passed and new_passed:
                results["improvements"].append({
                    "case": case["description"],
                    "expected": case["expected_classes"],
                    "new_predicted": new_classes,
                })
        
        results["regression_count"] = len(results["regressions"])
        results["improvement_count"] = len(results["improvements"])
        results["passes_regression"] = len(results["regressions"]) == 0
        
        return results
    
    def _get_predicted_classes(
        self,
        prediction: np.ndarray,
        threshold: float = 0.5,
    ) -> List[str]:
        """Get class names from prediction array."""
        return [
            MetricsCalculator.VULNERABILITY_CLASSES[i]["name"]
            for i, p in enumerate(prediction) if p >= threshold
        ]
    
    def save_cases(self, path: str):
        """Save regression cases to file."""
        with open(path, 'w') as f:
            json.dump(self.regression_cases, f, indent=2)
        logger.info(f"Saved {len(self.regression_cases)} regression cases")
