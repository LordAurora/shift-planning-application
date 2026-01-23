"""
Mitigation Engine

AI-powered remediation guidance generator for security vulnerabilities.
Provides:
- Secure code fixes
- Configuration hardening recommendations
- Best practice guidance
- OWASP compliance mapping
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from ..config import (
    SecurityAIConfig,
    VulnerabilityCategory,
    SeverityLevel,
    get_config
)

logger = logging.getLogger(__name__)


@dataclass
class MitigationStep:
    """Single mitigation step."""
    step_number: int
    title: str
    description: str
    code_example: Optional[str] = None
    references: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_number,
            "title": self.title,
            "description": self.description,
            "code_example": self.code_example,
            "references": self.references
        }


@dataclass
class MitigationPlan:
    """Complete mitigation plan for a vulnerability."""
    vulnerability_category: VulnerabilityCategory
    severity: SeverityLevel
    summary: str
    estimated_effort: str  # Low, Medium, High
    steps: List[MitigationStep]
    owasp_mapping: Optional[str] = None
    cwe_mapping: Optional[str] = None
    priority: int = 1  # 1 = highest priority
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.vulnerability_category.value,
            "severity": self.severity.value,
            "summary": self.summary,
            "estimated_effort": self.estimated_effort,
            "steps": [s.to_dict() for s in self.steps],
            "owasp_mapping": self.owasp_mapping,
            "cwe_mapping": self.cwe_mapping,
            "priority": self.priority
        }


class MitigationEngine:
    """
    AI-powered mitigation guidance generator.
    
    Generates context-aware remediation plans based on:
    - Vulnerability type and severity
    - Technology stack
    - Industry best practices
    - OWASP guidelines
    
    Example:
        engine = MitigationEngine()
        
        plan = engine.generate_plan(
            category=VulnerabilityCategory.INJECTION,
            context={"language": "python", "framework": "fastapi"}
        )
        
        for step in plan.steps:
            print(f"{step.step_number}. {step.title}")
    """
    
    # OWASP Top 10 mapping
    OWASP_MAPPING = {
        VulnerabilityCategory.INJECTION: "A03:2021 - Injection",
        VulnerabilityCategory.BROKEN_AUTH: "A07:2021 - Identification and Authentication Failures",
        VulnerabilityCategory.SENSITIVE_DATA: "A02:2021 - Cryptographic Failures",
        VulnerabilityCategory.XXE: "A05:2021 - Security Misconfiguration",
        VulnerabilityCategory.BROKEN_ACCESS: "A01:2021 - Broken Access Control",
        VulnerabilityCategory.MISCONFIG: "A05:2021 - Security Misconfiguration",
        VulnerabilityCategory.XSS: "A03:2021 - Injection",
        VulnerabilityCategory.INSECURE_DESERIALIZATION: "A08:2021 - Software and Data Integrity Failures",
        VulnerabilityCategory.VULNERABLE_COMPONENTS: "A06:2021 - Vulnerable and Outdated Components",
        VulnerabilityCategory.INSUFFICIENT_LOGGING: "A09:2021 - Security Logging and Monitoring Failures",
        VulnerabilityCategory.SSRF: "A10:2021 - Server-Side Request Forgery",
    }
    
    # CWE mapping
    CWE_MAPPING = {
        VulnerabilityCategory.INJECTION: "CWE-89, CWE-78, CWE-94",
        VulnerabilityCategory.BROKEN_AUTH: "CWE-287, CWE-384",
        VulnerabilityCategory.SENSITIVE_DATA: "CWE-311, CWE-312, CWE-319",
        VulnerabilityCategory.XXE: "CWE-611",
        VulnerabilityCategory.BROKEN_ACCESS: "CWE-284, CWE-285",
        VulnerabilityCategory.MISCONFIG: "CWE-16",
        VulnerabilityCategory.XSS: "CWE-79",
        VulnerabilityCategory.INSECURE_DESERIALIZATION: "CWE-502",
        VulnerabilityCategory.HARDCODED_SECRETS: "CWE-798",
        VulnerabilityCategory.PATH_TRAVERSAL: "CWE-22",
        VulnerabilityCategory.INSECURE_CRYPTO: "CWE-327, CWE-328",
        VulnerabilityCategory.SSRF: "CWE-918",
    }
    
    def __init__(self, config: Optional[SecurityAIConfig] = None):
        """Initialize mitigation engine."""
        self.config = config or get_config()
        self._mitigation_templates = self._load_templates()
    
    def _load_templates(self) -> Dict[VulnerabilityCategory, Dict[str, Any]]:
        """Load mitigation templates."""
        return {
            VulnerabilityCategory.INJECTION: {
                "summary": "Prevent code/command injection by using parameterized queries and input validation",
                "effort": "Medium",
                "steps": [
                    {
                        "title": "Use Parameterized Queries",
                        "description": "Never concatenate user input directly into queries. Use parameterized queries or ORM methods.",
                        "python_example": '''# Bad - vulnerable to SQL injection
query = f"SELECT * FROM users WHERE id = {user_id}"

# Good - parameterized query
from sqlalchemy import text
result = db.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})

# Best - use ORM
user = db.query(User).filter(User.id == user_id).first()''',
                    },
                    {
                        "title": "Validate and Sanitize Input",
                        "description": "Implement strict input validation for all user-supplied data.",
                        "python_example": '''from pydantic import BaseModel, validator, conint

class UserInput(BaseModel):
    user_id: conint(gt=0, lt=1000000)  # Constrained integer
    
    @validator('user_id')
    def validate_id(cls, v):
        if not isinstance(v, int):
            raise ValueError('ID must be an integer')
        return v''',
                    },
                    {
                        "title": "Use Allowlists",
                        "description": "When dynamic values are necessary, validate against an allowlist of permitted values.",
                        "python_example": '''ALLOWED_SORT_COLUMNS = {'name', 'created_at', 'email'}

def get_users(sort_by: str):
    if sort_by not in ALLOWED_SORT_COLUMNS:
        raise ValueError(f"Invalid sort column: {sort_by}")
    # Now safe to use sort_by''',
                    }
                ],
                "references": [
                    "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html",
                    "https://cheatsheetseries.owasp.org/cheatsheets/Query_Parameterization_Cheat_Sheet.html"
                ]
            },
            VulnerabilityCategory.HARDCODED_SECRETS: {
                "summary": "Remove hardcoded credentials and use secure secret management",
                "effort": "Low",
                "steps": [
                    {
                        "title": "Remove Hardcoded Secrets",
                        "description": "Immediately remove all hardcoded passwords, API keys, and tokens from source code.",
                        "python_example": '''# Bad - hardcoded secret
API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "supersecretpassword"

# Good - environment variables
import os
API_KEY = os.environ.get("API_KEY")
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD")

# Best - use a secret management service
from app.utils.secrets import get_secret
API_KEY = get_secret("api_key")''',
                    },
                    {
                        "title": "Use Environment Variables",
                        "description": "Store sensitive configuration in environment variables, never in code.",
                        "python_example": '''# .env file (never commit to version control)
DATABASE_URL=postgresql://user:pass@localhost/db
SECRET_KEY=your-secret-key-here

# Python with python-dotenv
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")''',
                    },
                    {
                        "title": "Implement Secret Management",
                        "description": "Use dedicated secret management (HashiCorp Vault, AWS Secrets Manager, etc.)",
                        "python_example": '''# Using HashiCorp Vault
import hvac

client = hvac.Client(url='https://vault.example.com')
secret = client.secrets.kv.v2.read_secret_version(
    path='myapp/database'
)
password = secret['data']['data']['password']''',
                    },
                    {
                        "title": "Rotate Compromised Secrets",
                        "description": "If secrets were committed to version control, consider them compromised and rotate immediately.",
                    }
                ],
                "references": [
                    "https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html",
                    "https://www.vaultproject.io/docs/what-is-vault"
                ]
            },
            VulnerabilityCategory.BROKEN_AUTH: {
                "summary": "Strengthen authentication mechanisms and session management",
                "effort": "Medium",
                "steps": [
                    {
                        "title": "Enable SSL/TLS Verification",
                        "description": "Never disable SSL certificate verification in production.",
                        "python_example": '''# Bad - SSL verification disabled
requests.get(url, verify=False)

# Good - proper SSL verification
requests.get(url, verify=True)
# Or with custom CA bundle
requests.get(url, verify='/path/to/ca-bundle.crt')''',
                    },
                    {
                        "title": "Implement Strong Password Policies",
                        "description": "Enforce minimum password requirements and use secure hashing.",
                        "python_example": '''from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)''',
                    },
                    {
                        "title": "Use Secure Session Management",
                        "description": "Implement secure session tokens with proper expiration.",
                        "python_example": '''from datetime import datetime, timedelta
import jwt

def create_token(user_id: int) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")''',
                    }
                ],
                "references": [
                    "https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html",
                    "https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html"
                ]
            },
            VulnerabilityCategory.XSS: {
                "summary": "Prevent cross-site scripting through proper output encoding and CSP",
                "effort": "Medium",
                "steps": [
                    {
                        "title": "Encode Output",
                        "description": "Always encode user-supplied data before rendering in HTML.",
                        "python_example": '''from markupsafe import escape

# In templates
# Bad
<div>{{ user_input }}</div>

# Good - auto-escaped in modern frameworks
<div>{{ user_input | e }}</div>

# In Python
safe_output = escape(user_input)''',
                    },
                    {
                        "title": "Implement Content Security Policy",
                        "description": "Add CSP headers to restrict resource loading.",
                        "python_example": '''# FastAPI middleware
from fastapi import FastAPI
from starlette.middleware import Middleware

app.add_middleware(
    SecurityHeadersMiddleware,
    csp="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
)''',
                    },
                    {
                        "title": "Sanitize Rich Text Input",
                        "description": "Use a sanitization library for any HTML input.",
                        "python_example": '''import bleach

# Sanitize HTML input
allowed_tags = ['p', 'br', 'strong', 'em', 'a']
allowed_attrs = {'a': ['href', 'title']}

clean_html = bleach.clean(
    user_html,
    tags=allowed_tags,
    attributes=allowed_attrs
)''',
                    }
                ],
                "references": [
                    "https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html",
                    "https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html"
                ]
            },
            VulnerabilityCategory.INSECURE_CRYPTO: {
                "summary": "Replace weak cryptographic algorithms with modern secure alternatives",
                "effort": "Low",
                "steps": [
                    {
                        "title": "Use Strong Hashing Algorithms",
                        "description": "Replace MD5/SHA1 with SHA-256 or SHA-3 for hashing.",
                        "python_example": '''import hashlib

# Bad - weak algorithms
hash_md5 = hashlib.md5(data).hexdigest()
hash_sha1 = hashlib.sha1(data).hexdigest()

# Good - strong algorithms
hash_sha256 = hashlib.sha256(data).hexdigest()
hash_sha3 = hashlib.sha3_256(data).hexdigest()''',
                    },
                    {
                        "title": "Use bcrypt/Argon2 for Passwords",
                        "description": "Never use regular hashing for passwords. Use password-specific algorithms.",
                        "python_example": '''# Best practice for password hashing
from argon2 import PasswordHasher

ph = PasswordHasher()
hashed = ph.hash(password)
is_valid = ph.verify(hashed, password)''',
                    },
                    {
                        "title": "Use Cryptographically Secure Random",
                        "description": "Use secrets module for security-sensitive random values.",
                        "python_example": '''import secrets

# Bad - not cryptographically secure
import random
token = ''.join(random.choices(string.ascii_letters, k=32))

# Good - cryptographically secure
token = secrets.token_urlsafe(32)
api_key = secrets.token_hex(32)''',
                    }
                ],
                "references": [
                    "https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html",
                    "https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html"
                ]
            },
            VulnerabilityCategory.PATH_TRAVERSAL: {
                "summary": "Prevent directory traversal attacks through path validation",
                "effort": "Low",
                "steps": [
                    {
                        "title": "Validate File Paths",
                        "description": "Never use user input directly in file paths.",
                        "python_example": '''from pathlib import Path

SAFE_DIR = Path("/app/uploads")

def get_file(filename: str):
    # Resolve the full path
    file_path = (SAFE_DIR / filename).resolve()
    
    # Verify it's still within safe directory
    if not str(file_path).startswith(str(SAFE_DIR.resolve())):
        raise ValueError("Invalid file path")
    
    return file_path''',
                    },
                    {
                        "title": "Use Allowlist for Files",
                        "description": "Maintain a list of allowed files instead of accepting arbitrary paths.",
                        "python_example": '''ALLOWED_FILES = {
    'report': '/app/reports/report.pdf',
    'manual': '/app/docs/manual.pdf'
}

def download_file(file_key: str):
    if file_key not in ALLOWED_FILES:
        raise ValueError("File not found")
    return ALLOWED_FILES[file_key]''',
                    }
                ],
                "references": [
                    "https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html"
                ]
            }
        }
    
    def generate_plan(
        self,
        category: VulnerabilityCategory,
        severity: SeverityLevel = SeverityLevel.MEDIUM,
        context: Optional[Dict[str, Any]] = None
    ) -> MitigationPlan:
        """
        Generate mitigation plan for a vulnerability.
        
        Args:
            category: Vulnerability category
            severity: Severity level
            context: Optional context (language, framework, etc.)
        
        Returns:
            MitigationPlan with steps and guidance
        """
        context = context or {}
        language = context.get("language", "python")
        
        template = self._mitigation_templates.get(category)
        
        if template is None:
            return self._generate_generic_plan(category, severity)
        
        # Build steps from template
        steps = []
        for i, step_data in enumerate(template["steps"], 1):
            code_example = step_data.get(f"{language}_example") or step_data.get("python_example")
            
            steps.append(MitigationStep(
                step_number=i,
                title=step_data["title"],
                description=step_data["description"],
                code_example=code_example,
                references=template.get("references", [])
            ))
        
        return MitigationPlan(
            vulnerability_category=category,
            severity=severity,
            summary=template["summary"],
            estimated_effort=template["effort"],
            steps=steps,
            owasp_mapping=self.OWASP_MAPPING.get(category),
            cwe_mapping=self.CWE_MAPPING.get(category),
            priority=self._calculate_priority(severity)
        )
    
    def _generate_generic_plan(
        self,
        category: VulnerabilityCategory,
        severity: SeverityLevel
    ) -> MitigationPlan:
        """Generate generic mitigation plan for unmapped categories."""
        return MitigationPlan(
            vulnerability_category=category,
            severity=severity,
            summary=f"Address {category.value} vulnerability following security best practices",
            estimated_effort="Medium",
            steps=[
                MitigationStep(
                    step_number=1,
                    title="Identify Affected Code",
                    description="Locate all instances of the vulnerability in your codebase",
                    references=["https://owasp.org/www-project-web-security-testing-guide/"]
                ),
                MitigationStep(
                    step_number=2,
                    title="Apply Security Fix",
                    description=f"Follow OWASP guidelines for remediating {category.value}",
                    references=["https://cheatsheetseries.owasp.org/"]
                ),
                MitigationStep(
                    step_number=3,
                    title="Test and Verify",
                    description="Ensure the fix doesn't break functionality and the vulnerability is resolved",
                )
            ],
            owasp_mapping=self.OWASP_MAPPING.get(category),
            cwe_mapping=self.CWE_MAPPING.get(category),
            priority=self._calculate_priority(severity)
        )
    
    def _calculate_priority(self, severity: SeverityLevel) -> int:
        """Calculate priority based on severity."""
        priority_map = {
            SeverityLevel.CRITICAL: 1,
            SeverityLevel.HIGH: 2,
            SeverityLevel.MEDIUM: 3,
            SeverityLevel.LOW: 4,
            SeverityLevel.INFO: 5
        }
        return priority_map.get(severity, 3)
    
    def generate_batch_plans(
        self,
        vulnerabilities: List[Dict[str, Any]]
    ) -> List[MitigationPlan]:
        """Generate mitigation plans for multiple vulnerabilities."""
        plans = []
        
        for vuln in vulnerabilities:
            category = VulnerabilityCategory(vuln.get("category", "misconfig"))
            severity = SeverityLevel(vuln.get("severity", "medium"))
            context = vuln.get("context", {})
            
            plan = self.generate_plan(category, severity, context)
            plans.append(plan)
        
        # Sort by priority
        plans.sort(key=lambda p: p.priority)
        
        return plans
    
    def get_quick_fix(
        self,
        category: VulnerabilityCategory,
        language: str = "python"
    ) -> Optional[str]:
        """Get a quick fix code example for a vulnerability."""
        template = self._mitigation_templates.get(category)
        
        if template and template["steps"]:
            first_step = template["steps"][0]
            return first_step.get(f"{language}_example") or first_step.get("python_example")
        
        return None
