"""
AutoCoder Models - Multi-model orchestration
"""

import os
import json
import logging
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    name: str
    provider: str
    base_url: str
    supports_tools: bool = False
    supports_vision: bool = False
    context_length: int = 8192


class BaseModelClient:
    """Base class for model clients."""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key

    def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError

    def chat(self, messages: list[dict], **kwargs) -> dict:
        raise NotImplementedError


class OllamaClient(BaseModelClient):
    """Ollama local model client."""

    def __init__(self, model: str = "deepseek-coder:14b", base_url: str = "http://localhost:11434"):
        super().__init__(base_url)
        self.model = model
        self._available = self._check_connection()

    def _check_connection(self) -> bool:
        try:
            import requests
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except:
            return False

    def is_available(self) -> bool:
        return self._available

    def list_models(self) -> list[dict]:
        try:
            import requests
            resp = requests.get(f"{self.base_url}/api/tags", timeout=10)
            return resp.json().get("models", [])
        except:
            return []

    def generate(self, prompt: str, **kwargs) -> str:
        import requests
        model_name = self.model.split(":")[0] if ":" in self.model else self.model
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.2),
                "num_predict": kwargs.get("max_tokens", 4096),
            }
        }

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=kwargs.get("timeout", 180)
            )
            resp.raise_for_status()
            return resp.json().get("response", "")
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return f"Error: {e}"

    def chat(self, messages: list[dict], **kwargs) -> dict:
        import requests
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.2),
                "num_predict": kwargs.get("max_tokens", 4096),
            }
        }

        if "tools" in kwargs:
            payload["tools"] = kwargs["tools"]

        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=kwargs.get("timeout", 180)
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            return {"message": {"content": f"Error: {e}"}, "done": True}


class OpenAIClient(BaseModelClient):
    """OpenAI API client."""

    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None):
        super().__init__("https://api.openai.com/v1", api_key or os.environ.get("OPENAI_API_KEY"))
        self.model = model

    def generate(self, prompt: str, **kwargs) -> str:
        import requests
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", 0.2),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=kwargs.get("timeout", 120)
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return f"Error: {e}"

    def chat(self, messages: list[dict], **kwargs) -> dict:
        import requests
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.2),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=kwargs.get("timeout", 120)
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"OpenAI chat failed: {e}")
            return {"choices": [{"message": {"content": f"Error: {e}"}}]}


class AnthropicClient(BaseModelClient):
    """Anthropic Claude API client."""

    def __init__(self, model: str = "claude-sonnet-4-20250514", api_key: Optional[str] = None):
        super().__init__("https://api.anthropic.com/v1", api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = model

    def generate(self, prompt: str, **kwargs) -> str:
        import requests
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        payload = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            resp = requests.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload,
                timeout=kwargs.get("timeout", 120)
            )
            resp.raise_for_status()
            return resp.json()["content"][0]["text"]
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            return f"Error: {e}"

    def chat(self, messages: list[dict], **kwargs) -> dict:
        return {"choices": [{"message": {"content": self.generate(messages[-1]["content"], **kwargs)}}]}


class LMStudioClient(BaseModelClient):
    """LM Studio local model client."""

    def __init__(self, model: str = "local-model", base_url: str = "http://localhost:1234/v1"):
        super().__init__(base_url)
        self.model = model
        self._available = self._check_connection()

    def _check_connection(self) -> bool:
        try:
            import requests
            resp = requests.get(f"{self.base_url.replace('/v1', '')}/models", timeout=5)
            return resp.status_code == 200
        except:
            return False

    def is_available(self) -> bool:
        return self._available

    def generate(self, prompt: str, **kwargs) -> str:
        return OllamaClient(self.model, self.base_url.replace("/v1", "")).generate(prompt, **kwargs)

    def chat(self, messages: list[dict], **kwargs) -> dict:
        return OllamaClient(self.model, self.base_url.replace("/v1", "")).chat(messages, **kwargs)


class ModelOrchestrator:
    """Routes requests to optimal model."""

    def __init__(self, default_model: str = "deepseek-coder:14b"):
        self.default_model = default_model
        self.clients: dict[str, BaseModelClient] = {}
        self._init_clients()

    def _init_clients(self):
        self.clients["ollama"] = OllamaClient()
        self.clients["openai"] = OpenAIClient()
        self.clients["anthropic"] = AnthropicClient()
        self.clients["lmstudio"] = LMStudioClient()

    def get_available_models(self) -> list[str]:
        models = []
        if self.clients["ollama"].is_available():
            models.extend([m["name"] for m in self.clients["ollama"].list_models()])
        return models

    def select_model(self, task_type: str, use_gpu: bool = True) -> str:
        """Select model based on task type."""
        if not use_gpu:
            return "llama3.2:3b"
        
        model_map = {
            "code_generation": "deepseek-coder:14b",
            "reasoning": "deepseek-r1:7b",
            "natural_response": "llama3.2:3b",
            "verification": "stable-code:3b",
            "web_search": "llama3.2:3b",
        }
        return model_map.get(task_type, self.default_model)

    def generate(self, prompt: str, provider: str = "ollama", **kwargs) -> str:
        if provider not in self.clients:
            provider = "ollama"
        
        client = self.clients[provider]
        
        if provider == "ollama":
            return client.generate(prompt, **kwargs)
        elif provider == "openai":
            return client.generate(prompt, **kwargs)
        elif provider == "anthropic":
            return client.generate(prompt, **kwargs)
        
        return client.generate(prompt, **kwargs)

    def chat(self, messages: list[dict], provider: str = "ollama", **kwargs) -> dict:
        if provider not in self.clients:
            provider = "ollama"
        return self.clients[provider].chat(messages, **kwargs)
