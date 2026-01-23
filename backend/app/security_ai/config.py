"""
Security AI Configuration

Environment-aware configuration supporting:
- Local development (TensorFlow)
- Huawei Cloud ModelArts (MindSpore ready)

All secrets loaded from environment variables - NEVER hardcoded.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from pathlib import Path


class ExecutionEnvironment(Enum):
    """Execution environment for the security AI system."""
    LOCAL = "local"
    HUAWEI_CLOUD = "huawei_cloud"
    DOCKER = "docker"


class MLFramework(Enum):
    """Supported ML frameworks."""
    TENSORFLOW = "tensorflow"
    PYTORCH = "pytorch"
    MINDSPORE = "mindspore"  # For Huawei Ascend NPU


class SeverityLevel(Enum):
    """Vulnerability severity classification levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityCategory(Enum):
    """Categories of security vulnerabilities."""
    INJECTION = "injection"  # SQL, Command, LDAP injection
    BROKEN_AUTH = "broken_authentication"
    SENSITIVE_DATA = "sensitive_data_exposure"
    XXE = "xml_external_entities"
    BROKEN_ACCESS = "broken_access_control"
    MISCONFIG = "security_misconfiguration"
    XSS = "cross_site_scripting"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    VULNERABLE_COMPONENTS = "vulnerable_components"
    INSUFFICIENT_LOGGING = "insufficient_logging"
    SSRF = "server_side_request_forgery"
    HARDCODED_SECRETS = "hardcoded_secrets"
    INSECURE_CRYPTO = "insecure_cryptography"
    PATH_TRAVERSAL = "path_traversal"
    RACE_CONDITION = "race_condition"


@dataclass
class ModelConfig:
    """ML Model configuration."""
    model_name: str
    version: str
    checkpoint_path: Optional[str] = None
    vocab_size: int = 50000
    embedding_dim: int = 256
    hidden_dim: int = 512
    num_layers: int = 6
    num_heads: int = 8
    dropout_rate: float = 0.1
    max_sequence_length: int = 2048
    batch_size: int = 32
    learning_rate: float = 1e-4


@dataclass
class InferenceConfig:
    """Inference configuration."""
    confidence_threshold: float = 0.7
    min_confidence_for_critical: float = 0.85
    max_findings_per_file: int = 100
    enable_explainability: bool = True
    timeout_seconds: int = 30
    use_gpu: bool = True
    gpu_memory_fraction: float = 0.8


@dataclass
class HuaweiCloudConfig:
    """Huawei Cloud ModelArts configuration (Phase 2)."""
    # All sensitive values from environment
    region: str = field(default_factory=lambda: os.getenv("HUAWEI_REGION", "cn-north-4"))
    project_id: str = field(default_factory=lambda: os.getenv("HUAWEI_PROJECT_ID", ""))
    access_key: str = field(default_factory=lambda: os.getenv("HUAWEI_ACCESS_KEY", ""))  # From env only
    secret_key: str = field(default_factory=lambda: os.getenv("HUAWEI_SECRET_KEY", ""))  # From env only
    obs_bucket: str = field(default_factory=lambda: os.getenv("HUAWEI_OBS_BUCKET", ""))
    modelarts_endpoint: str = field(default_factory=lambda: os.getenv("HUAWEI_MODELARTS_ENDPOINT", ""))
    
    # Ascend NPU configuration
    use_ascend_npu: bool = True
    npu_device_id: int = 0
    
    # Model deployment
    model_id: Optional[str] = None
    service_id: Optional[str] = None
    
    def validate(self) -> bool:
        """Validate cloud configuration."""
        required = [self.project_id, self.access_key, self.secret_key, self.obs_bucket]
        return all(required)


@dataclass
class SecurityAIConfig:
    """
    Main configuration for the Security AI system.
    
    Usage:
        config = SecurityAIConfig.from_environment()
        config = SecurityAIConfig.for_local_development()
        config = SecurityAIConfig.for_huawei_cloud()
    """
    
    environment: ExecutionEnvironment = ExecutionEnvironment.LOCAL
    framework: MLFramework = MLFramework.TENSORFLOW
    
    # Paths
    base_path: Path = field(default_factory=lambda: Path(__file__).parent)
    models_path: Path = field(default_factory=lambda: Path(__file__).parent / "trained_models")
    datasets_path: Path = field(default_factory=lambda: Path(__file__).parent / "datasets")
    logs_path: Path = field(default_factory=lambda: Path(__file__).parent / "logs")
    
    # Model configurations
    vulnerability_detector: ModelConfig = field(default_factory=lambda: ModelConfig(
        model_name="vulnerability_detector",
        version="1.0.0"
    ))
    
    severity_classifier: ModelConfig = field(default_factory=lambda: ModelConfig(
        model_name="severity_classifier",
        version="1.0.0",
        hidden_dim=256,
        num_layers=4
    ))
    
    # Inference settings
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    
    # Huawei Cloud settings (Phase 2)
    huawei_cloud: HuaweiCloudConfig = field(default_factory=HuaweiCloudConfig)
    
    # Supported languages for code analysis
    supported_languages: List[str] = field(default_factory=lambda: [
        "python", "javascript", "typescript", "java", "go", "rust", "c", "cpp"
    ])
    
    # Security scanning rules
    enabled_vulnerability_categories: List[VulnerabilityCategory] = field(
        default_factory=lambda: list(VulnerabilityCategory)
    )
    
    def __post_init__(self):
        """Initialize paths and validate configuration."""
        self.models_path.mkdir(parents=True, exist_ok=True)
        self.datasets_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_environment(cls) -> "SecurityAIConfig":
        """Create configuration from environment variables."""
        env = os.getenv("SECURITY_AI_ENV", "local")
        
        if env == "huawei_cloud":
            return cls.for_huawei_cloud()
        elif env == "docker":
            return cls.for_docker()
        else:
            return cls.for_local_development()
    
    @classmethod
    def for_local_development(cls) -> "SecurityAIConfig":
        """Configuration optimized for local development."""
        return cls(
            environment=ExecutionEnvironment.LOCAL,
            framework=MLFramework.TENSORFLOW,
            inference=InferenceConfig(
                use_gpu=False,  # CPU for local dev
                confidence_threshold=0.6,
                enable_explainability=True
            )
        )
    
    @classmethod
    def for_huawei_cloud(cls) -> "SecurityAIConfig":
        """Configuration for Huawei Cloud ModelArts deployment."""
        return cls(
            environment=ExecutionEnvironment.HUAWEI_CLOUD,
            framework=MLFramework.MINDSPORE,  # Optimized for Ascend NPU
            inference=InferenceConfig(
                use_gpu=True,
                confidence_threshold=0.7,
                enable_explainability=True,
                gpu_memory_fraction=0.9
            ),
            huawei_cloud=HuaweiCloudConfig(
                use_ascend_npu=True
            )
        )
    
    @classmethod
    def for_docker(cls) -> "SecurityAIConfig":
        """Configuration for containerized deployment."""
        return cls(
            environment=ExecutionEnvironment.DOCKER,
            framework=MLFramework.TENSORFLOW,
            inference=InferenceConfig(
                use_gpu=os.getenv("USE_GPU", "false").lower() == "true",
                confidence_threshold=0.7
            )
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (for serialization)."""
        return {
            "environment": self.environment.value,
            "framework": self.framework.value,
            "models_path": str(self.models_path),
            "inference": {
                "confidence_threshold": self.inference.confidence_threshold,
                "enable_explainability": self.inference.enable_explainability,
                "use_gpu": self.inference.use_gpu
            },
            "supported_languages": self.supported_languages,
            "enabled_categories": [c.value for c in self.enabled_vulnerability_categories]
        }


# Global configuration instance
_config: Optional[SecurityAIConfig] = None


def get_config() -> SecurityAIConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = SecurityAIConfig.from_environment()
    return _config


def set_config(config: SecurityAIConfig) -> None:
    """Set global configuration instance."""
    global _config
    _config = config
