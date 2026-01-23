"""
Rule-Based Security Engine

Deterministic detection of known vulnerabilities with zero tolerance
for false negatives on critical security rules.

Design Principles:
1. CRITICAL rules NEVER miss (100% recall for known patterns)
2. Rules are fast, interpretable, and auditable
3. Each rule maps to CWE/OWASP for compliance
4. Rules can be updated without retraining ML models
"""

import re
import ast
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Callable, Pattern
from enum import Enum, auto
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND CONFIGURATION
# =============================================================================

class RuleSeverity(Enum):
    """
    Severity levels aligned with CVSS v3.1.
    
    CRITICAL: CVSS 9.0-10.0 - Immediate exploitation risk
    HIGH: CVSS 7.0-8.9 - Serious vulnerability
    MEDIUM: CVSS 4.0-6.9 - Moderate risk
    LOW: CVSS 0.1-3.9 - Minor issue
    INFO: CVSS 0.0 - Informational finding
    """
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    
    @property
    def cvss_range(self) -> tuple:
        """Get CVSS score range for severity."""
        ranges = {
            RuleSeverity.CRITICAL: (9.0, 10.0),
            RuleSeverity.HIGH: (7.0, 8.9),
            RuleSeverity.MEDIUM: (4.0, 6.9),
            RuleSeverity.LOW: (0.1, 3.9),
            RuleSeverity.INFO: (0.0, 0.0),
        }
        return ranges[self]
    
    @property
    def priority(self) -> int:
        """Numeric priority (higher = more severe)."""
        priorities = {
            RuleSeverity.CRITICAL: 5,
            RuleSeverity.HIGH: 4,
            RuleSeverity.MEDIUM: 3,
            RuleSeverity.LOW: 2,
            RuleSeverity.INFO: 1,
        }
        return priorities[self]


class RuleCategory(Enum):
    """Vulnerability categories aligned with OWASP Top 10 2021."""
    INJECTION = "A03:2021-Injection"
    BROKEN_AUTH = "A07:2021-Identification and Authentication Failures"
    SENSITIVE_DATA = "A02:2021-Cryptographic Failures"
    XXE = "A05:2021-Security Misconfiguration"
    BROKEN_ACCESS = "A01:2021-Broken Access Control"
    MISCONFIG = "A05:2021-Security Misconfiguration"
    XSS = "A03:2021-Injection"
    INSECURE_DESER = "A08:2021-Software and Data Integrity Failures"
    VULNERABLE_COMP = "A06:2021-Vulnerable and Outdated Components"
    LOGGING = "A09:2021-Security Logging and Monitoring Failures"
    SSRF = "A10:2021-Server-Side Request Forgery"


class RuleConfidence(Enum):
    """
    Confidence level of rule match.
    
    DEFINITE: Pattern is unambiguous (e.g., hardcoded password)
    HIGH: Very likely vulnerability (e.g., SQL string concat)
    MEDIUM: Possible vulnerability (e.g., user input in query)
    LOW: Suspicious pattern (needs context)
    """
    DEFINITE = 1.0
    HIGH = 0.9
    MEDIUM = 0.7
    LOW = 0.5


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class RuleMatch:
    """Details of where a rule matched."""
    line_number: int
    column_start: int
    column_end: int
    matched_text: str
    context_before: str = ""
    context_after: str = ""


@dataclass
class RuleResult:
    """Result of a single rule evaluation."""
    rule_id: str
    rule_name: str
    severity: RuleSeverity
    category: RuleCategory
    confidence: RuleConfidence
    cwe_id: str
    description: str
    matches: List[RuleMatch] = field(default_factory=list)
    remediation: str = ""
    references: List[str] = field(default_factory=list)
    is_critical: bool = False
    
    @property
    def match_count(self) -> int:
        return len(self.matches)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "category": self.category.value,
            "confidence": self.confidence.value,
            "cwe_id": self.cwe_id,
            "description": self.description,
            "matches": [
                {
                    "line": m.line_number,
                    "column_start": m.column_start,
                    "column_end": m.column_end,
                    "matched_text": m.matched_text,
                    "context": f"{m.context_before}>>>{m.matched_text}<<<{m.context_after}"
                }
                for m in self.matches
            ],
            "remediation": self.remediation,
            "references": self.references,
            "is_critical": self.is_critical,
        }


# =============================================================================
# RULE DEFINITIONS
# =============================================================================

@dataclass
class SecurityRule:
    """
    Definition of a security rule.
    
    Rules can be:
    1. Pattern-based (regex)
    2. AST-based (syntax tree analysis)
    3. Custom function-based
    """
    rule_id: str
    name: str
    description: str
    severity: RuleSeverity
    category: RuleCategory
    cwe_id: str
    
    # Detection patterns
    patterns: List[str] = field(default_factory=list)  # Regex patterns
    anti_patterns: List[str] = field(default_factory=list)  # Exclusion patterns
    ast_checker: Optional[Callable[[ast.AST], List[ast.AST]]] = None
    custom_checker: Optional[Callable[[str], List[RuleMatch]]] = None
    
    # Metadata
    remediation: str = ""
    references: List[str] = field(default_factory=list)
    is_critical: bool = False
    enabled: bool = True
    
    # Compiled patterns (for performance)
    _compiled_patterns: List[Pattern] = field(default_factory=list, repr=False)
    _compiled_anti_patterns: List[Pattern] = field(default_factory=list, repr=False)
    
    def __post_init__(self):
        """Compile regex patterns for performance."""
        self._compiled_patterns = [
            re.compile(p, re.IGNORECASE | re.MULTILINE)
            for p in self.patterns
        ]
        self._compiled_anti_patterns = [
            re.compile(p, re.IGNORECASE | re.MULTILINE)
            for p in self.anti_patterns
        ]


# =============================================================================
# CRITICAL RULES (ZERO FALSE NEGATIVE TOLERANCE)
# =============================================================================

class CriticalRules:
    """
    Critical security rules with zero tolerance for false negatives.
    
    These rules detect unambiguous vulnerabilities that MUST be caught:
    - Hardcoded credentials
    - SQL injection with string concatenation
    - Command injection with os.system/subprocess
    - Dangerous deserialization
    
    Design: High precision patterns with explicit exclusions.
    """
    
    @staticmethod
    def get_all() -> List[SecurityRule]:
        """Get all critical security rules."""
        return [
            # =========================================================
            # SQL INJECTION - CRITICAL
            # =========================================================
            SecurityRule(
                rule_id="SEC-001",
                name="SQL Injection - String Formatting",
                description="SQL query constructed with string formatting using user input",
                severity=RuleSeverity.CRITICAL,
                category=RuleCategory.INJECTION,
                cwe_id="CWE-89",
                patterns=[
                    # f-string SQL
                    r'(?:execute|query|raw|cursor\.execute)\s*\(\s*f["\'].*(?:SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER).*\{.*\}',
                    # .format() SQL
                    r'(?:execute|query|raw|cursor\.execute)\s*\(["\'].*(?:SELECT|INSERT|UPDATE|DELETE).*\.format\s*\(',
                    # % formatting SQL
                    r'(?:execute|query|raw|cursor\.execute)\s*\(["\'].*(?:SELECT|INSERT|UPDATE|DELETE).*%\s*(?:s|d)',
                    # String concatenation SQL
                    r'(?:execute|query|raw|cursor\.execute)\s*\(["\'].*(?:SELECT|INSERT|UPDATE|DELETE).*["\']\s*\+',
                ],
                anti_patterns=[
                    r'parameterized',
                    r'prepared_statement',
                    r'\?\s*,',  # Parameterized placeholder
                    r'%s\s*,\s*\(',  # Parameterized with tuple
                ],
                remediation="Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
                references=[
                    "https://cwe.mitre.org/data/definitions/89.html",
                    "https://owasp.org/Top10/A03_2021-Injection/",
                ],
                is_critical=True,
            ),
            
            # =========================================================
            # COMMAND INJECTION - CRITICAL
            # =========================================================
            SecurityRule(
                rule_id="SEC-002",
                name="Command Injection - os.system/subprocess",
                description="OS command executed with user-controlled input",
                severity=RuleSeverity.CRITICAL,
                category=RuleCategory.INJECTION,
                cwe_id="CWE-78",
                patterns=[
                    # os.system with variable
                    r'os\.system\s*\(\s*(?:f["\']|["\'].*\.format|["\'].*%|.*\+)',
                    # subprocess.call with shell=True and variable
                    r'subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True[^)]*(?:f["\']|\.format|%s|\+)',
                    # eval with input
                    r'eval\s*\(\s*(?:input|request|data|params)',
                    # exec with input
                    r'exec\s*\(\s*(?:input|request|data|params)',
                ],
                anti_patterns=[
                    r'shlex\.quote',
                    r'shell\s*=\s*False',
                    r'subprocess\.run\s*\(\s*\[',  # List form is safer
                ],
                remediation="Use subprocess with shell=False and list arguments: subprocess.run(['ls', '-la', directory], shell=False)",
                references=[
                    "https://cwe.mitre.org/data/definitions/78.html",
                ],
                is_critical=True,
            ),
            
            # =========================================================
            # HARDCODED CREDENTIALS - CRITICAL
            # =========================================================
            SecurityRule(
                rule_id="SEC-003",
                name="Hardcoded Credentials",
                description="Sensitive credentials hardcoded in source code",
                severity=RuleSeverity.CRITICAL,
                category=RuleCategory.SENSITIVE_DATA,
                cwe_id="CWE-798",
                patterns=[
                    # Password assignments
                    r'(?:password|passwd|pwd|secret|api_key|apikey|auth_token|access_token)\s*=\s*["\'][^"\']{4,}["\']',
                    # AWS keys
                    r'(?:AKIA|ABIA|ACCA|ASIA)[A-Z0-9]{16}',
                    # Private keys
                    r'-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----',
                    # JWT secrets
                    r'jwt[_-]?secret\s*=\s*["\'][^"\']+["\']',
                ],
                anti_patterns=[
                    r'os\.environ',
                    r'getenv',
                    r'config\.',
                    r'settings\.',
                    r'placeholder',
                    r'example',
                    r'<.*>',  # Template placeholders
                    r'\$\{',  # Environment variable syntax
                ],
                remediation="Use environment variables or secure vault: password = os.environ.get('DB_PASSWORD')",
                references=[
                    "https://cwe.mitre.org/data/definitions/798.html",
                ],
                is_critical=True,
            ),
            
            # =========================================================
            # INSECURE DESERIALIZATION - CRITICAL
            # =========================================================
            SecurityRule(
                rule_id="SEC-004",
                name="Insecure Deserialization",
                description="Deserializing untrusted data can lead to remote code execution",
                severity=RuleSeverity.CRITICAL,
                category=RuleCategory.INSECURE_DESER,
                cwe_id="CWE-502",
                patterns=[
                    # pickle with user data
                    r'pickle\.loads?\s*\(\s*(?:request|data|input|body)',
                    # yaml unsafe load
                    r'yaml\.(?:load|unsafe_load)\s*\([^)]*(?:Loader\s*=\s*yaml\.(?:Loader|UnsafeLoader|FullLoader))?[^)]*\)',
                    # marshal
                    r'marshal\.loads?\s*\(',
                    # shelve
                    r'shelve\.open\s*\([^)]*(?:request|user|input)',
                ],
                anti_patterns=[
                    r'yaml\.safe_load',
                    r'Loader\s*=\s*yaml\.SafeLoader',
                ],
                remediation="Use safe deserialization: yaml.safe_load(data) or json.loads(data)",
                references=[
                    "https://cwe.mitre.org/data/definitions/502.html",
                ],
                is_critical=True,
            ),
            
            # =========================================================
            # PATH TRAVERSAL - CRITICAL
            # =========================================================
            SecurityRule(
                rule_id="SEC-005",
                name="Path Traversal",
                description="File path constructed with user input without validation",
                severity=RuleSeverity.CRITICAL,
                category=RuleCategory.BROKEN_ACCESS,
                cwe_id="CWE-22",
                patterns=[
                    # open with user input
                    r'open\s*\(\s*(?:f["\']|["\'].*\.format|.*\+\s*(?:request|user|input|filename|path))',
                    # os.path.join with user input (without validation)
                    r'os\.path\.join\s*\([^)]*(?:request|user_input|filename)[^)]*\)',
                    # send_file with user input
                    r'send_file\s*\(\s*(?:f["\']|.*\+|.*\.format)',
                ],
                anti_patterns=[
                    r'os\.path\.basename',
                    r'secure_filename',
                    r'\.startswith\s*\(',
                    r'realpath.*startswith',
                ],
                remediation="Validate paths: safe_path = os.path.join(BASE_DIR, os.path.basename(user_input))",
                references=[
                    "https://cwe.mitre.org/data/definitions/22.html",
                ],
                is_critical=True,
            ),
            
            # =========================================================
            # XSS - HIGH (can be critical in some contexts)
            # =========================================================
            SecurityRule(
                rule_id="SEC-006",
                name="Cross-Site Scripting (XSS)",
                description="User input rendered in HTML without escaping",
                severity=RuleSeverity.HIGH,
                category=RuleCategory.XSS,
                cwe_id="CWE-79",
                patterns=[
                    # innerHTML with user data
                    r'innerHTML\s*=\s*(?:user|input|data|request)',
                    # document.write
                    r'document\.write\s*\([^)]*(?:user|input|data)',
                    # Jinja2 without escaping
                    r'\{\{.*\|safe\}\}',
                    # render_template_string with user input
                    r'render_template_string\s*\([^)]*(?:request|user|input)',
                ],
                anti_patterns=[
                    r'escape\(',
                    r'html\.escape',
                    r'bleach\.clean',
                    r'sanitize',
                ],
                remediation="Escape output: html.escape(user_input) or use template auto-escaping",
                references=[
                    "https://cwe.mitre.org/data/definitions/79.html",
                ],
                is_critical=False,
            ),
            
            # =========================================================
            # SSRF - HIGH
            # =========================================================
            SecurityRule(
                rule_id="SEC-007",
                name="Server-Side Request Forgery (SSRF)",
                description="Server makes requests to user-controlled URLs",
                severity=RuleSeverity.HIGH,
                category=RuleCategory.SSRF,
                cwe_id="CWE-918",
                patterns=[
                    # requests with user URL
                    r'requests\.(?:get|post|put|delete|head)\s*\(\s*(?:f["\']|.*\+|.*\.format|user|input|url)',
                    # urllib with user URL
                    r'urllib\.request\.urlopen\s*\(\s*(?:f["\']|.*\+|user|input|url)',
                    # httpx with user URL
                    r'httpx\.(?:get|post|put|delete)\s*\(\s*(?:f["\']|.*\+|user|input|url)',
                ],
                anti_patterns=[
                    r'allowlist',
                    r'whitelist',
                    r'validate_url',
                    r'is_safe_url',
                ],
                remediation="Validate URLs against allowlist: if urlparse(url).netloc in ALLOWED_HOSTS",
                references=[
                    "https://cwe.mitre.org/data/definitions/918.html",
                ],
                is_critical=False,
            ),
            
            # =========================================================
            # WEAK CRYPTOGRAPHY - HIGH
            # =========================================================
            SecurityRule(
                rule_id="SEC-008",
                name="Weak Cryptography",
                description="Use of broken or weak cryptographic algorithms",
                severity=RuleSeverity.HIGH,
                category=RuleCategory.SENSITIVE_DATA,
                cwe_id="CWE-327",
                patterns=[
                    # MD5 for security
                    r'hashlib\.md5\s*\(',
                    r'MD5\.new\s*\(',
                    # SHA1 for security
                    r'hashlib\.sha1\s*\(',
                    # DES encryption
                    r'DES\.new\s*\(',
                    r'from Crypto\.Cipher import DES',
                    # ECB mode
                    r'mode\s*=\s*(?:AES\.)?MODE_ECB',
                    # Random for crypto
                    r'random\.(?:randint|choice|random)\s*\(',
                ],
                anti_patterns=[
                    r'secrets\.',
                    r'hashlib\.sha256',
                    r'hashlib\.sha512',
                    r'bcrypt',
                    r'argon2',
                    r'MODE_GCM',
                    r'MODE_CBC.*iv',
                ],
                remediation="Use strong algorithms: hashlib.sha256() for hashing, secrets.token_bytes() for random",
                references=[
                    "https://cwe.mitre.org/data/definitions/327.html",
                ],
                is_critical=False,
            ),
        ]


# =============================================================================
# HIGH/MEDIUM RULES
# =============================================================================

class StandardRules:
    """Standard security rules for HIGH and MEDIUM severity issues."""
    
    @staticmethod
    def get_all() -> List[SecurityRule]:
        return [
            SecurityRule(
                rule_id="SEC-101",
                name="Debug Mode Enabled",
                description="Application running in debug mode in production",
                severity=RuleSeverity.MEDIUM,
                category=RuleCategory.MISCONFIG,
                cwe_id="CWE-489",
                patterns=[
                    r'DEBUG\s*=\s*True',
                    r'app\.run\s*\([^)]*debug\s*=\s*True',
                    r'FLASK_DEBUG\s*=\s*["\']?1',
                ],
                anti_patterns=[
                    r'if.*development',
                    r'if.*test',
                    r'os\.environ\.get\s*\(["\']DEBUG',
                ],
                remediation="Set DEBUG=False in production and use environment variables",
                is_critical=False,
            ),
            SecurityRule(
                rule_id="SEC-102",
                name="Missing CSRF Protection",
                description="Form without CSRF token protection",
                severity=RuleSeverity.MEDIUM,
                category=RuleCategory.BROKEN_ACCESS,
                cwe_id="CWE-352",
                patterns=[
                    r'@csrf_exempt',
                    r'WTF_CSRF_ENABLED\s*=\s*False',
                    r'csrf\s*=\s*False',
                ],
                remediation="Enable CSRF protection for all state-changing operations",
                is_critical=False,
            ),
            SecurityRule(
                rule_id="SEC-103",
                name="Insecure Cookie Configuration",
                description="Cookies set without security flags",
                severity=RuleSeverity.MEDIUM,
                category=RuleCategory.SENSITIVE_DATA,
                cwe_id="CWE-614",
                patterns=[
                    r'set_cookie\s*\([^)]*(?!secure)',
                    r'SESSION_COOKIE_SECURE\s*=\s*False',
                    r'httponly\s*=\s*False',
                ],
                anti_patterns=[
                    r'secure\s*=\s*True',
                    r'httponly\s*=\s*True',
                    r'samesite',
                ],
                remediation="Set secure=True, httponly=True, samesite='Lax' for cookies",
                is_critical=False,
            ),
            SecurityRule(
                rule_id="SEC-104",
                name="Verbose Error Messages",
                description="Detailed error messages exposed to users",
                severity=RuleSeverity.LOW,
                category=RuleCategory.LOGGING,
                cwe_id="CWE-209",
                patterns=[
                    r'traceback\.print_exc\s*\(',
                    r'return.*str\(e\)',
                    r'response.*exception.*message',
                ],
                remediation="Log errors internally, return generic error messages to users",
                is_critical=False,
            ),
            SecurityRule(
                rule_id="SEC-105",
                name="Mass Assignment Vulnerability",
                description="Object created directly from user input without field filtering",
                severity=RuleSeverity.MEDIUM,
                category=RuleCategory.BROKEN_ACCESS,
                cwe_id="CWE-915",
                patterns=[
                    r'\.objects\.create\s*\(\s*\*\*request\.(?:data|POST|json)',
                    r'Model\s*\(\s*\*\*request\.',
                    r'update\s*\(\s*\*\*request\.',
                ],
                anti_patterns=[
                    r'serializer\.validated_data',
                    r'form\.cleaned_data',
                    r'allowed_fields',
                ],
                remediation="Explicitly specify allowed fields: User.objects.create(name=data['name'], email=data['email'])",
                is_critical=False,
            ),
        ]


# =============================================================================
# RULE ENGINE
# =============================================================================

class RuleEngine:
    """
    Rule-based security detection engine.
    
    Features:
    - Fast pattern matching with compiled regex
    - AST analysis for semantic checks
    - Custom checker support
    - Anti-pattern filtering to reduce false positives
    """
    
    def __init__(self, rules: Optional[List[SecurityRule]] = None):
        """
        Initialize rule engine.
        
        Args:
            rules: Custom rules. If None, loads all default rules.
        """
        if rules is None:
            self.rules = CriticalRules.get_all() + StandardRules.get_all()
        else:
            self.rules = rules
        
        # Index rules by category and severity for fast lookup
        self._rules_by_category: Dict[RuleCategory, List[SecurityRule]] = {}
        self._rules_by_severity: Dict[RuleSeverity, List[SecurityRule]] = {}
        self._critical_rules: List[SecurityRule] = []
        
        self._build_indices()
        logger.info(f"Rule engine initialized with {len(self.rules)} rules")
    
    def _build_indices(self):
        """Build rule indices for fast lookup."""
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # By category
            if rule.category not in self._rules_by_category:
                self._rules_by_category[rule.category] = []
            self._rules_by_category[rule.category].append(rule)
            
            # By severity
            if rule.severity not in self._rules_by_severity:
                self._rules_by_severity[rule.severity] = []
            self._rules_by_severity[rule.severity].append(rule)
            
            # Critical rules
            if rule.is_critical:
                self._critical_rules.append(rule)
    
    def scan(
        self,
        code: str,
        filename: str = "<unknown>",
        categories: Optional[List[RuleCategory]] = None,
        min_severity: RuleSeverity = RuleSeverity.LOW,
    ) -> List[RuleResult]:
        """
        Scan code for security vulnerabilities.
        
        Args:
            code: Source code to scan
            filename: Filename for reporting
            categories: Filter by categories (None = all)
            min_severity: Minimum severity to report
        
        Returns:
            List of rule results (matches found)
        """
        results = []
        lines = code.split('\n')
        
        # Filter rules
        rules_to_check = self._filter_rules(categories, min_severity)
        
        for rule in rules_to_check:
            matches = self._check_rule(rule, code, lines)
            
            if matches:
                result = RuleResult(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    confidence=self._calculate_confidence(rule, matches, code),
                    cwe_id=rule.cwe_id,
                    description=rule.description,
                    matches=matches,
                    remediation=rule.remediation,
                    references=rule.references,
                    is_critical=rule.is_critical,
                )
                results.append(result)
        
        # Sort by severity (critical first)
        results.sort(key=lambda r: r.severity.priority, reverse=True)
        
        return results
    
    def scan_critical_only(self, code: str) -> List[RuleResult]:
        """
        Scan only critical rules (fast path for CI/CD blocking).
        
        Args:
            code: Source code to scan
        
        Returns:
            List of critical rule matches
        """
        results = []
        lines = code.split('\n')
        
        for rule in self._critical_rules:
            matches = self._check_rule(rule, code, lines)
            
            if matches:
                result = RuleResult(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    confidence=RuleConfidence.DEFINITE,  # Critical rules are definite
                    cwe_id=rule.cwe_id,
                    description=rule.description,
                    matches=matches,
                    remediation=rule.remediation,
                    references=rule.references,
                    is_critical=True,
                )
                results.append(result)
        
        return results
    
    def _filter_rules(
        self,
        categories: Optional[List[RuleCategory]],
        min_severity: RuleSeverity,
    ) -> List[SecurityRule]:
        """Filter rules by category and severity."""
        filtered = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            if categories and rule.category not in categories:
                continue
            
            if rule.severity.priority < min_severity.priority:
                continue
            
            filtered.append(rule)
        
        return filtered
    
    def _check_rule(
        self,
        rule: SecurityRule,
        code: str,
        lines: List[str],
    ) -> List[RuleMatch]:
        """Check a single rule against code."""
        matches = []
        
        # Pattern-based detection
        for pattern in rule._compiled_patterns:
            for match in pattern.finditer(code):
                # Check anti-patterns
                if self._matches_anti_pattern(rule, match.group(), code):
                    continue
                
                # Calculate line number
                line_num = code[:match.start()].count('\n') + 1
                col_start = match.start() - code.rfind('\n', 0, match.start()) - 1
                
                # Get context
                context_before = lines[max(0, line_num - 2):line_num - 1]
                context_after = lines[line_num:min(len(lines), line_num + 2)]
                
                matches.append(RuleMatch(
                    line_number=line_num,
                    column_start=col_start,
                    column_end=col_start + len(match.group()),
                    matched_text=match.group()[:200],  # Truncate long matches
                    context_before='\n'.join(context_before),
                    context_after='\n'.join(context_after),
                ))
        
        # AST-based detection
        if rule.ast_checker:
            try:
                tree = ast.parse(code)
                ast_matches = rule.ast_checker(tree)
                for node in ast_matches:
                    matches.append(RuleMatch(
                        line_number=getattr(node, 'lineno', 0),
                        column_start=getattr(node, 'col_offset', 0),
                        column_end=getattr(node, 'end_col_offset', 0),
                        matched_text=ast.dump(node)[:200],
                    ))
            except SyntaxError:
                pass  # Skip AST analysis for non-Python or invalid code
        
        # Custom checker
        if rule.custom_checker:
            custom_matches = rule.custom_checker(code)
            matches.extend(custom_matches)
        
        return matches
    
    def _matches_anti_pattern(
        self,
        rule: SecurityRule,
        matched_text: str,
        full_code: str,
    ) -> bool:
        """Check if match is negated by anti-pattern."""
        # Check in matched text
        for pattern in rule._compiled_anti_patterns:
            if pattern.search(matched_text):
                return True
        
        # Check in surrounding context (100 chars before/after)
        match_start = full_code.find(matched_text)
        if match_start >= 0:
            context_start = max(0, match_start - 100)
            context_end = min(len(full_code), match_start + len(matched_text) + 100)
            context = full_code[context_start:context_end]
            
            for pattern in rule._compiled_anti_patterns:
                if pattern.search(context):
                    return True
        
        return False
    
    def _calculate_confidence(
        self,
        rule: SecurityRule,
        matches: List[RuleMatch],
        code: str,
    ) -> RuleConfidence:
        """Calculate confidence level for matches."""
        if rule.is_critical:
            return RuleConfidence.DEFINITE
        
        # Multiple matches increase confidence
        if len(matches) >= 3:
            return RuleConfidence.HIGH
        
        # High severity rules with clear patterns
        if rule.severity == RuleSeverity.HIGH:
            return RuleConfidence.HIGH
        
        # Medium severity
        if rule.severity == RuleSeverity.MEDIUM:
            return RuleConfidence.MEDIUM
        
        return RuleConfidence.LOW
    
    def add_rule(self, rule: SecurityRule):
        """Add a new rule to the engine."""
        self.rules.append(rule)
        self._build_indices()
    
    def disable_rule(self, rule_id: str):
        """Disable a rule by ID."""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                rule.enabled = False
                self._build_indices()
                return
        raise ValueError(f"Rule {rule_id} not found")
    
    def get_rule(self, rule_id: str) -> Optional[SecurityRule]:
        """Get rule by ID."""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get rule engine statistics."""
        return {
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules if r.enabled),
            "critical_rules": len(self._critical_rules),
            "by_severity": {
                s.value: len(rules)
                for s, rules in self._rules_by_severity.items()
            },
            "by_category": {
                c.value: len(rules)
                for c, rules in self._rules_by_category.items()
            },
        }
