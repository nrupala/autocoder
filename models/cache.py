"""
AutoCoder LLM Cache
Reduces cost and latency by caching LLM responses
"""

import os
import json
import time
import hashlib
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cached LLM response."""
    model: str
    prompt_hash: str
    response: str
    timestamp: float
    metadata: dict = field(default_factory=dict)


class LLMCache:
    """Persistent cache for LLM responses."""

    def __init__(self, cache_dir: str = ".autocoder/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.cache_dir / "index.json"
        self._load_index()

    def _load_index(self):
        if self.index_file.exists():
            try:
                self.index = json.loads(self.index_file.read_text())
            except:
                self.index = {}
        else:
            self.index = {}

    def _save_index(self):
        self.index_file.write_text(json.dumps(self.index, indent=2))

    def _hash_prompt(self, model: str, prompt: str) -> str:
        data = f"{model}:{prompt}"
        return hashlib.sha512(data.encode()).hexdigest()[:32]

    def _get_cache_path(self, prompt_hash: str) -> Path:
        return self.cache_dir / f"{prompt_hash}.json"

    def get(self, model: str, prompt: str, max_age_seconds: int = 86400) -> Optional[str]:
        """Get cached response."""
        prompt_hash = self._hash_prompt(model, prompt)
        
        if prompt_hash not in self.index:
            return None
        
        entry_data = self.index[prompt_hash]
        
        if time.time() - entry_data.get("timestamp", 0) > max_age_seconds:
            logger.debug(f"Cache expired for {prompt_hash}")
            return None
        
        cache_file = self._get_cache_path(prompt_hash)
        if not cache_file.exists():
            return None
        
        try:
            data = json.loads(cache_file.read_text())
            logger.debug(f"Cache hit for {prompt_hash}")
            return data.get("response")
        except:
            return None

    def put(self, model: str, prompt: str, response: str, metadata: dict = None):
        """Store response in cache."""
        prompt_hash = self._hash_prompt(model, prompt)
        
        cache_file = self._get_cache_path(prompt_hash)
        cache_data = {
            "model": model,
            "prompt_hash": prompt_hash,
            "response": response,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        
        cache_file.write_text(json.dumps(cache_data))
        
        self.index[prompt_hash] = {
            "model": model,
            "timestamp": time.time()
        }
        self._save_index()
        
        logger.debug(f"Cached response for {prompt_hash}")

    def clear(self, older_than_seconds: int = None):
        """Clear cache."""
        if older_than_seconds is None:
            for cache_file in self.cache_dir.glob("*.json"):
                if cache_file != self.index_file:
                    cache_file.unlink()
            self.index = {}
            self._save_index()
            logger.info("Cache cleared")
        else:
            now = time.time()
            for prompt_hash, entry in list(self.index.items()):
                if now - entry.get("timestamp", 0) > older_than_seconds:
                    cache_file = self._get_cache_path(prompt_hash)
                    if cache_file.exists():
                        cache_file.unlink()
                    del self.index[prompt_hash]
            self._save_index()
            logger.info(f"Cleared cache older than {older_than_seconds}s")

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total_size = 0
        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file != self.index_file:
                total_size += cache_file.stat().st_size
        
        return {
            "entries": len(self.index),
            "size_bytes": total_size,
            "size_mb": total_size / (1024 * 1024)
        }


class ModelConfig:
    """Model configuration management."""

    def __init__(self, config_dir: str = ".autocoder/config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "models.json"
        self._load_config()

    def _load_config(self):
        if self.config_file.exists():
            try:
                self.config = json.loads(self.config_file.read_text())
            except:
                self.config = self._default_config()
        else:
            self.config = self._default_config()

    def _default_config(self) -> dict:
        return {
            "providers": {
                "ollama": {
                    "base_url": "http://localhost:11434",
                    "models": {
                        "deepseek-coder:14b": {
                            "description": "Best for code generation",
                            "quantization": "q4_0",
                            "context_length": 16384
                        },
                        "llama3.2:3b": {
                            "description": "General purpose",
                            "quantization": "q4_0",
                            "context_length": 8192
                        },
                        "mistral:7b": {
                            "description": "Fast reasoning",
                            "quantization": "q4_0",
                            "context_length": 8192
                        },
                        "phi3:3b": {
                            "description": "Low resource",
                            "quantization": "q8_0",
                            "context_length": 4096
                        }
                    }
                },
                "openai": {
                    "api_base": "https://api.openai.com/v1",
                    "models": {
                        "gpt-4o": {"context_length": 128000},
                        "gpt-4-turbo": {"context_length": 128000},
                        "gpt-3.5-turbo": {"context_length": 16385}
                    }
                },
                "anthropic": {
                    "api_base": "https://api.anthropic.com",
                    "models": {
                        "claude-sonnet-4-20250514": {"context_length":200000},
                        "claude-haiku-3": {"context_length": 200000}
                    }
                }
            },
            "routing": {
                "code_generation": "ollama:deepseek-coder:14b",
                "reasoning": "ollama:deepseek-r1:7b",
                "natural_response": "ollama:llama3.2:3b",
                "verification": "ollama:stable-code:3b"
            }
        }

    def save(self):
        self.config_file.write_text(json.dumps(self.config, indent=2))

    def get(self, key: str, default=None):
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def set(self, key: str, value):
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        config[keys[-1]] = value
        self.save()
