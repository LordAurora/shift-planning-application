"""
Ascend NPU Optimization Guide

Reference configurations and best practices for optimizing
MindSpore models on Huawei Ascend NPU hardware.

Note: This module is DESIGN-ONLY documentation.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum


# =============================================================================
# ASCEND HARDWARE SPECIFICATIONS
# =============================================================================

class AscendModel(Enum):
    """Ascend NPU model variants."""
    ASCEND_910 = "ascend_910"    # Training (256 TFLOPS FP16)
    ASCEND_910B = "ascend_910b"  # Training (improved)
    ASCEND_310 = "ascend_310"    # Inference (22 TOPS INT8)
    ASCEND_310P = "ascend_310p"  # Inference (improved)


@dataclass
class AscendSpecs:
    """Hardware specifications for Ascend NPU."""
    model: AscendModel
    fp16_tflops: float
    int8_tops: float
    memory_gb: float
    bandwidth_tb_s: float
    power_watts: float
    use_case: str


ASCEND_HARDWARE = {
    AscendModel.ASCEND_910: AscendSpecs(
        model=AscendModel.ASCEND_910,
        fp16_tflops=256.0,
        int8_tops=512.0,
        memory_gb=32.0,
        bandwidth_tb_s=1.2,
        power_watts=310.0,
        use_case="Large-scale model training",
    ),
    AscendModel.ASCEND_310: AscendSpecs(
        model=AscendModel.ASCEND_310,
        fp16_tflops=8.0,
        int8_tops=22.0,
        memory_gb=8.0,
        bandwidth_tb_s=0.07,
        power_watts=8.0,
        use_case="Edge inference, low power deployment",
    ),
}


# =============================================================================
# CONTEXT CONFIGURATION
# =============================================================================

CONTEXT_CONFIG_TRAINING = """
# MindSpore Context Configuration for Ascend Training
# Apply at the start of your training script

from mindspore import context

context.set_context(
    # Execution mode
    mode=context.GRAPH_MODE,          # Static graph for optimization
    # mode=context.PYNATIVE_MODE,     # Dynamic graph for debugging
    
    # Target hardware
    device_target="Ascend",
    device_id=0,                      # NPU device index
    
    # Memory configuration
    max_device_memory="28GB",         # Reserve for model (leave 4GB for system)
    mempool_block_size="1GB",         # Memory pool granularity
    
    # Graph optimization
    enable_graph_kernel=True,         # Automatic kernel fusion
    graph_kernel_flags="--enable_cluster_ops=MatMul,Add,ReLU",
    
    # Debugging (disable in production)
    save_graphs=False,
    save_graphs_path="./graphs",
)

# Enable profiling for performance analysis
from mindspore import Profiler
profiler = Profiler(output_path="./profiler_data", profile_memory=True)
"""


CONTEXT_CONFIG_INFERENCE = """
# MindSpore Context Configuration for Ascend Inference
# Apply at the start of your inference service

from mindspore import context

context.set_context(
    mode=context.GRAPH_MODE,
    device_target="Ascend",
    device_id=0,
    
    # Inference optimizations
    max_device_memory="6GB",          # Smaller for inference
    
    # Graph optimization
    enable_graph_kernel=True,
    graph_kernel_flags="--enable_cluster_ops=MatMul,Add",
    
    # Deterministic for reproducibility
    deterministic="ON",
)
"""


# =============================================================================
# OPTIMIZATION TECHNIQUES
# =============================================================================

@dataclass
class OptimizationTechnique:
    """Description of an optimization technique."""
    name: str
    description: str
    speedup: str
    memory_impact: str
    code_example: str
    considerations: List[str]


OPTIMIZATION_TECHNIQUES = [
    OptimizationTechnique(
        name="Dataset Sink Mode",
        description="Keep data on NPU device, avoid host-device transfer per batch",
        speedup="10-30% faster training",
        memory_impact="Slightly higher NPU memory",
        code_example="""
model.train(
    epoch=100,
    train_dataset=dataset,
    dataset_sink_mode=True,      # Enable sink mode
    sink_size=100,               # Steps per sink (optional)
)
""",
        considerations=[
            "Not compatible with dynamic shapes",
            "Debugging is harder (data on device)",
            "Set sink_size for large datasets",
        ],
    ),
    
    OptimizationTechnique(
        name="Mixed Precision Training (AMP)",
        description="Use FP16 for compute, FP32 for master weights",
        speedup="1.5-2x faster, same accuracy",
        memory_impact="~50% less memory",
        code_example="""
from mindspore import amp

# Build network with mixed precision
model = amp.build_train_network(
    network,
    optimizer,
    loss_fn,
    level="O2",    # O1=conservative, O2=aggressive FP16
)
""",
        considerations=[
            "Watch for gradient underflow",
            "Use loss scaling for stability",
            "Some ops stay FP32 (softmax, batchnorm)",
        ],
    ),
    
    OptimizationTechnique(
        name="Operator Fusion",
        description="Automatically fuse compatible operators into single kernels",
        speedup="5-20% faster",
        memory_impact="Reduced intermediate tensors",
        code_example="""
context.set_context(
    enable_graph_kernel=True,
    graph_kernel_flags=(
        "--enable_cluster_ops=MatMul,Add,ReLU"
        "--enable_stitch_fusion=true"
    ),
)
""",
        considerations=[
            "Only works in GRAPH_MODE",
            "May increase compilation time",
            "Not all ops are fusible",
        ],
    ),
    
    OptimizationTechnique(
        name="Gradient Checkpointing",
        description="Recompute activations during backward pass to save memory",
        speedup="Slightly slower (recomputation)",
        memory_impact="2-4x less activation memory",
        code_example="""
from mindspore.rewrite import PatternEngine

# Enable checkpointing for memory-intensive models
PatternEngine.apply_checkpointing(
    network,
    segments=4,     # Split into 4 checkpointed segments
)
""",
        considerations=[
            "Trades compute for memory",
            "Essential for large models",
            "Tune segment count for balance",
        ],
    ),
    
    OptimizationTechnique(
        name="Distributed Training (Data Parallel)",
        description="Train across multiple NPUs with synchronized gradients",
        speedup="Near-linear scaling",
        memory_impact="Per-NPU memory unchanged",
        code_example="""
from mindspore.communication import init
from mindspore.parallel import set_algo_parameters

# Initialize distributed environment
init()
context.set_auto_parallel_context(
    parallel_mode="data_parallel",
    gradients_mean=True,
    device_num=8,
)

# Model automatically parallelized
model.train(...)
""",
        considerations=[
            "Requires HCCL (Huawei Collective Communication)",
            "Scale learning rate with device count",
            "Ensure batch size divisible by device count",
        ],
    ),
]


# =============================================================================
# PERFORMANCE TUNING CHECKLIST
# =============================================================================

PERFORMANCE_CHECKLIST = """
# Ascend NPU Performance Tuning Checklist

## 1. Context Configuration
☐ Use GRAPH_MODE for production
☐ Enable graph_kernel for operator fusion
☐ Set appropriate max_device_memory
☐ Configure mempool_block_size

## 2. Data Pipeline
☐ Use MindRecord format for large datasets
☐ Enable dataset_sink_mode
☐ Set num_parallel_workers appropriately
☐ Use drop_remainder=True for consistent batch sizes

## 3. Model Architecture
☐ Use supported operators (check compatibility list)
☐ Replace unsupported ops with equivalents
☐ Avoid dynamic shapes where possible
☐ Use batch normalization in training mode

## 4. Training Loop
☐ Enable mixed precision (AMP O2)
☐ Use loss scaling for stability
☐ Implement gradient clipping
☐ Enable gradient checkpointing for large models

## 5. Distributed Training
☐ Initialize HCCL properly
☐ Scale learning rate with device count
☐ Use gradients_mean=True
☐ Profile to identify bottlenecks

## 6. Memory Optimization
☐ Monitor memory usage with Profiler
☐ Use gradient checkpointing if OOM
☐ Reduce batch size if necessary
☐ Clear unused tensors explicitly

## 7. Inference Optimization
☐ Export model for inference (ONNX or CKPT)
☐ Use Ascend 310 for production serving
☐ Enable INT8 quantization if accuracy allows
☐ Profile inference latency

## 8. Profiling and Debugging
☐ Use MindSpore Profiler for analysis
☐ Check AICORE utilization (target >80%)
☐ Identify data loading bottlenecks
☐ Compare with GPU baseline
"""


# =============================================================================
# OPERATOR COMPATIBILITY
# =============================================================================

SUPPORTED_OPERATORS = {
    "computation": [
        "MatMul", "BatchMatMul", "Conv2D", "Conv1D",
        "DepthwiseConv2d", "MaxPool", "AvgPool",
        "Add", "Sub", "Mul", "Div", "Pow",
        "Exp", "Log", "Sqrt", "Rsqrt",
        "Abs", "Neg", "Sign",
    ],
    "activation": [
        "ReLU", "ReLU6", "LeakyReLU", "PReLU",
        "Sigmoid", "Tanh", "GELU", "Softmax",
        "Softplus", "Softsign", "ELU", "SELU",
    ],
    "normalization": [
        "BatchNorm", "LayerNorm", "GroupNorm",
        "InstanceNorm", "L2Normalize",
    ],
    "recurrent": [
        "LSTM", "GRU", "RNN",
    ],
    "attention": [
        "MultiHeadAttention", "ScaledDotProductAttention",
    ],
    "loss": [
        "SoftmaxCrossEntropy", "BinaryCrossEntropy",
        "MSE", "MAE", "Huber", "NLLLoss",
    ],
    "reduction": [
        "ReduceMean", "ReduceSum", "ReduceMax", "ReduceMin",
        "ArgMax", "ArgMin",
    ],
    "shape": [
        "Reshape", "Transpose", "Concat", "Split",
        "Squeeze", "ExpandDims", "Tile", "Gather",
        "Slice", "StridedSlice", "Pad",
    ],
}


OPERATORS_REQUIRING_FALLBACK = [
    "SparseTensor operations",
    "Complex number operations",
    "Custom CUDA kernels",
    "Dynamic control flow (while_loop with variable iterations)",
    "Ragged tensors",
]


# =============================================================================
# MODELARTS CONFIGURATION
# =============================================================================

MODELARTS_TRAINING_CONFIG = """
# ModelArts Training Job Configuration

# training_config.yaml
training_config:
  # Compute resources
  compute:
    instance_type: "modelarts.vm.cpu.8u.high"  # For data preprocessing
    # instance_type: "modelarts.p3.large.public"  # For NPU training
    instance_count: 1
    
  # For multi-NPU training
  ascend_config:
    instance_type: "modelarts.kat1.8xlarge"  # 8x Ascend 910
    instance_count: 1
    device_count: 8

  # Code and data
  code_dir: "obs://bucket/code/"
  boot_file: "train.py"
  data_url: "obs://bucket/data/"
  train_url: "obs://bucket/output/"
  
  # Hyperparameters
  hyperparameters:
    epochs: 100
    batch_size: 32
    learning_rate: 0.0001
    use_focal_loss: true
    
  # Framework
  framework:
    type: "mindspore"
    version: "1.9.0"
    
  # Logging
  log_url: "obs://bucket/logs/"
"""


MODELARTS_INFERENCE_CONFIG = """
# ModelArts Inference Service Configuration

# inference_config.yaml
inference_config:
  # Model
  model_name: "security-vuln-detector"
  model_version: "1.0.0"
  model_path: "obs://bucket/models/security_model.ckpt"
  
  # Runtime
  runtime:
    framework: "mindspore"
    framework_version: "1.9.0"
    device_target: "Ascend"
    
  # Compute (Ascend 310 for inference)
  compute:
    instance_type: "modelarts.vm.ai1.large"  # Ascend 310
    instance_count: 2  # For high availability
    
  # Auto-scaling
  scaling:
    min_instances: 2
    max_instances: 10
    target_cpu_utilization: 70
    scale_down_delay_seconds: 300
    
  # Networking
  network:
    vpc_id: "vpc-xxx"
    subnet_id: "subnet-xxx"
    security_group_id: "sg-xxx"
    
  # API configuration
  api:
    protocol: "https"
    timeout_ms: 10000
    max_request_size_mb: 1
"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_recommended_config(
    model_params: int,
    batch_size: int,
    seq_length: int,
    use_case: str = "training",
) -> Dict[str, Any]:
    """
    Get recommended Ascend configuration based on model size.
    
    Args:
        model_params: Number of model parameters
        batch_size: Training batch size
        seq_length: Input sequence length
        use_case: "training" or "inference"
    
    Returns:
        Recommended configuration dictionary
    """
    # Estimate memory usage (rough: 4 bytes per param + activations)
    param_memory_gb = (model_params * 4) / (1024 ** 3)
    activation_memory_gb = (batch_size * seq_length * 512 * 4) / (1024 ** 3)
    total_memory_gb = param_memory_gb + activation_memory_gb * 2  # Forward + backward
    
    config = {
        "estimated_memory_gb": total_memory_gb,
        "recommendations": [],
    }
    
    if use_case == "training":
        if total_memory_gb > 24:
            config["recommendations"].append("Use gradient checkpointing")
            config["recommendations"].append("Consider model parallelism")
        
        if total_memory_gb > 16:
            config["recommendations"].append("Enable mixed precision (AMP O2)")
        
        config["hardware"] = "Ascend 910"
        config["mixed_precision"] = total_memory_gb > 16
        config["gradient_checkpointing"] = total_memory_gb > 24
        config["dataset_sink_mode"] = True
        
    else:  # inference
        config["hardware"] = "Ascend 310"
        config["quantization"] = "INT8 recommended" if model_params > 100_000_000 else "FP16"
        config["batch_size"] = min(batch_size, 8)  # Smaller batches for latency
    
    return config


def estimate_training_time(
    model_tflops: float,
    dataset_samples: int,
    batch_size: int,
    epochs: int,
    hardware: AscendModel = AscendModel.ASCEND_910,
) -> Dict[str, float]:
    """
    Estimate training time on Ascend hardware.
    
    Args:
        model_tflops: Model TFLOPS per sample
        dataset_samples: Number of training samples
        batch_size: Batch size
        epochs: Number of epochs
        hardware: Target Ascend hardware
    
    Returns:
        Estimated time breakdown
    """
    specs = ASCEND_HARDWARE[hardware]
    
    # Steps per epoch
    steps_per_epoch = dataset_samples // batch_size
    total_steps = steps_per_epoch * epochs
    
    # Time per step (assuming 50% hardware efficiency)
    efficiency = 0.5
    tflops_per_step = model_tflops * batch_size
    time_per_step_s = tflops_per_step / (specs.fp16_tflops * efficiency)
    
    # Add data loading overhead (10%)
    time_per_step_s *= 1.1
    
    total_time_hours = (total_steps * time_per_step_s) / 3600
    
    return {
        "steps_per_epoch": steps_per_epoch,
        "total_steps": total_steps,
        "time_per_step_ms": time_per_step_s * 1000,
        "estimated_hours": total_time_hours,
        "estimated_cost_usd": total_time_hours * 5.0,  # Rough estimate
    }
