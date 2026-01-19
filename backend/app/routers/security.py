"""
Security Analysis API Router

FastAPI endpoints for security vulnerability scanning.
Provides:
- Code snippet analysis
- File upload scanning
- Project-wide security audits
- API security assessment
- Report generation
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
import tempfile
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["Security Analysis"])


# Request/Response Models
class CodeSnippetRequest(BaseModel):
    """Request model for code snippet analysis."""
    code: str = Field(..., description="Source code to analyze")
    language: str = Field(default="python", description="Programming language")
    generate_mitigations: bool = Field(default=True, description="Generate fix suggestions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "password = 'admin123'\nquery = f'SELECT * FROM users WHERE id = {user_id}'",
                "language": "python",
                "generate_mitigations": True
            }
        }


class ScanConfigRequest(BaseModel):
    """Configuration for project scanning."""
    include_api_scan: bool = Field(default=True, description="Include API security scan")
    generate_mitigations: bool = Field(default=True, description="Generate mitigation plans")
    max_workers: int = Field(default=4, ge=1, le=16, description="Parallel workers")
    file_extensions: Optional[List[str]] = Field(
        default=None,
        description="File extensions to scan (e.g., ['.py', '.js'])"
    )


class ScanStatusResponse(BaseModel):
    """Response model for scan status."""
    scan_id: str
    status: str
    progress: float
    message: Optional[str] = None


class FindingSummary(BaseModel):
    """Summary of security findings."""
    total: int
    critical: int
    high: int
    medium: int
    low: int


class QuickFixRequest(BaseModel):
    """Request for quick fix suggestions."""
    vulnerability_type: str = Field(..., description="Vulnerability category")
    
    class Config:
        json_schema_extra = {
            "example": {
                "vulnerability_type": "INJECTION"
            }
        }


# In-memory scan storage (use Redis/DB in production)
_scan_results = {}


def get_pipeline():
    """Dependency to get security pipeline instance."""
    try:
        from ..security_ai.pipeline.inference import SecurityInferencePipeline
        return SecurityInferencePipeline()
    except ImportError as e:
        logger.error(f"Failed to import security pipeline: {e}")
        raise HTTPException(
            status_code=503,
            detail="Security analysis service not available. Ensure TensorFlow is installed."
        )


@router.post("/scan/code", summary="Analyze code snippet for vulnerabilities")
async def scan_code_snippet(
    request: CodeSnippetRequest,
    pipeline = Depends(get_pipeline)
):
    """
    Analyze a code snippet for security vulnerabilities.
    
    Returns detected vulnerabilities with severity levels and optional mitigation guidance.
    
    **Supported Languages**: Python, JavaScript, TypeScript, Java, Go, Rust
    
    **Detection Categories**:
    - SQL/Command Injection
    - Hardcoded Secrets
    - Authentication Issues
    - XSS Vulnerabilities
    - Path Traversal
    - Insecure Cryptography
    """
    try:
        result = pipeline.analyze_code_snippet(
            code=request.code,
            language=request.language,
            generate_mitigations=request.generate_mitigations
        )
        
        return {
            "success": True,
            "data": result,
            "summary": result.get("summary", {})
        }
    except Exception as e:
        logger.error(f"Code analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan/file", summary="Upload and scan a file")
async def scan_file(
    file: UploadFile = File(...),
    generate_mitigations: bool = Form(default=True),
    pipeline = Depends(get_pipeline)
):
    """
    Upload a source file for security analysis.
    
    **Supported File Types**: .py, .js, .ts, .java, .go, .rs, .c, .cpp, .h
    
    **Max File Size**: 10MB
    """
    # Validate file
    allowed_extensions = {'.py', '.js', '.ts', '.java', '.go', '.rs', '.c', '.cpp', '.h'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Read file content
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large. Max size: 10MB")
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='wb', suffix=file_ext, delete=False) as f:
        f.write(content)
        temp_path = f.name
    
    try:
        result = pipeline.analyze_file(
            file_path=temp_path,
            generate_mitigations=generate_mitigations
        )
        
        return {
            "success": True,
            "filename": file.filename,
            "analysis_id": result.analysis_id,
            "security_score": result.overall_score,
            "findings_count": result.summary.get("total_findings", 0),
            "findings": result.code_analysis.file_results[0].to_dict() if result.code_analysis else None,
            "mitigations": [p.to_dict() for p in result.mitigation_plans]
        }
    finally:
        os.unlink(temp_path)


@router.post("/scan/project", summary="Scan entire project directory")
async def scan_project(
    project_path: str = Form(..., description="Path to project directory"),
    config: Optional[str] = Form(default=None, description="JSON scan configuration"),
    background_tasks: BackgroundTasks = None,
    pipeline = Depends(get_pipeline)
):
    """
    Perform comprehensive security scan on a project directory.
    
    This is a potentially long-running operation. For large projects,
    consider using async scan with status polling.
    
    **Scans Include**:
    - Source code vulnerability detection
    - API security assessment
    - Configuration file analysis
    - Dependency audit (if supported)
    """
    import json
    import uuid
    
    # Validate path exists
    if not Path(project_path).exists():
        raise HTTPException(status_code=404, detail=f"Project path not found: {project_path}")
    
    # Parse config
    scan_config = ScanConfigRequest()
    if config:
        try:
            config_data = json.loads(config)
            scan_config = ScanConfigRequest(**config_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON configuration")
    
    try:
        result = pipeline.analyze_project(
            project_path=project_path,
            include_api_scan=scan_config.include_api_scan,
            generate_mitigations=scan_config.generate_mitigations,
            max_workers=scan_config.max_workers
        )
        
        # Store result for retrieval
        _scan_results[result.analysis_id] = result
        
        return {
            "success": True,
            "analysis_id": result.analysis_id,
            "timestamp": result.timestamp,
            "duration_seconds": result.duration_seconds,
            "security_score": result.overall_score,
            "summary": result.summary,
            "files_analyzed": result.code_analysis.files_analyzed if result.code_analysis else 0,
            "requires_attention": result.summary.get("requires_immediate_attention", False)
        }
    except Exception as e:
        logger.error(f"Project scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scan/{scan_id}", summary="Get scan results by ID")
async def get_scan_results(scan_id: str):
    """
    Retrieve detailed results for a completed security scan.
    
    Returns full analysis including:
    - All detected vulnerabilities
    - Severity breakdown
    - Mitigation recommendations
    - Security score
    """
    if scan_id not in _scan_results:
        raise HTTPException(status_code=404, detail=f"Scan not found: {scan_id}")
    
    result = _scan_results[scan_id]
    return {
        "success": True,
        "data": result.to_dict()
    }


@router.get("/scan/{scan_id}/report", summary="Download scan report")
async def download_scan_report(
    scan_id: str,
    format: str = "json"
):
    """
    Download security analysis report.
    
    **Available Formats**:
    - `json`: Machine-readable JSON format
    - `html`: Human-readable HTML report
    """
    if scan_id not in _scan_results:
        raise HTTPException(status_code=404, detail=f"Scan not found: {scan_id}")
    
    result = _scan_results[scan_id]
    
    if format not in ["json", "html"]:
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'html'")
    
    # Create temp file for report
    try:
        from ..security_ai.pipeline.inference import SecurityInferencePipeline
        pipeline = SecurityInferencePipeline()
    except ImportError:
        raise HTTPException(status_code=503, detail="Report generation unavailable")
    
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix=f".{format}",
        delete=False
    ) as f:
        output_path = f.name
    
    pipeline.save_report(result, output_path, format=format)
    
    return FileResponse(
        path=output_path,
        filename=f"security_report_{scan_id}.{format}",
        media_type="application/json" if format == "json" else "text/html"
    )


@router.post("/api/scan", summary="Scan API for security issues")
async def scan_api(
    project_path: str = Form(..., description="Path to FastAPI project"),
    openapi_url: Optional[str] = Form(default=None, description="OpenAPI spec URL"),
    pipeline = Depends(get_pipeline)
):
    """
    Perform API security assessment.
    
    Checks for:
    - Authentication configuration
    - Authorization patterns
    - Rate limiting
    - CORS settings
    - Security headers
    - Input validation
    """
    if not Path(project_path).exists():
        raise HTTPException(status_code=404, detail=f"Project path not found: {project_path}")
    
    try:
        from ..security_ai.services.api_scanner import APISecurityScanner
        scanner = APISecurityScanner()
        
        result = scanner.scan_fastapi_app(project_path)
        
        return {
            "success": True,
            "security_score": result.security_score,
            "endpoints_scanned": result.endpoints_scanned,
            "findings": [f.to_dict() for f in result.findings],
            "compliance_checklist": result.compliance_checklist
        }
    except Exception as e:
        logger.error(f"API scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-fix", summary="Get quick fix for vulnerability type")
async def get_quick_fix(request: QuickFixRequest):
    """
    Get quick remediation guidance for a specific vulnerability type.
    
    **Supported Vulnerability Types**:
    - INJECTION
    - HARDCODED_SECRETS
    - BROKEN_AUTH
    - XSS
    - PATH_TRAVERSAL
    - INSECURE_CRYPTO
    - SSRF
    """
    try:
        from ..security_ai.services.mitigation_engine import MitigationEngine
        from ..security_ai.config import VulnerabilityCategory, SeverityLevel
        
        engine = MitigationEngine()
        
        # Map string to category
        try:
            category = VulnerabilityCategory[request.vulnerability_type.upper()]
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown vulnerability type: {request.vulnerability_type}"
            )
        
        quick_fix = engine.get_quick_fix(category)
        
        return {
            "success": True,
            "vulnerability_type": request.vulnerability_type,
            "quick_fix": quick_fix
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick fix generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories", summary="List supported vulnerability categories")
async def list_categories():
    """
    Get list of all supported vulnerability detection categories.
    """
    try:
        from ..security_ai.config import VulnerabilityCategory, SeverityLevel
        
        categories = [
            {
                "id": cat.value,
                "name": cat.name,
                "description": _get_category_description(cat)
            }
            for cat in VulnerabilityCategory
        ]
        
        severity_levels = [
            {
                "id": level.value,
                "name": level.name
            }
            for level in SeverityLevel
        ]
        
        return {
            "success": True,
            "categories": categories,
            "severity_levels": severity_levels
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="Security module not available")


def _get_category_description(category) -> str:
    """Get description for vulnerability category."""
    descriptions = {
        "INJECTION": "SQL, Command, and other injection vulnerabilities",
        "HARDCODED_SECRETS": "Hardcoded passwords, API keys, and credentials",
        "BROKEN_AUTH": "Authentication and session management flaws",
        "XSS": "Cross-site scripting vulnerabilities",
        "PATH_TRAVERSAL": "Directory traversal and file access issues",
        "INSECURE_DESERIALIZATION": "Unsafe deserialization of untrusted data",
        "INSECURE_CRYPTO": "Weak cryptographic algorithms and implementations",
        "SSRF": "Server-side request forgery",
        "SECURITY_MISCONFIGURATION": "Security configuration issues",
        "INSUFFICIENT_LOGGING": "Inadequate logging and monitoring",
        "XXEXML": "XML External Entity vulnerabilities",
        "CORS_MISCONFIGURATION": "Cross-Origin Resource Sharing issues",
        "OPEN_REDIRECT": "URL redirection vulnerabilities",
        "MASS_ASSIGNMENT": "Mass assignment/object binding issues",
        "INFORMATION_DISCLOSURE": "Sensitive data exposure"
    }
    return descriptions.get(category.value, "Security vulnerability")


@router.get("/health", summary="Security service health check")
async def health_check():
    """
    Check if security analysis service is operational.
    """
    try:
        from ..security_ai.pipeline.inference import SecurityInferencePipeline
        from ..security_ai.config import get_config
        
        config = get_config()
        
        return {
            "status": "healthy",
            "environment": config.environment.value,
            "tensorflow_available": True,
            "models_loaded": False,  # Lazy loading
            "version": "1.0.0"
        }
    except ImportError as e:
        return {
            "status": "degraded",
            "error": str(e),
            "tensorflow_available": False
        }
