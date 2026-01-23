"""
Sample Dataset Generator

Creates example vulnerability samples for testing and demonstration.
"""

from typing import List
from datetime import datetime

from .schema import (
    DatasetSample,
    LabelTaxonomy,
    SeverityEncoding,
    CodeLocation,
    VulnerabilityDomain,
    CWECategory,
    OWASPCategory,
    SeverityLevel,
    SampleType,
    AnalysisContext,
)


def create_sample_dataset() -> List[DatasetSample]:
    """
    Create a collection of sample vulnerability examples.
    
    Returns:
        List of DatasetSample objects covering various vulnerability types
    """
    samples = []
    
    # =========================================================================
    # SQL INJECTION SAMPLES
    # =========================================================================
    
    samples.append(DatasetSample(
        sample_id="sql_injection_001",
        sample_type=SampleType.SOURCE_CODE,
        language="python",
        content='''def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.SOURCE_CODE,
            cwe_ids=[CWECategory.CWE_89],
            owasp_categories=[OWASPCategory.A03_INJECTION],
            severity=SeverityEncoding.critical(),
            is_vulnerable=True,
            vulnerability_subtype="sql_injection_string_format"
        ),
        context=AnalysisContext.WEB_APPLICATION,
        location=CodeLocation(
            file_path="app/database.py",
            start_line=10,
            end_line=13,
            function_name="get_user"
        ),
        framework="fastapi",
        source="manual",
        tags=["injection", "sql", "critical", "easy_fix"],
        notes="Classic f-string SQL injection. Fix with parameterized query."
    ))
    
    samples.append(DatasetSample(
        sample_id="sql_injection_002",
        sample_type=SampleType.SOURCE_CODE,
        language="python",
        content='''def search_products(name):
    query = "SELECT * FROM products WHERE name LIKE '%" + name + "%'"
    return db.execute(query).fetchall()''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.SOURCE_CODE,
            cwe_ids=[CWECategory.CWE_89],
            owasp_categories=[OWASPCategory.A03_INJECTION],
            severity=SeverityEncoding.critical(),
            is_vulnerable=True,
            vulnerability_subtype="sql_injection_concatenation"
        ),
        context=AnalysisContext.WEB_APPLICATION,
        framework="flask",
        source="manual",
        tags=["injection", "sql", "critical"]
    ))
    
    # Safe SQL example
    samples.append(DatasetSample(
        sample_id="sql_safe_001",
        sample_type=SampleType.SOURCE_CODE,
        language="python",
        content='''def get_user(user_id: int):
    query = "SELECT * FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))
    return cursor.fetchone()''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.SOURCE_CODE,
            cwe_ids=[],
            owasp_categories=[],
            severity=SeverityEncoding(
                level=SeverityLevel.INFO,
                cvss_score=0.0,
                exploitability=0.0,
                impact=0.0,
                confidence=0.95
            ),
            is_vulnerable=False
        ),
        context=AnalysisContext.WEB_APPLICATION,
        source="manual",
        tags=["safe", "parameterized_query"]
    ))
    
    # =========================================================================
    # HARDCODED SECRETS
    # =========================================================================
    
    samples.append(DatasetSample(
        sample_id="hardcoded_secret_001",
        sample_type=SampleType.SOURCE_CODE,
        language="python",
        content='''# Configuration
API_KEY = "sk-1234567890abcdef1234567890abcdef"
AWS_SECRET = "AKIAIOSFODNN7EXAMPLE"

def call_api():
    return requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.AUTHENTICATION,
            cwe_ids=[CWECategory.CWE_798],
            owasp_categories=[OWASPCategory.A07_AUTH_FAILURES],
            severity=SeverityEncoding.critical(confidence=0.95),
            is_vulnerable=True,
            vulnerability_subtype="hardcoded_api_key"
        ),
        context=AnalysisContext.WEB_APPLICATION,
        source="manual",
        tags=["secrets", "api_key", "aws", "critical"]
    ))
    
    samples.append(DatasetSample(
        sample_id="hardcoded_secret_002",
        sample_type=SampleType.SOURCE_CODE,
        language="javascript",
        content='''const config = {
    database: {
        host: "localhost",
        user: "admin",
        password: "SuperSecret123!",
        database: "production_db"
    }
};''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.AUTHENTICATION,
            cwe_ids=[CWECategory.CWE_798, CWECategory.CWE_312],
            owasp_categories=[OWASPCategory.A07_AUTH_FAILURES, OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES],
            severity=SeverityEncoding.critical(),
            is_vulnerable=True,
            vulnerability_subtype="hardcoded_password"
        ),
        context=AnalysisContext.WEB_APPLICATION,
        framework="express",
        source="manual",
        tags=["secrets", "password", "database"]
    ))
    
    # =========================================================================
    # BROKEN AUTHENTICATION
    # =========================================================================
    
    samples.append(DatasetSample(
        sample_id="broken_auth_001",
        sample_type=SampleType.SOURCE_CODE,
        language="python",
        content='''def verify_password(stored_password, input_password):
    # Insecure: timing attack vulnerable comparison
    return stored_password == input_password''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.AUTHENTICATION,
            cwe_ids=[CWECategory.CWE_287],
            owasp_categories=[OWASPCategory.A07_AUTH_FAILURES],
            severity=SeverityEncoding.high(),
            is_vulnerable=True,
            vulnerability_subtype="timing_attack"
        ),
        context=AnalysisContext.AUTHENTICATION_SERVICE,
        source="manual",
        tags=["auth", "timing_attack", "password"]
    ))
    
    samples.append(DatasetSample(
        sample_id="broken_auth_002",
        sample_type=SampleType.SOURCE_CODE,
        language="python",
        content='''import jwt

def create_token(user_id):
    # Insecure: using 'none' algorithm
    return jwt.encode({"user_id": user_id}, "", algorithm="none")''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.AUTHENTICATION,
            cwe_ids=[CWECategory.CWE_287, CWECategory.CWE_327],
            owasp_categories=[OWASPCategory.A07_AUTH_FAILURES, OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES],
            severity=SeverityEncoding.critical(),
            is_vulnerable=True,
            vulnerability_subtype="jwt_none_algorithm"
        ),
        context=AnalysisContext.AUTHENTICATION_SERVICE,
        source="manual",
        tags=["auth", "jwt", "critical"]
    ))
    
    # =========================================================================
    # XSS VULNERABILITIES
    # =========================================================================
    
    samples.append(DatasetSample(
        sample_id="xss_001",
        sample_type=SampleType.SOURCE_CODE,
        language="javascript",
        content='''function displayUserContent(userInput) {
    document.getElementById("content").innerHTML = userInput;
}''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.SOURCE_CODE,
            cwe_ids=[CWECategory.CWE_79],
            owasp_categories=[OWASPCategory.A03_INJECTION],
            severity=SeverityEncoding.high(),
            is_vulnerable=True,
            vulnerability_subtype="dom_xss"
        ),
        context=AnalysisContext.WEB_APPLICATION,
        source="manual",
        tags=["xss", "dom", "javascript"]
    ))
    
    samples.append(DatasetSample(
        sample_id="xss_002",
        sample_type=SampleType.SOURCE_CODE,
        language="python",
        content='''@app.route("/greet")
def greet():
    name = request.args.get("name", "")
    return f"<h1>Hello, {name}!</h1>"''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.SOURCE_CODE,
            cwe_ids=[CWECategory.CWE_79],
            owasp_categories=[OWASPCategory.A03_INJECTION],
            severity=SeverityEncoding.medium(),
            is_vulnerable=True,
            vulnerability_subtype="reflected_xss"
        ),
        context=AnalysisContext.WEB_APPLICATION,
        framework="flask",
        source="manual",
        tags=["xss", "reflected", "flask"]
    ))
    
    # =========================================================================
    # PATH TRAVERSAL
    # =========================================================================
    
    samples.append(DatasetSample(
        sample_id="path_traversal_001",
        sample_type=SampleType.SOURCE_CODE,
        language="python",
        content='''@app.route("/download")
def download_file():
    filename = request.args.get("file")
    return send_file(f"/uploads/{filename}")''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.SOURCE_CODE,
            cwe_ids=[CWECategory.CWE_22],
            owasp_categories=[OWASPCategory.A01_BROKEN_ACCESS_CONTROL],
            severity=SeverityEncoding.high(),
            is_vulnerable=True,
            vulnerability_subtype="lfi"
        ),
        context=AnalysisContext.WEB_APPLICATION,
        framework="flask",
        source="manual",
        tags=["path_traversal", "lfi", "file_access"]
    ))
    
    # =========================================================================
    # INSECURE DESERIALIZATION
    # =========================================================================
    
    samples.append(DatasetSample(
        sample_id="deserialization_001",
        sample_type=SampleType.SOURCE_CODE,
        language="python",
        content='''import pickle

def load_user_data(data):
    # Dangerous: deserializing untrusted data
    return pickle.loads(data)''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.SOURCE_CODE,
            cwe_ids=[CWECategory.CWE_502],
            owasp_categories=[OWASPCategory.A08_DATA_INTEGRITY_FAILURES],
            severity=SeverityEncoding.critical(),
            is_vulnerable=True,
            vulnerability_subtype="pickle_deserialization"
        ),
        context=AnalysisContext.WEB_APPLICATION,
        source="manual",
        tags=["deserialization", "pickle", "rce"]
    ))
    
    samples.append(DatasetSample(
        sample_id="deserialization_002",
        sample_type=SampleType.SOURCE_CODE,
        language="python",
        content='''import yaml

def parse_config(config_string):
    # Dangerous: yaml.load without safe_load
    return yaml.load(config_string)''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.SOURCE_CODE,
            cwe_ids=[CWECategory.CWE_502],
            owasp_categories=[OWASPCategory.A08_DATA_INTEGRITY_FAILURES],
            severity=SeverityEncoding.high(),
            is_vulnerable=True,
            vulnerability_subtype="yaml_deserialization"
        ),
        context=AnalysisContext.WEB_APPLICATION,
        source="manual",
        tags=["deserialization", "yaml"]
    ))
    
    # =========================================================================
    # SSRF
    # =========================================================================
    
    samples.append(DatasetSample(
        sample_id="ssrf_001",
        sample_type=SampleType.SOURCE_CODE,
        language="python",
        content='''@app.route("/fetch")
def fetch_url():
    url = request.args.get("url")
    response = requests.get(url)
    return response.text''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.SOURCE_CODE,
            cwe_ids=[CWECategory.CWE_918],
            owasp_categories=[OWASPCategory.A10_SSRF],
            severity=SeverityEncoding.high(),
            is_vulnerable=True,
            vulnerability_subtype="ssrf_unvalidated"
        ),
        context=AnalysisContext.WEB_APPLICATION,
        framework="flask",
        source="manual",
        tags=["ssrf", "network"]
    ))
    
    # =========================================================================
    # INSECURE CRYPTOGRAPHY
    # =========================================================================
    
    samples.append(DatasetSample(
        sample_id="weak_crypto_001",
        sample_type=SampleType.SOURCE_CODE,
        language="python",
        content='''import hashlib

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.DATA_PROTECTION,
            cwe_ids=[CWECategory.CWE_327, CWECategory.CWE_328],
            owasp_categories=[OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES],
            severity=SeverityEncoding.high(),
            is_vulnerable=True,
            vulnerability_subtype="weak_hash_md5"
        ),
        context=AnalysisContext.AUTHENTICATION_SERVICE,
        source="manual",
        tags=["crypto", "md5", "password"]
    ))
    
    samples.append(DatasetSample(
        sample_id="weak_crypto_002",
        sample_type=SampleType.SOURCE_CODE,
        language="python",
        content='''from Crypto.Cipher import DES

def encrypt_data(data, key):
    cipher = DES.new(key, DES.MODE_ECB)
    return cipher.encrypt(data)''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.DATA_PROTECTION,
            cwe_ids=[CWECategory.CWE_327],
            owasp_categories=[OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES],
            severity=SeverityEncoding.high(),
            is_vulnerable=True,
            vulnerability_subtype="weak_cipher_des"
        ),
        context=AnalysisContext.LIBRARY,
        source="manual",
        tags=["crypto", "des", "ecb"]
    ))
    
    # =========================================================================
    # CONFIGURATION SAMPLES
    # =========================================================================
    
    samples.append(DatasetSample(
        sample_id="config_001",
        sample_type=SampleType.CONFIG_FILE,
        language="yaml",
        content='''# Docker Compose configuration
version: "3"
services:
  web:
    image: myapp:latest
    environment:
      - DATABASE_PASSWORD=mysecretpassword
      - API_KEY=sk-1234567890
    ports:
      - "80:80"''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.CONFIGURATION,
            cwe_ids=[CWECategory.CWE_798, CWECategory.CWE_16],
            owasp_categories=[OWASPCategory.A05_SECURITY_MISCONFIGURATION, OWASPCategory.A07_AUTH_FAILURES],
            severity=SeverityEncoding.critical(),
            is_vulnerable=True,
            vulnerability_subtype="secrets_in_config"
        ),
        context=AnalysisContext.INFRASTRUCTURE,
        source="manual",
        tags=["config", "docker", "secrets"]
    ))
    
    samples.append(DatasetSample(
        sample_id="config_002",
        sample_type=SampleType.CONFIG_FILE,
        language="json",
        content='''{
  "cors": {
    "origin": "*",
    "methods": ["GET", "POST", "PUT", "DELETE"],
    "credentials": true
  }
}''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.CONFIGURATION,
            cwe_ids=[CWECategory.CWE_16],
            owasp_categories=[OWASPCategory.A05_SECURITY_MISCONFIGURATION],
            severity=SeverityEncoding.medium(),
            is_vulnerable=True,
            vulnerability_subtype="cors_misconfiguration"
        ),
        context=AnalysisContext.WEB_APPLICATION,
        source="manual",
        tags=["config", "cors", "misconfiguration"]
    ))
    
    # =========================================================================
    # API SECURITY SAMPLES
    # =========================================================================
    
    samples.append(DatasetSample(
        sample_id="api_001",
        sample_type=SampleType.API_ENDPOINT,
        language="python",
        content='''@app.route("/api/users/<user_id>", methods=["GET"])
def get_user(user_id):
    # Missing authentication check
    user = User.query.get(user_id)
    return jsonify(user.to_dict())''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.API_SECURITY,
            cwe_ids=[CWECategory.CWE_306],
            owasp_categories=[OWASPCategory.A01_BROKEN_ACCESS_CONTROL],
            severity=SeverityEncoding.high(),
            is_vulnerable=True,
            vulnerability_subtype="missing_authentication"
        ),
        context=AnalysisContext.WEB_APPLICATION,
        framework="flask",
        source="manual",
        tags=["api", "auth", "endpoint"]
    ))
    
    samples.append(DatasetSample(
        sample_id="api_002",
        sample_type=SampleType.API_ENDPOINT,
        language="python",
        content='''@app.route("/api/admin/users", methods=["DELETE"])
@login_required
def delete_all_users():
    # Missing authorization check - any logged in user can delete all users
    User.query.delete()
    db.session.commit()
    return jsonify({"status": "success"})''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.API_SECURITY,
            cwe_ids=[CWECategory.CWE_862],
            owasp_categories=[OWASPCategory.A01_BROKEN_ACCESS_CONTROL],
            severity=SeverityEncoding.critical(),
            is_vulnerable=True,
            vulnerability_subtype="missing_authorization"
        ),
        context=AnalysisContext.WEB_APPLICATION,
        framework="flask",
        source="manual",
        tags=["api", "authorization", "admin"]
    ))
    
    # =========================================================================
    # INSUFFICIENT LOGGING
    # =========================================================================
    
    samples.append(DatasetSample(
        sample_id="logging_001",
        sample_type=SampleType.SOURCE_CODE,
        language="python",
        content='''@app.route("/login", methods=["POST"])
def login():
    user = authenticate(request.form["username"], request.form["password"])
    if user:
        return create_session(user)
    else:
        # No logging of failed login attempts
        return jsonify({"error": "Invalid credentials"}), 401''',
        labels=LabelTaxonomy(
            domain=VulnerabilityDomain.SOURCE_CODE,
            cwe_ids=[CWECategory.CWE_778],
            owasp_categories=[OWASPCategory.A09_LOGGING_FAILURES],
            severity=SeverityEncoding.medium(),
            is_vulnerable=True,
            vulnerability_subtype="missing_security_logging"
        ),
        context=AnalysisContext.WEB_APPLICATION,
        framework="flask",
        source="manual",
        tags=["logging", "auth", "monitoring"]
    ))
    
    return samples


def generate_training_batch(count: int = 100) -> List[DatasetSample]:
    """
    Generate a larger batch of samples by creating variations.
    
    Args:
        count: Approximate number of samples to generate
    
    Returns:
        List of DatasetSample objects
    """
    base_samples = create_sample_dataset()
    
    # For demonstration, just return base samples
    # In production, this would generate variations
    samples = base_samples.copy()
    
    # Add variations (simplified)
    variations = []
    for sample in base_samples[:min(count - len(base_samples), len(base_samples))]:
        # Create a variation with slight modifications
        variation = DatasetSample(
            sample_id=f"{sample.sample_id}_var",
            sample_type=sample.sample_type,
            language=sample.language,
            content=sample.content,  # In production, would modify content
            labels=sample.labels,
            context=sample.context,
            location=sample.location,
            framework=sample.framework,
            source="synthetic",
            tags=sample.tags + ["synthetic"],
            notes=f"Variation of {sample.sample_id}"
        )
        variations.append(variation)
    
    return samples + variations
