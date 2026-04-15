"""
AutoCoder LLM Adapter
===================
AutoCoder adopts ANY LLM/GGUF model and makes it work.
Searches web, reads docs, makes autonomous coding possible.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Optional, List, Dict, Any


class LLMFinder:
    """Finds local GGUF models."""
    
    MODEL_LOCATIONS = [
        "D:/models",
        "C:/models",
        os.path.expanduser("~/models"),
        "D:/lmstudio-community",
    ]
    
    @classmethod
    def find_gguf_models(cls) -> List[Dict[str, Any]]:
        """Find all GGUF models on system."""
        models = []
        for loc in cls.MODEL_LOCATIONS:
            p = Path(loc)
            if p.exists():
                for f in p.rglob("*.gguf"):
                    models.append({
                        "path": str(f),
                        "name": f.stem,
                        "size": f.stat().st_size
                    })
        return models
    
    @classmethod
    def get_best_model(cls) -> Optional[Dict]:
        """Get best available model."""
        models = cls.find_gguf_models()
        if not models:
            return None
        # Prefer smaller quantized models for speed
        models.sort(key=lambda x: x.get("size", 0))
        return models[0]


class WebSearcher:
    """AutoCoder searches the web."""
    
    @classmethod
    def search(cls, query: str, num: int = 5) -> List[Dict]:
        """Search web for information."""
        try:
            # Try using curl/requests
            import urllib.parse
            url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}&format=json"
            
            proc = subprocess.run([
                "curl", "-s", url
            ], capture_output=True, text=True, timeout=10)
            
            if proc.returncode == 0:
                return [{"query": query, "results": proc.stdout[:500]}]
        except Exception as e:
            pass
        
        return [{"query": query, "error": str(e)}]
    
    @classmethod
    def get_docs(cls, topic: str) -> str:
        """Get documentation for a topic."""
        queries = [
            f"{topic} python documentation",
            f"{topic} github examples",
            f"how to use {topic} tutorial"
        ]
        
        for q in queries:
            results = cls.search(q)
            if results:
                return str(results[0])[:500]
        return ""


class AutoCoderLLM:
    """
    AutoCoder that adopts ANY LLM.
    - Finds local GGUF models
    - Uses Ollama if available
    - Uses LM Studio if available
    - Falls back to template
    - Searches web for help
    """
    
    def __init__(self):
        self.model = None
        self.provider = "none"
        self._detect()
    
    def _detect(self):
        """Detect available LLM."""
        # Check for GGUF models
        gguf_models = LLMFinder.find_gguf_models()
        if gguf_models:
            self.model = gguf_models[0]
            self.provider = "gguf"
            return
        
        # Check for Ollama
        try:
            subprocess.run(["ollama", "list"], capture_output=True, timeout=5)
            self.provider = "ollama"
            self.model = {"name": "llama2"}
            return
        except:
            pass
        
        # Check for LM Studio
        try:
            import requests
            r = requests.get("http://localhost:1234/v1/models", timeout=2)
            if r.status_code == 200:
                self.provider = "lmstudio"
                self.model = r.json().get("data", [{}])[0] if r.json().get("data") else {"id": "default"}
                return
        except:
            pass
        
        # Fall back to template
        self.provider = "template"
        self.model = {"name": "template"}
    
    def generate(self, prompt: str) -> str:
        """Generate code with best available LLM."""
        if self.provider == "gguf":
            return self._generate_gguf(prompt)
        elif self.provider == "ollama":
            return self._generate_ollama(prompt)
        elif self.provider == "lmstudio":
            return self._generate_lmstudio(prompt)
        else:
            return self._generate_template(prompt)
    
    def _generate_gguf(self, prompt: str) -> str:
        """Generate using llama.cpp."""
        from engine import generate
        return generate(prompt)
    
    def _generate_ollama(self, prompt: str) -> str:
        """Generate using Ollama."""
        try:
            import requests
            r = requests.post("http://localhost:11434/api/generate", json={
                "model": "llama2",
                "prompt": prompt,
                "stream": False
            }, timeout=60)
            if r.status_code == 200:
                return r.json().get("response", "")
        except:
            pass
        return self._generate_template(prompt)
    
    def _generate_lmstudio(self, prompt: str) -> str:
        """Generate using LM Studio."""
        try:
            import requests
            r = requests.post("http://localhost:1234/v1/chat/completions", json={
                "model": self.model.get("id", "local-model"),
                "messages": [{"role": "user", "content": prompt}]
            }, timeout=60)
            if r.status_code == 200:
                return r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        except:
            pass
        return self._generate_template(prompt)
    
    def _generate_template(self, prompt: str) -> str:
        """Generate using template engine."""
        from engine import generate
        return generate(prompt)
    
    def search_and_code(self, prompt: str) -> str:
        """AutoCoder searches web then generates code."""
        # Extract what to search for
        keywords = prompt.lower().split()
        if any(k in prompt.lower() for k in ["how", "what", "example", "docs"]):
            docs = WebSearcher.get_docs(prompt)
            if docs:
                prompt = f"{prompt}\n\nReference: {docs}"
        
        return self.generate(prompt)
    
    def get_status(self) -> Dict:
        """Get LLM status."""
        return {
            "provider": self.provider,
            "model": self.model.get("name") if self.model else "none",
            "gguf_available": bool(LLMFinder.find_gguf_models())
        }


# Global instance
_llm = None

def get_llm() -> AutoCoderLLM:
    global _llm
    if _llm is None:
        _llm = AutoCoderLLM()
    return _llm


def generate_with_llm(prompt: str) -> str:
    """Generate with best available LLM."""
    return get_llm().generate(prompt)


def search_and_generate(prompt: str) -> str:
    """Search web then generate."""
    return get_llm().search_and_code(prompt)


if __name__ == "__main__":
    llm = get_llm()
    status = llm.get_status()
    print(f"AutoCoder LLM Status:")
    print(f"  Provider: {status['provider']}")
    print(f"  Model: {status['model']}")
    print(f"  GGUF Found: {status['gguf_available']}")
    
    # Test generation
    print("\nTesting code generation:")
    code = llm.generate("hello world python")
    print(code[:200])