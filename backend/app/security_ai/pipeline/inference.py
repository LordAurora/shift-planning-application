"""
Security Inference Pipeline

Production-ready inference pipeline for security analysis.
Supports:
- Single file analysis
- Batch project analysis
- API scanning
- Async processing
- Result caching
"""

import logging
import time
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json

from ..config import SecurityAIConfig, get_config, SeverityLevel
from ..models.vulnerability_detector import VulnerabilityDetector, DetectionResult
from ..models.severity_classifier import SeverityClassifier
from ..services.code_analyzer import CodeAnalyzer, ProjectAnalysisResult
from ..services.api_scanner import APISecurityScanner, APIScanResult
from ..services.mitigation_engine import MitigationEngine, MitigationPlan

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Complete security analysis result."""
    analysis_id: str
    timestamp: str
    duration_seconds: float
    project_path: Optional[str] = None
    code_analysis: Optional[ProjectAnalysisResult] = None
    api_scan: Optional[APIScanResult] = None
    mitigation_plans: List[MitigationPlan] = field(default_factory=list)
    overall_score: float = 100.0
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "timestamp": self.timestamp,
            "duration_seconds": self.duration_seconds,
            "project_path": self.project_path,
            "code_analysis": self.code_analysis.to_dict() if self.code_analysis else None,
            "api_scan": self.api_scan.to_dict() if self.api_scan else None,
            "mitigation_plans": [p.to_dict() for p in self.mitigation_plans],
            "overall_score": self.overall_score,
            "summary": self.summary
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


class SecurityInferencePipeline:
    """
    Complete security analysis pipeline.
    
    Orchestrates:
    1. Code analysis (ML + rule-based)
    2. API security scanning
    3. Severity classification
    4. Mitigation generation
    
    Example:
        pipeline = SecurityInferencePipeline()
        
        # Full project analysis
        result = pipeline.analyze_project("./backend")
        print(f"Security Score: {result.overall_score}/100")
        
        # Quick single file scan
        result = pipeline.analyze_file("auth.py")
        
        # Get remediation guidance
        for plan in result.mitigation_plans:
            print(f"Fix {plan.vulnerability_category}: {plan.summary}")
    """
    
    def __init__(self, config: Optional[SecurityAIConfig] = None):
        """Initialize inference pipeline."""
        self.config = config or get_config()
        
        # Initialize components
        self.code_analyzer = CodeAnalyzer(config)
        self.api_scanner = APISecurityScanner(config)
        self.mitigation_engine = MitigationEngine(config)
        
        logger.info(f"SecurityInferencePipeline initialized in {self.config.environment.value} mode")
    
    def analyze_project(
        self,
        project_path: str,
        include_api_scan: bool = True,
        generate_mitigations: bool = True,
        max_workers: int = 4
    ) -> PipelineResult:
        """
        Perform complete security analysis on a project.
        
        Args:
            project_path: Path to project root
            include_api_scan: Whether to scan for API security issues
            generate_mitigations: Whether to generate mitigation plans
            max_workers: Parallel workers for file analysis
        
        Returns:
            PipelineResult with complete analysis
        """
        import uuid
        from datetime import datetime
        
        start_time = time.time()
        analysis_id = str(uuid.uuid4())[:8]
        
        logger.info(f"Starting project analysis: {project_path} (ID: {analysis_id})")
        
        # Code analysis
        code_result = self.code_analyzer.analyze_project(
            project_path,
            max_workers=max_workers
        )
        
        # API scanning
        api_result = None
        if include_api_scan:
            try:
                api_result = self.api_scanner.scan_fastapi_app(project_path)
            except Exception as e:
                logger.warning(f"API scan failed: {e}")
        
        # Collect all findings for mitigation
        all_findings = []
        if code_result:
            for file_result in code_result.file_results:
                for finding in file_result.findings:
                    all_findings.append({
                        "category": finding.category.value,
                        "severity": finding.severity.value,
                        "context": {"file": file_result.file_path}
                    })
        
        # Generate mitigation plans
        mitigation_plans = []
        if generate_mitigations and all_findings:
            # Deduplicate by category
            seen_categories = set()
            unique_findings = []
            for f in all_findings:
                if f["category"] not in seen_categories:
                    seen_categories.add(f["category"])
                    unique_findings.append(f)
            
            mitigation_plans = self.mitigation_engine.generate_batch_plans(unique_findings)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(code_result, api_result)
        
        # Generate summary
        summary = self._generate_summary(code_result, api_result, mitigation_plans)
        
        duration = time.time() - start_time
        
        return PipelineResult(
            analysis_id=analysis_id,
            timestamp=datetime.utcnow().isoformat(),
            duration_seconds=round(duration, 2),
            project_path=project_path,
            code_analysis=code_result,
            api_scan=api_result,
            mitigation_plans=mitigation_plans,
            overall_score=overall_score,
            summary=summary
        )
    
    def analyze_file(
        self,
        file_path: str,
        generate_mitigations: bool = True
    ) -> PipelineResult:
        """
        Analyze a single file for security issues.
        
        Args:
            file_path: Path to file to analyze
            generate_mitigations: Whether to generate mitigation plans
        
        Returns:
            PipelineResult with analysis
        """
        import uuid
        from datetime import datetime
        
        start_time = time.time()
        analysis_id = str(uuid.uuid4())[:8]
        
        # Analyze file
        file_result = self.code_analyzer.analyze_file(file_path)
        
        # Create project result wrapper
        code_result = ProjectAnalysisResult(
            project_path=file_path,
            files_analyzed=1,
            total_lines=file_result.metrics.get("lines", 0),
            file_results=[file_result],
            security_score=100.0 - (len(file_result.findings) * 5)
        )
        
        # Generate mitigations
        mitigation_plans = []
        if generate_mitigations and file_result.findings:
            findings = [
                {"category": f.category.value, "severity": f.severity.value}
                for f in file_result.findings
            ]
            # Deduplicate
            unique = {f["category"]: f for f in findings}.values()
            mitigation_plans = self.mitigation_engine.generate_batch_plans(list(unique))
        
        duration = time.time() - start_time
        
        return PipelineResult(
            analysis_id=analysis_id,
            timestamp=datetime.utcnow().isoformat(),
            duration_seconds=round(duration, 2),
            project_path=file_path,
            code_analysis=code_result,
            mitigation_plans=mitigation_plans,
            overall_score=code_result.security_score,
            summary=self._generate_summary(code_result, None, mitigation_plans)
        )
    
    def analyze_code_snippet(
        self,
        code: str,
        language: str = "python",
        generate_mitigations: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a code snippet for security issues.
        
        Args:
            code: Source code string
            language: Programming language
            generate_mitigations: Whether to generate fixes
        
        Returns:
            Dictionary with findings and mitigations
        """
        from ..models.vulnerability_detector import VulnerabilityDetector
        
        detector = VulnerabilityDetector(self.config)
        detector.model = detector.build_model()
        detector._is_loaded = True
        
        result = detector.analyze(code, language, file_path="<snippet>")
        
        mitigations = []
        if generate_mitigations:
            for finding in result.findings:
                plan = self.mitigation_engine.generate_plan(
                    finding.category,
                    finding.severity,
                    {"language": language}
                )
                mitigations.append(plan.to_dict())
        
        return {
            "findings": [f.to_dict() for f in result.findings],
            "mitigations": mitigations,
            "summary": {
                "total": len(result.findings),
                "critical": result.critical_count,
                "high": result.high_count
            }
        }
    
    def _calculate_overall_score(
        self,
        code_result: Optional[ProjectAnalysisResult],
        api_result: Optional[APIScanResult]
    ) -> float:
        """Calculate overall security score."""
        scores = []
        
        if code_result:
            scores.append(code_result.security_score)
        
        if api_result:
            scores.append(api_result.security_score)
        
        if not scores:
            return 100.0
        
        return round(sum(scores) / len(scores), 1)
    
    def _generate_summary(
        self,
        code_result: Optional[ProjectAnalysisResult],
        api_result: Optional[APIScanResult],
        mitigation_plans: List[MitigationPlan]
    ) -> Dict[str, Any]:
        """Generate analysis summary."""
        summary = {
            "total_findings": 0,
            "by_severity": {level.value: 0 for level in SeverityLevel},
            "high_priority_fixes": [],
            "requires_immediate_attention": False
        }
        
        # Aggregate findings
        if code_result:
            summary["total_findings"] += code_result.summary.get("total_findings", 0)
            for severity, count in code_result.summary.get("by_severity", {}).items():
                summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + count
        
        if api_result:
            for finding in api_result.findings:
                summary["total_findings"] += 1
                summary["by_severity"][finding.severity.value] += 1
        
        # Check for critical issues
        critical_count = summary["by_severity"].get("critical", 0)
        high_count = summary["by_severity"].get("high", 0)
        
        if critical_count > 0:
            summary["requires_immediate_attention"] = True
        
        # Add high priority fixes
        for plan in mitigation_plans[:3]:  # Top 3
            summary["high_priority_fixes"].append({
                "category": plan.vulnerability_category.value,
                "summary": plan.summary,
                "effort": plan.estimated_effort
            })
        
        return summary
    
    def save_report(
        self,
        result: PipelineResult,
        output_path: str,
        format: str = "json"
    ) -> str:
        """
        Save analysis report to file.
        
        Args:
            result: Pipeline result to save
            output_path: Output file path
            format: Output format (json, html)
        
        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(output_path, 'w') as f:
                f.write(result.to_json(indent=2))
        elif format == "html":
            html_content = self._generate_html_report(result)
            with open(output_path, 'w') as f:
                f.write(html_content)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Report saved to {output_path}")
        return str(output_path)
    
    def _generate_html_report(self, result: PipelineResult) -> str:
        """Generate HTML report from analysis result."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Security Analysis Report - {result.analysis_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .score {{ font-size: 48px; font-weight: bold; color: {'#dc3545' if result.overall_score < 50 else '#28a745' if result.overall_score >= 80 else '#ffc107'}; }}
        .severity-critical {{ color: #dc3545; }}
        .severity-high {{ color: #fd7e14; }}
        .severity-medium {{ color: #ffc107; }}
        .severity-low {{ color: #28a745; }}
        .finding {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #007bff; }}
        .mitigation {{ background: #e7f3ff; padding: 15px; margin: 10px 0; border-radius: 4px; }}
        pre {{ background: #272822; color: #f8f8f2; padding: 15px; border-radius: 4px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Security Analysis Report</h1>
        <p><strong>Analysis ID:</strong> {result.analysis_id}</p>
        <p><strong>Timestamp:</strong> {result.timestamp}</p>
        <p><strong>Duration:</strong> {result.duration_seconds}s</p>
        
        <h2>Overall Security Score</h2>
        <div class="score">{result.overall_score}/100</div>
        
        <h2>Summary</h2>
        <ul>
            <li>Total Findings: {result.summary.get('total_findings', 0)}</li>
            <li>Critical: <span class="severity-critical">{result.summary.get('by_severity', {}).get('critical', 0)}</span></li>
            <li>High: <span class="severity-high">{result.summary.get('by_severity', {}).get('high', 0)}</span></li>
            <li>Medium: <span class="severity-medium">{result.summary.get('by_severity', {}).get('medium', 0)}</span></li>
            <li>Low: <span class="severity-low">{result.summary.get('by_severity', {}).get('low', 0)}</span></li>
        </ul>
        
        {'<div class="finding" style="border-color: #dc3545;"><strong>⚠️ REQUIRES IMMEDIATE ATTENTION</strong></div>' if result.summary.get('requires_immediate_attention') else ''}
        
        <h2>Recommended Actions</h2>
        {''.join(f'<div class="mitigation"><strong>{i+1}. {fix["category"]}</strong><br>{fix["summary"]}<br><em>Effort: {fix["effort"]}</em></div>' for i, fix in enumerate(result.summary.get('high_priority_fixes', [])))}
        
        <hr>
        <p><em>Generated by Security AI Analysis System</em></p>
    </div>
</body>
</html>
"""
