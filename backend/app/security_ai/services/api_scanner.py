"""
API Security Scanner

Analyzes API configurations and endpoints for security vulnerabilities:
- Authentication/Authorization issues
- Rate limiting gaps
- CORS misconfiguration
- Input validation weaknesses
- Sensitive data exposure
- Insecure HTTP configurations
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from ..config import (
    SecurityAIConfig,
    VulnerabilityCategory,
    SeverityLevel,
    get_config
)

logger = logging.getLogger(__name__)


class APISecurityCheck(Enum):
    """Types of API security checks."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMITING = "rate_limiting"
    CORS = "cors"
    INPUT_VALIDATION = "input_validation"
    SENSITIVE_DATA = "sensitive_data"
    HTTPS = "https"
    HEADERS = "headers"
    LOGGING = "logging"


@dataclass
class APIFinding:
    """API security finding."""
    check_type: APISecurityCheck
    severity: SeverityLevel
    endpoint: Optional[str]
    description: str
    recommendation: str
    evidence: Optional[str] = None
    cwe_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_type": self.check_type.value,
            "severity": self.severity.value,
            "endpoint": self.endpoint,
            "description": self.description,
            "recommendation": self.recommendation,
            "evidence": self.evidence,
            "cwe_id": self.cwe_id
        }


@dataclass
class APIScanResult:
    """Result of API security scan."""
    api_name: str
    endpoints_scanned: int
    findings: List[APIFinding]
    security_score: float
    compliance: Dict[str, bool] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "api_name": self.api_name,
            "endpoints_scanned": self.endpoints_scanned,
            "findings": [f.to_dict() for f in self.findings],
            "security_score": self.security_score,
            "compliance": self.compliance,
            "summary": {
                "total_findings": len(self.findings),
                "critical": sum(1 for f in self.findings if f.severity == SeverityLevel.CRITICAL),
                "high": sum(1 for f in self.findings if f.severity == SeverityLevel.HIGH)
            }
        }


class APISecurityScanner:
    """
    API Security Scanner for analyzing web API configurations.
    
    Checks for:
    - Missing or weak authentication
    - Authorization bypass vulnerabilities
    - Rate limiting configuration
    - CORS misconfigurations
    - Input validation gaps
    - Sensitive data in responses
    - Security header issues
    
    Example:
        scanner = APISecurityScanner()
        
        # Scan FastAPI application
        result = scanner.scan_fastapi_app("backend/app")
        
        # Check specific endpoints
        result = scanner.scan_openapi_spec("openapi.json")
    """
    
    # Security headers to check
    REQUIRED_HEADERS = {
        "X-Content-Type-Options": ("nosniff", SeverityLevel.MEDIUM),
        "X-Frame-Options": ("DENY", SeverityLevel.MEDIUM),
        "X-XSS-Protection": ("1; mode=block", SeverityLevel.LOW),
        "Strict-Transport-Security": ("max-age=31536000", SeverityLevel.HIGH),
        "Content-Security-Policy": (None, SeverityLevel.MEDIUM),
        "Referrer-Policy": ("strict-origin-when-cross-origin", SeverityLevel.LOW),
    }
    
    # Dangerous CORS configurations
    DANGEROUS_CORS = {
        "*": SeverityLevel.HIGH,
        "null": SeverityLevel.CRITICAL,
    }
    
    # Sensitive field patterns
    SENSITIVE_PATTERNS = [
        r"password",
        r"secret",
        r"token",
        r"api_key",
        r"apikey",
        r"private",
        r"credit_card",
        r"ssn",
        r"social_security",
    ]
    
    def __init__(self, config: Optional[SecurityAIConfig] = None):
        """Initialize API scanner."""
        self.config = config or get_config()
    
    def scan_fastapi_app(self, app_path: str) -> APIScanResult:
        """
        Scan a FastAPI application for security issues.
        
        Args:
            app_path: Path to FastAPI application directory
        
        Returns:
            APIScanResult with findings
        """
        findings = []
        endpoints_scanned = 0
        app_path = Path(app_path)
        
        # Scan router files
        router_files = list(app_path.rglob("*router*.py")) + list(app_path.rglob("*routes*.py"))
        
        for router_file in router_files:
            try:
                with open(router_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_findings = self._scan_fastapi_routes(content, str(router_file))
                findings.extend(file_findings)
                endpoints_scanned += len(re.findall(r'@router\.(get|post|put|delete|patch)', content))
                
            except Exception as e:
                logger.error(f"Error scanning {router_file}: {e}")
        
        # Scan main.py for CORS and middleware
        main_files = list(app_path.rglob("main.py"))
        for main_file in main_files:
            try:
                with open(main_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                findings.extend(self._scan_cors_config(content, str(main_file)))
                findings.extend(self._scan_middleware(content, str(main_file)))
                
            except Exception as e:
                logger.error(f"Error scanning {main_file}: {e}")
        
        # Calculate security score
        security_score = self._calculate_score(findings)
        
        # Check compliance
        compliance = self._check_compliance(findings)
        
        return APIScanResult(
            api_name=str(app_path),
            endpoints_scanned=endpoints_scanned,
            findings=findings,
            security_score=security_score,
            compliance=compliance
        )
    
    def _scan_fastapi_routes(
        self,
        content: str,
        file_path: str
    ) -> List[APIFinding]:
        """Scan FastAPI route definitions."""
        findings = []
        
        # Check for missing authentication
        public_endpoints = re.findall(
            r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\'].*?\)\s*\n(?:async )?def (\w+)',
            content,
            re.MULTILINE
        )
        
        for method, path, func_name in public_endpoints:
            # Check if endpoint has authentication
            # Look for Depends patterns near the function
            func_pattern = rf'def {func_name}\([^)]*\)'
            func_match = re.search(func_pattern, content)
            
            if func_match:
                # Check for auth dependency
                func_end = content.find(':', func_match.end())
                func_def = content[func_match.start():func_end + 100]
                
                has_auth = any(pattern in func_def for pattern in [
                    'get_current_user',
                    'require_role',
                    'Depends(auth',
                    'OAuth2',
                    'HTTPBearer',
                    'HTTPBasic',
                ])
                
                # Check if sensitive endpoint without auth
                sensitive_paths = ['/admin', '/users', '/delete', '/update', '/config']
                is_sensitive = any(sp in path for sp in sensitive_paths)
                
                if is_sensitive and not has_auth:
                    findings.append(APIFinding(
                        check_type=APISecurityCheck.AUTHENTICATION,
                        severity=SeverityLevel.CRITICAL,
                        endpoint=f"{method.upper()} {path}",
                        description=f"Sensitive endpoint '{path}' may lack authentication",
                        recommendation="Add authentication dependency using Depends(get_current_user) or similar",
                        evidence=f"Function: {func_name}",
                        cwe_id="CWE-306"
                    ))
        
        # Check for SQL injection in query parameters
        raw_queries = re.findall(
            r'db\.(query|execute)\s*\([^)]*\+[^)]*\)',
            content
        )
        for query in raw_queries:
            findings.append(APIFinding(
                check_type=APISecurityCheck.INPUT_VALIDATION,
                severity=SeverityLevel.CRITICAL,
                endpoint=None,
                description="Potential SQL injection: Query constructed with string concatenation",
                recommendation="Use parameterized queries with SQLAlchemy ORM methods",
                evidence=query,
                cwe_id="CWE-89"
            ))
        
        # Check for response model exposing sensitive fields
        for pattern in self.SENSITIVE_PATTERNS:
            matches = re.findall(
                rf'response_model\s*=.*?{pattern}',
                content,
                re.IGNORECASE
            )
            for match in matches:
                findings.append(APIFinding(
                    check_type=APISecurityCheck.SENSITIVE_DATA,
                    severity=SeverityLevel.MEDIUM,
                    endpoint=None,
                    description=f"Response model may expose sensitive field: {pattern}",
                    recommendation="Create a separate response schema that excludes sensitive fields",
                    evidence=match,
                    cwe_id="CWE-200"
                ))
        
        return findings
    
    def _scan_cors_config(
        self,
        content: str,
        file_path: str
    ) -> List[APIFinding]:
        """Scan CORS configuration."""
        findings = []
        
        # Check for permissive CORS
        cors_matches = re.findall(
            r'allow_origins\s*=\s*\[(.*?)\]',
            content,
            re.DOTALL
        )
        
        for match in cors_matches:
            if '"*"' in match or "'*'" in match:
                findings.append(APIFinding(
                    check_type=APISecurityCheck.CORS,
                    severity=SeverityLevel.HIGH,
                    endpoint=None,
                    description="CORS allows all origins (*)",
                    recommendation="Specify allowed origins explicitly. Use environment variables for flexibility.",
                    evidence="allow_origins = ['*']",
                    cwe_id="CWE-942"
                ))
        
        # Check credentials with wildcard origin
        if 'allow_credentials=True' in content and ("'*'" in content or '"*"' in content):
            findings.append(APIFinding(
                check_type=APISecurityCheck.CORS,
                severity=SeverityLevel.CRITICAL,
                endpoint=None,
                description="CORS allows credentials with wildcard origin - this is blocked by browsers but indicates misconfiguration",
                recommendation="Never use allow_credentials=True with wildcard origins",
                evidence="allow_origins=['*'] with allow_credentials=True",
                cwe_id="CWE-942"
            ))
        
        return findings
    
    def _scan_middleware(
        self,
        content: str,
        file_path: str
    ) -> List[APIFinding]:
        """Scan middleware configuration."""
        findings = []
        
        # Check for rate limiting
        has_rate_limiting = any(pattern in content for pattern in [
            'RateLimitMiddleware',
            'slowapi',
            'rate_limit',
            'throttle'
        ])
        
        if not has_rate_limiting:
            findings.append(APIFinding(
                check_type=APISecurityCheck.RATE_LIMITING,
                severity=SeverityLevel.MEDIUM,
                endpoint=None,
                description="No rate limiting middleware detected",
                recommendation="Implement rate limiting using slowapi or custom middleware",
                evidence=None,
                cwe_id="CWE-770"
            ))
        
        # Check for security headers middleware
        has_security_headers = any(pattern in content for pattern in [
            'SecurityHeadersMiddleware',
            'secure_headers',
            'X-Content-Type-Options',
            'X-Frame-Options'
        ])
        
        if not has_security_headers:
            findings.append(APIFinding(
                check_type=APISecurityCheck.HEADERS,
                severity=SeverityLevel.MEDIUM,
                endpoint=None,
                description="Security headers middleware not detected",
                recommendation="Add middleware to set security headers (X-Content-Type-Options, X-Frame-Options, etc.)",
                evidence=None,
                cwe_id="CWE-693"
            ))
        
        # Check for request logging
        has_logging = any(pattern in content for pattern in [
            'LoggingMiddleware',
            'access_log',
            'request_log',
            'audit_log'
        ])
        
        if not has_logging:
            findings.append(APIFinding(
                check_type=APISecurityCheck.LOGGING,
                severity=SeverityLevel.LOW,
                endpoint=None,
                description="Request logging middleware not detected",
                recommendation="Implement request logging for security monitoring and audit trails",
                evidence=None,
                cwe_id="CWE-778"
            ))
        
        return findings
    
    def scan_openapi_spec(self, spec_path: str) -> APIScanResult:
        """
        Scan OpenAPI specification for security issues.
        
        Args:
            spec_path: Path to OpenAPI JSON/YAML file
        
        Returns:
            APIScanResult with findings
        """
        import json
        
        findings = []
        endpoints_scanned = 0
        
        try:
            with open(spec_path, 'r') as f:
                if spec_path.endswith('.json'):
                    spec = json.load(f)
                else:
                    # Would need PyYAML for YAML files
                    raise NotImplementedError("YAML parsing requires PyYAML")
        except Exception as e:
            logger.error(f"Error loading OpenAPI spec: {e}")
            return APIScanResult(
                api_name=spec_path,
                endpoints_scanned=0,
                findings=[],
                security_score=0.0
            )
        
        # Check security definitions
        security_schemes = spec.get('components', {}).get('securitySchemes', {})
        
        if not security_schemes:
            findings.append(APIFinding(
                check_type=APISecurityCheck.AUTHENTICATION,
                severity=SeverityLevel.HIGH,
                endpoint=None,
                description="No security schemes defined in OpenAPI spec",
                recommendation="Define security schemes (OAuth2, API Key, Bearer, etc.)",
                evidence=None,
                cwe_id="CWE-306"
            ))
        
        # Check each endpoint
        paths = spec.get('paths', {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    endpoints_scanned += 1
                    
                    # Check for security requirement
                    endpoint_security = details.get('security', spec.get('security', []))
                    
                    if not endpoint_security:
                        findings.append(APIFinding(
                            check_type=APISecurityCheck.AUTHENTICATION,
                            severity=SeverityLevel.MEDIUM,
                            endpoint=f"{method.upper()} {path}",
                            description=f"Endpoint has no security requirement",
                            recommendation="Add security requirement or explicitly mark as public",
                            evidence=None,
                            cwe_id="CWE-306"
                        ))
        
        security_score = self._calculate_score(findings)
        
        return APIScanResult(
            api_name=spec_path,
            endpoints_scanned=endpoints_scanned,
            findings=findings,
            security_score=security_score
        )
    
    def _calculate_score(self, findings: List[APIFinding]) -> float:
        """Calculate API security score (0-100)."""
        score = 100.0
        
        severity_deductions = {
            SeverityLevel.CRITICAL: 20,
            SeverityLevel.HIGH: 10,
            SeverityLevel.MEDIUM: 5,
            SeverityLevel.LOW: 2,
            SeverityLevel.INFO: 0
        }
        
        for finding in findings:
            score -= severity_deductions.get(finding.severity, 0)
        
        return max(0.0, score)
    
    def _check_compliance(self, findings: List[APIFinding]) -> Dict[str, bool]:
        """Check compliance with security standards."""
        checks = {
            "authentication_configured": True,
            "rate_limiting_enabled": True,
            "cors_restricted": True,
            "security_headers_set": True,
            "logging_enabled": True,
            "no_critical_issues": True
        }
        
        for finding in findings:
            if finding.check_type == APISecurityCheck.AUTHENTICATION:
                checks["authentication_configured"] = False
            elif finding.check_type == APISecurityCheck.RATE_LIMITING:
                checks["rate_limiting_enabled"] = False
            elif finding.check_type == APISecurityCheck.CORS:
                checks["cors_restricted"] = False
            elif finding.check_type == APISecurityCheck.HEADERS:
                checks["security_headers_set"] = False
            elif finding.check_type == APISecurityCheck.LOGGING:
                checks["logging_enabled"] = False
            
            if finding.severity == SeverityLevel.CRITICAL:
                checks["no_critical_issues"] = False
        
        return checks
