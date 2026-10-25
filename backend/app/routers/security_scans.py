"""
Security AI scans backed by the hybrid detection engine.

Scans are persisted so the Security dashboard reports real numbers.
When no trained ML model is available, the engine runs in rules-only mode
and the API says so explicitly instead of reporting model metrics.
"""

import time
from collections import Counter
from datetime import datetime
from functools import lru_cache
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.security_scan import SecurityScan
from app.models.user import User
from app.utils.security import get_current_user

router = APIRouter(prefix="/security", tags=["Security Analysis"])

SEVERITIES = ["critical", "high", "medium", "low", "info"]

CATEGORY_KEYWORDS = [
    ("sql", "sql_injection"),
    ("command", "command_injection"),
    ("path traversal", "path_traversal"),
    ("xss", "xss"),
    ("cross-site", "xss"),
    ("credential", "hardcoded_secret"),
    ("secret", "hardcoded_secret"),
    ("password", "hardcoded_secret"),
    ("api key", "hardcoded_secret"),
    ("crypto", "weak_crypto"),
    ("hash", "weak_crypto"),
    ("random", "weak_crypto"),
    ("auth", "auth_bypass"),
    ("debug", "insecure_config"),
    ("config", "insecure_config"),
    ("access", "access_control"),
    ("deserializ", "data_exposure"),
    ("log", "data_exposure"),
]


class ScanRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=200_000)
    filename: str = "snippet.py"
    language: str = "python"
    detection_mode: Literal["full", "rules_only", "critical_only"] = "full"


@lru_cache(maxsize=1)
def _detector():
    from app.security_ai.hybrid_engine.hybrid_detector import HybridConfig, HybridSecurityDetector

    return HybridSecurityDetector(HybridConfig(use_gpu=False))


def _ml_available() -> bool:
    return bool(_detector().get_statistics().get("ml_engine", {}).get("loaded"))


def _category(name: str, cwe: Optional[str]) -> str:
    text = f"{name} {cwe or ''}".lower()
    for keyword, category in CATEGORY_KEYWORDS:
        if keyword in text:
            return category
    return "other"


def _source(value: str) -> str:
    if value in ("rule_only", "rule_override"):
        return "rule"
    if value == "ml_only":
        return "ml"
    return "hybrid"


def _serialize_findings(result, filename: str) -> List[dict]:
    findings = []
    for index, vuln in enumerate(result.vulnerabilities):
        severity = vuln.severity.value
        if severity == "suppressed":
            continue
        findings.append({
            "id": f"{vuln.vulnerability_id}-{index}",
            "title": vuln.name,
            "description": vuln.description,
            "severity": severity,
            "category": _category(vuln.name, vuln.cwe_id),
            "cwe_id": vuln.cwe_id,
            "owasp_category": vuln.owasp_category,
            "detection_source": _source(vuln.source.value),
            "confidence_score": round(vuln.confidence.combined_score, 3),
            "mitigation": vuln.remediation,
            "file_path": filename,
            "line_number": vuln.affected_lines[0] if vuln.affected_lines else None,
            "code_snippet": vuln.code_snippets[0] if vuln.code_snippets else None,
            "false_positive_flag": False,
        })
    return findings


def _to_response(scan: SecurityScan) -> dict:
    created = scan.created_at or datetime.now()
    findings = scan.findings or []
    sources = Counter(f["detection_source"] for f in findings)
    return {
        "scan_id": str(scan.id),
        "status": "completed",
        "scan_type": "source_code",
        "detection_mode": scan.detection_mode,
        "filename": scan.filename,
        "language": scan.language,
        "started_at": created.isoformat(),
        "completed_at": created.isoformat(),
        "duration_ms": scan.duration_ms,
        "vulnerabilities": [{**f, "id": f"{scan.id}-{f['id']}", "created_at": created.isoformat()} for f in findings],
        "summary": {
            "total": scan.total,
            "critical": scan.critical,
            "high": scan.high,
            "medium": scan.medium,
            "low": scan.low,
            "info": scan.info,
        },
        "rule_detections": sources.get("rule", 0),
        "ml_detections": sources.get("ml", 0),
        "hybrid_detections": sources.get("hybrid", 0),
    }


@router.post("/scans", summary="Scan source code and store the result")
def create_scan(
    request: ScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.security_ai.hybrid_engine.hybrid_detector import DetectionMode

    ml_loaded = _ml_available()
    mode = request.detection_mode
    # Without trained weights the ML layer would only produce placeholder output
    effective_mode = "rules_only" if (mode == "full" and not ml_loaded) else mode
    engine_mode = {
        "full": DetectionMode.FULL,
        "rules_only": DetectionMode.RULES_ONLY,
        "critical_only": DetectionMode.CRITICAL_ONLY,
    }[effective_mode]

    started = time.perf_counter()
    try:
        result = _detector().scan(request.content, request.filename, mode=engine_mode)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Scan failed: {exc}")
    duration = (time.perf_counter() - started) * 1000

    findings = _serialize_findings(result, request.filename)
    counts = Counter(f["severity"] for f in findings)

    scan = SecurityScan(
        filename=request.filename,
        language=request.language,
        detection_mode=effective_mode,
        duration_ms=round(duration, 2),
        total=len(findings),
        findings=findings,
        created_by=current_user.id,
        **{s: counts.get(s, 0) for s in SEVERITIES},
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    response = _to_response(scan)
    response["ml_model_loaded"] = ml_loaded
    return response


@router.get("/scans", summary="List recent scans")
def list_scans(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scans = db.query(SecurityScan).order_by(SecurityScan.created_at.desc()).limit(min(limit, 100)).all()
    return [_to_response(s) for s in scans]


@router.get("/dashboard/stats", summary="Aggregated Security AI statistics")
def dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scans = db.query(SecurityScan).order_by(SecurityScan.created_at.desc()).all()
    findings = [f for s in scans for f in (s.findings or [])]

    severity = {s: sum(getattr(scan, s) for scan in scans) for s in SEVERITIES}
    categories = Counter(f["category"] for f in findings)
    sources = Counter(f["detection_source"] for f in findings)
    for key in ("rule", "ml", "hybrid"):
        sources.setdefault(key, 0)

    priority = {s: i for i, s in enumerate(SEVERITIES)}
    findings = [{**f, "id": f"{s.id}-{f['id']}"} for s in scans for f in (s.findings or [])]
    top = sorted(findings, key=lambda f: (priority.get(f["severity"], 9), -f.get("confidence_score", 0)))[:5]

    engine = _detector().get_statistics()
    return {
        "total_scans": len(scans),
        "total_vulnerabilities": len(findings),
        "open_vulnerabilities": severity["critical"] + severity["high"] + severity["medium"],
        "resolved_vulnerabilities": 0,
        "severity_distribution": severity,
        "category_distribution": dict(categories),
        "detection_source_distribution": dict(sources),
        "recent_scans": [_to_response(s) for s in scans[:5]],
        "top_vulnerabilities": top,
        # No trained model is bundled, so model quality metrics are not reported
        "model_accuracy": None,
        "false_positive_rate": None,
        "ml_model_loaded": bool(engine.get("ml_engine", {}).get("loaded")),
        "rule_engine": engine.get("rule_engine", {}),
    }


@router.get("/engine/rules", summary="Rules loaded in the detection engine")
def engine_rules(current_user: User = Depends(get_current_user)):
    rules = []
    for rule in _detector().rule_engine.rules:
        rules.append({
            "id": rule.rule_id,
            "name": rule.name,
            "description": rule.description,
            "severity": rule.severity.value,
            "category": rule.category.value,
            "cwe_id": rule.cwe_id,
            "patterns": len(rule.patterns),
            "remediation": rule.remediation,
            "enabled": rule.enabled,
        })
    return rules
