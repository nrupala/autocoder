"""
AutoCoder Core - Hardware Detection & Optimization
"""

import platform
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class HardwareProfile:
    gpu_count: int = 0
    gpu_name: str = ""
    gpu_memory: int = 0
    cpu_count: int = 1
    ram_total: int = 0
    has_cuda: bool = False
    os_name: str = ""


@dataclass
class ExecutionConfig:
    use_gpu: bool = False
    model_quantization: str = "q4_0"
    batch_size: int = 8
    parallel_workers: int = 2
    model: str = "deepseek-coder:14b"
    max_tokens: int = 4096
    temperature: float = 0.2


class HardwareDetector:
    """Detects available compute resources."""

    def __init__(self):
        self.profile = self._detect()

    def _detect(self) -> HardwareProfile:
        profile = HardwareProfile()
        profile.os_name = platform.system()

        try:
            import psutil
            profile.cpu_count = psutil.cpu_count(logical=False) or 1
            profile.ram_total = psutil.virtual_memory().total
        except ImportError:
            pass

        try:
            import torch
            if torch.cuda.is_available():
                profile.has_cuda = True
                profile.gpu_count = torch.cuda.device_count()
                profile.gpu_name = torch.cuda.get_device_name(0)
                profile.gpu_memory = torch.cuda.get_device_properties(0).total_memory
        except ImportError:
            pass

        return profile

    def get_execution_config(self, task_type: str = "code_generation") -> ExecutionConfig:
        if self.profile.has_cuda and self.profile.gpu_count > 0:
            return self._gpu_config()
        else:
            return self._cpu_config()

    def _gpu_config(self) -> ExecutionConfig:
        mem_gb = self.profile.gpu_memory / (1024**3)

        if mem_gb >= 24:
            return ExecutionConfig(
                use_gpu=True, model_quantization="q2_K", batch_size=64,
                parallel_workers=8, model="deepseek-coder:14b"
            )
        elif mem_gb >= 16:
            return ExecutionConfig(
                use_gpu=True, model_quantization="q4_0", batch_size=32,
                parallel_workers=4, model="deepseek-coder:14b"
            )
        elif mem_gb >= 10:
            return ExecutionConfig(
                use_gpu=True, model_quantization="q4_0", batch_size=16,
                parallel_workers=2, model="qwen2.5-coder:7b"
            )
        else:
            return ExecutionConfig(
                use_gpu=True, model_quantization="q5_1", batch_size=8,
                parallel_workers=1, model="phi3:3b"
            )

    def _cpu_config(self) -> ExecutionConfig:
        ram_gb = self.profile.ram_total / (1024**3)

        if ram_gb >= 32:
            return ExecutionConfig(
                use_gpu=False, model_quantization="q8_0", batch_size=8,
                parallel_workers=4, model="llama3.2:3b"
            )
        elif ram_gb >= 16:
            return ExecutionConfig(
                use_gpu=False, model_quantization="q5_1", batch_size=4,
                parallel_workers=2, model="llama3.2:3b"
            )
        elif ram_gb >= 8:
            return ExecutionConfig(
                use_gpu=False, model_quantization="q4_0", batch_size=2,
                parallel_workers=1, model="llama3.2:1b"
            )
        else:
            return ExecutionConfig(
                use_gpu=False, model_quantization="q4_0", batch_size=1,
                parallel_workers=1, model="stable-code:3b"
            )


def get_optimal_model_for_task(task_type: str, config: ExecutionConfig) -> str:
    """Get optimal model based on task type and hardware."""
    
    model_map = {
        "code_generation": [
            ("deepseek-coder:14b", 16),
            ("qwen2.5-coder:7b", 10),
            ("phi3:3b", 6),
            ("stable-code:3b", 4),
        ],
        "reasoning": [
            ("deepseek-r1:7b", 16),
            ("llama3.2:3b", 8),
            ("mistral:7b", 8),
        ],
        "natural_response": [
            ("llama3.2:3b", 8),
            ("mistral:7b", 8),
            ("phi3:3b", 4),
        ],
        "verification": [
            ("stable-code:3b", 4),
            ("deepseek-coder:14b", 16),
        ],
    }

    candidates = model_map.get(task_type, model_map["code_generation"])
    
    if config.use_gpu:
        mem_gb = config.batch_size * 2
        for model, min_mem in candidates:
            if mem_gb >= min_mem or min_mem <= 6:
                return model
        return candidates[-1][0]
    else:
        return candidates[-1][0]
