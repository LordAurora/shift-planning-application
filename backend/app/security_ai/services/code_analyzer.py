"""
Code Analyzer Service

Comprehensive static code analysis service combining:
- Rule-based pattern matching
- ML-based vulnerability detection
- Abstract Syntax Tree (AST) analysis
- Control flow analysis

Supports multiple languages: Python, JavaScript, TypeScript, Java, Go
"""

import os
import ast
import logging
import re
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..config import (
    SecurityAIConfig,
    VulnerabilityCategory,
    SeverityLevel,
    get_config
)
from ..models.vulnerability_detector import (
    VulnerabilityDetector,
    VulnerabilityFinding,
    DetectionResult
)
from ..models.severity_classifier import SeverityClassifier

logger = logging.getLogger(__name__)


@dataclass
class FileAnalysisResult:
    """Result of analyzing a single file."""
    file_path: str
    language: str
    findings: List[VulnerabilityFinding]
    metrics: Dict[str, Any]
    ast_issues: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "language": self.language,
            "findings": [f.to_dict() for f in self.findings],
            "metrics": self.metrics,
            "ast_issues": self.ast_issues,
            "summary": {
                "total_findings": len(self.findings),
                "critical": sum(1 for f in self.findings if f.severity == SeverityLevel.CRITICAL),
                "high": sum(1 for f in self.findings if f.severity == SeverityLevel.HIGH),
            }
        }


@dataclass
class ProjectAnalysisResult:
    """Result of analyzing an entire project."""
    project_path: str
    files_analyzed: int
    total_lines: int
    file_results: List[FileAnalysisResult]
    security_score: float  # 0-100
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self._calculate_summary()
    
    def _calculate_summary(self):
        """Calculate project-wide summary."""
        all_findings = [f for r in self.file_results for f in r.findings]
        
        by_severity = {level: 0 for level in SeverityLevel}
        by_category = {cat: 0 for cat in VulnerabilityCategory}
        
        for finding in all_findings:
            by_severity[finding.severity] += 1
            by_category[finding.category] += 1
        
        self.summary = {
            "total_findings": len(all_findings),
            "by_severity": {k.value: v for k, v in by_severity.items()},
            "by_category": {k.value: v for k, v in by_category.items() if v > 0},
            "files_with_issues": sum(1 for r in self.file_results if r.findings),
            "critical_files": [
                r.file_path for r in self.file_results
                if any(f.severity == SeverityLevel.CRITICAL for f in r.findings)
            ]
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "files_analyzed": self.files_analyzed,
            "total_lines": self.total_lines,
            "security_score": self.security_score,
            "summary": self.summary,
            "file_results": [r.to_dict() for r in self.file_results]
        }


class CodeAnalyzer:
    """
    Comprehensive code analysis service.
    
    Combines multiple analysis techniques:
    1. ML-based vulnerability detection
    2. AST-based analysis for language-specific patterns
    3. Control flow analysis for security-critical paths
    4. Dependency analysis for vulnerable components
    
    Example:
        analyzer = CodeAnalyzer()
        
        # Analyze single file
        result = analyzer.analyze_file("app/auth.py")
        
        # Analyze entire project
        project_result = analyzer.analyze_project("./backend")
        print(f"Security Score: {project_result.security_score}/100")
    """
    
    # File extensions to language mapping
    LANGUAGE_MAPPING = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
    }
    
    # Directories to skip
    SKIP_DIRS = {
        "node_modules", "venv", ".venv", "env", ".env",
        "__pycache__", ".git", ".svn", "dist", "build",
        "target", "vendor", ".idea", ".vscode"
    }
    
    # Dangerous Python AST patterns
    DANGEROUS_PYTHON_CALLS = {
        "eval": (VulnerabilityCategory.INJECTION, SeverityLevel.CRITICAL),
        "exec": (VulnerabilityCategory.INJECTION, SeverityLevel.CRITICAL),
        "compile": (VulnerabilityCategory.INJECTION, SeverityLevel.HIGH),
        "__import__": (VulnerabilityCategory.INJECTION, SeverityLevel.HIGH),
        "getattr": (VulnerabilityCategory.BROKEN_ACCESS, SeverityLevel.MEDIUM),
        "setattr": (VulnerabilityCategory.BROKEN_ACCESS, SeverityLevel.MEDIUM),
        "pickle.loads": (VulnerabilityCategory.INSECURE_DESERIALIZATION, SeverityLevel.CRITICAL),
        "yaml.load": (VulnerabilityCategory.INSECURE_DESERIALIZATION, SeverityLevel.HIGH),
        "subprocess.call": (VulnerabilityCategory.INJECTION, SeverityLevel.HIGH),
        "os.system": (VulnerabilityCategory.INJECTION, SeverityLevel.CRITICAL),
        "os.popen": (VulnerabilityCategory.INJECTION, SeverityLevel.CRITICAL),
    }
    
    def __init__(self, config: Optional[SecurityAIConfig] = None):
        """Initialize code analyzer."""
        self.config = config or get_config()
        self.detector = VulnerabilityDetector(config)
        self.classifier = SeverityClassifier(config)
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize ML models."""
        try:
            # Build models without loading checkpoints
            self.detector.model = self.detector.build_model()
            self.detector._is_loaded = True
            logger.info("Vulnerability detector model initialized")
        except Exception as e:
            logger.warning(f"Could not initialize ML model: {e}. Using rule-based detection only.")
    
    def analyze_file(
        self,
        file_path: str,
        use_ml: bool = True
    ) -> FileAnalysisResult:
        """
        Analyze a single file for security vulnerabilities.
        
        Args:
            file_path: Path to file to analyze
            use_ml: Whether to use ML detection
        
        Returns:
            FileAnalysisResult with findings and metrics
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine language
        language = self.LANGUAGE_MAPPING.get(file_path.suffix.lower(), "unknown")
        
        if language == "unknown":
            logger.warning(f"Unknown language for file: {file_path}")
            return FileAnalysisResult(
                file_path=str(file_path),
                language=language,
                findings=[],
                metrics={"lines": 0, "complexity": 0},
                ast_issues=[]
            )
        
        # Read file
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return FileAnalysisResult(
                file_path=str(file_path),
                language=language,
                findings=[],
                metrics={"error": str(e)},
                ast_issues=[]
            )
        
        # ML-based detection
        detection_result = self.detector.analyze(
            code=code,
            language=language,
            file_path=str(file_path),
            use_ml=use_ml
        )
        
        # AST-based analysis (language specific)
        ast_issues = []
        if language == "python":
            ast_issues = self._analyze_python_ast(code, str(file_path))
        
        # Calculate metrics
        metrics = self._calculate_metrics(code, language)
        
        # Combine findings
        all_findings = detection_result.findings.copy()
        
        # Convert AST issues to findings
        for issue in ast_issues:
            finding = VulnerabilityFinding(
                category=issue["category"],
                severity=issue["severity"],
                confidence=0.9,
                line_start=issue["line"],
                line_end=issue["line"],
                code_snippet=issue["code"],
                description=issue["description"],
                mitigation=issue["mitigation"],
                cwe_id=issue.get("cwe_id")
            )
            all_findings.append(finding)
        
        return FileAnalysisResult(
            file_path=str(file_path),
            language=language,
            findings=all_findings,
            metrics=metrics,
            ast_issues=ast_issues
        )
    
    def analyze_project(
        self,
        project_path: str,
        max_workers: int = 4,
        use_ml: bool = True
    ) -> ProjectAnalysisResult:
        """
        Analyze entire project for security vulnerabilities.
        
        Args:
            project_path: Path to project root
            max_workers: Number of parallel workers
            use_ml: Whether to use ML detection
        
        Returns:
            ProjectAnalysisResult with aggregated findings
        """
        project_path = Path(project_path)
        
        if not project_path.exists():
            raise FileNotFoundError(f"Project path not found: {project_path}")
        
        # Collect files to analyze
        files_to_analyze = self._collect_files(project_path)
        logger.info(f"Found {len(files_to_analyze)} files to analyze")
        
        # Analyze files in parallel
        file_results = []
        total_lines = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self.analyze_file, f, use_ml): f
                for f in files_to_analyze
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    file_results.append(result)
                    total_lines += result.metrics.get("lines", 0)
                except Exception as e:
                    logger.error(f"Error analyzing {file_path}: {e}")
        
        # Calculate security score
        security_score = self._calculate_security_score(file_results, total_lines)
        
        return ProjectAnalysisResult(
            project_path=str(project_path),
            files_analyzed=len(file_results),
            total_lines=total_lines,
            file_results=file_results,
            security_score=security_score
        )
    
    def _collect_files(self, root: Path) -> List[str]:
        """Collect all analyzable files in project."""
        files = []
        
        for path in root.rglob("*"):
            # Skip directories
            if path.is_dir():
                continue
            
            # Skip excluded directories
            if any(skip in path.parts for skip in self.SKIP_DIRS):
                continue
            
            # Check if language is supported
            if path.suffix.lower() in self.LANGUAGE_MAPPING:
                files.append(str(path))
        
        return files
    
    def _analyze_python_ast(
        self,
        code: str,
        file_path: str
    ) -> List[Dict[str, Any]]:
        """Analyze Python code using AST."""
        issues = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return issues
        
        lines = code.split('\n')
        
        for node in ast.walk(tree):
            # Check for dangerous function calls
            if isinstance(node, ast.Call):
                func_name = self._get_func_name(node)
                
                if func_name in self.DANGEROUS_PYTHON_CALLS:
                    category, severity = self.DANGEROUS_PYTHON_CALLS[func_name]
                    line = getattr(node, 'lineno', 0)
                    
                    issues.append({
                        "category": category,
                        "severity": severity,
                        "line": line,
                        "code": lines[line - 1] if 0 < line <= len(lines) else "",
                        "description": f"Dangerous function call: {func_name}",
                        "mitigation": self._get_ast_mitigation(func_name),
                        "cwe_id": self._get_cwe_for_func(func_name)
                    })
            
            # Check for assert statements (disabled in optimized mode)
            elif isinstance(node, ast.Assert):
                line = getattr(node, 'lineno', 0)
                issues.append({
                    "category": VulnerabilityCategory.MISCONFIG,
                    "severity": SeverityLevel.LOW,
                    "line": line,
                    "code": lines[line - 1] if 0 < line <= len(lines) else "",
                    "description": "Assert statement used for security check",
                    "mitigation": "Replace assert with proper validation that works in production (-O flag)",
                    "cwe_id": "CWE-617"
                })
            
            # Check for bare except clauses
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    line = getattr(node, 'lineno', 0)
                    issues.append({
                        "category": VulnerabilityCategory.MISCONFIG,
                        "severity": SeverityLevel.LOW,
                        "line": line,
                        "code": lines[line - 1] if 0 < line <= len(lines) else "",
                        "description": "Bare except clause catches all exceptions including KeyboardInterrupt",
                        "mitigation": "Specify exception types explicitly",
                        "cwe_id": None
                    })
        
        return issues
    
    def _get_func_name(self, node: ast.Call) -> str:
        """Extract function name from Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        return ""
    
    def _get_ast_mitigation(self, func_name: str) -> str:
        """Get mitigation for dangerous function."""
        mitigations = {
            "eval": "Use ast.literal_eval() for safe evaluation of literals, or avoid dynamic code execution entirely.",
            "exec": "Avoid dynamic code execution. Use safer alternatives like function dispatch.",
            "os.system": "Use subprocess.run() with shell=False and explicit argument list.",
            "subprocess.call": "Use subprocess.run() with shell=False for better security.",
            "pickle.loads": "Use JSON or other safe serialization formats. If pickle is required, use hmac verification.",
            "yaml.load": "Use yaml.safe_load() instead of yaml.load().",
        }
        return mitigations.get(func_name, f"Review usage of {func_name} for security implications.")
    
    def _get_cwe_for_func(self, func_name: str) -> Optional[str]:
        """Get CWE ID for dangerous function."""
        cwe_mapping = {
            "eval": "CWE-94",
            "exec": "CWE-94",
            "os.system": "CWE-78",
            "subprocess.call": "CWE-78",
            "pickle.loads": "CWE-502",
            "yaml.load": "CWE-502",
        }
        return cwe_mapping.get(func_name)
    
    def _calculate_metrics(self, code: str, language: str) -> Dict[str, Any]:
        """Calculate code metrics."""
        lines = code.split('\n')
        
        return {
            "lines": len(lines),
            "non_empty_lines": sum(1 for line in lines if line.strip()),
            "comment_lines": self._count_comments(code, language),
            "complexity": self._estimate_complexity(code, language)
        }
    
    def _count_comments(self, code: str, language: str) -> int:
        """Count comment lines in code."""
        count = 0
        
        if language == "python":
            # Single line comments
            count += len(re.findall(r'^\s*#', code, re.MULTILINE))
            # Docstrings (rough estimate)
            count += code.count('"""') + code.count("'''")
        elif language in ["javascript", "typescript", "java", "go", "c", "cpp"]:
            count += len(re.findall(r'^\s*//', code, re.MULTILINE))
            count += len(re.findall(r'/\*', code))
        
        return count
    
    def _estimate_complexity(self, code: str, language: str) -> int:
        """Estimate cyclomatic complexity (simplified)."""
        complexity = 1  # Base complexity
        
        # Count decision points
        patterns = [
            r'\bif\b', r'\belif\b', r'\belse\b',
            r'\bfor\b', r'\bwhile\b',
            r'\btry\b', r'\bcatch\b', r'\bexcept\b',
            r'\bcase\b', r'\b\?\b',  # Ternary
            r'\band\b', r'\bor\b', r'&&', r'\|\|'
        ]
        
        for pattern in patterns:
            complexity += len(re.findall(pattern, code))
        
        return complexity
    
    def _calculate_security_score(
        self,
        file_results: List[FileAnalysisResult],
        total_lines: int
    ) -> float:
        """
        Calculate overall security score (0-100).
        
        Score calculation:
        - Start at 100
        - Deduct points based on findings by severity
        - Normalize by lines of code
        """
        if total_lines == 0:
            return 100.0
        
        score = 100.0
        
        severity_deductions = {
            SeverityLevel.CRITICAL: 15,
            SeverityLevel.HIGH: 8,
            SeverityLevel.MEDIUM: 3,
            SeverityLevel.LOW: 1,
            SeverityLevel.INFO: 0
        }
        
        for result in file_results:
            for finding in result.findings:
                deduction = severity_deductions.get(finding.severity, 0)
                # Scale deduction by file size relative to project
                file_lines = result.metrics.get("lines", 100)
                scale_factor = min(1.0, file_lines / 500)  # Cap at 500 lines
                score -= deduction * scale_factor
        
        return max(0.0, min(100.0, score))
