"""
AutoCoder Integration Layer
===========================
Unified integration for all AutoCoder ecosystem services.
 Connects UIS, SLM, AxiomCode, and auto-discovers local repos.
"""

import os
import logging
import json
import asyncio
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
from pathlib import Path
try:
    import aiohttp
except ImportError:
    aiohttp = None
import subprocess

logger = logging.getLogger(__name__)

REPO_PATHS = {
    "autocoder": Path("C:/Users/nrupa/autocoder"),
    "uis": Path("D:/UIS"),
    "axiomcode": Path("D:/axiomcode"),
    "slm": Path("D:/sl/projects/sllm"),
    "simplicity": Path("D:/simplicity"),
    "relay_sim": Path("D:/sl/projects/relay_sim"),
    "knowledge_app": Path("D:/sl/projects/Knowledge_app"),
    "mykey": Path("D:/sl/projects/mykey"),
    "vault_tracker": Path("D:/sl/projects/vault-tracker"),
}


@dataclass
class ServiceConfig:
    name: str
    url: str
    port: int
    repo_path: Optional[str] = None
    status: str = "unknown"
    has_utilities: bool = False
    has_engine: bool = False
    has_memory: bool = False


class ServiceRegistry:
    """Registry of all AutoCoder ecosystem services."""
    
    def __init__(self):
        self.services: Dict[str, ServiceConfig] = {}
        self._register_default_services()
        self._discover_local_repos()
    
    def _register_default_services(self):
        """Register known services."""
        # AutoCoder itself
        self.register("autocoder", "http://localhost:5000", 5000, str(REPO_PATHS.get("autocoder", "")))
        
        # UIS - Unified Intelligence System
        self.register("uis", "http://localhost:8000", 8000, str(REPO_PATHS.get("uis", "")))
        
        # SLM - Self-Learning Model
        self.register("slm", "http://localhost:8080", 8080, str(REPO_PATHS.get("sllm", "")))
        
        # AxiomCode - Mathematical code verification
        self.register("axiomcode", "http://localhost:9000", 9000, str(REPO_PATHS.get("axiomcode", "")))
        
        # Ollama for local models
        self.register("ollama", "http://localhost:11434", 11434)
        
        # LM Studio
        self.register("lmstudio", "http://localhost:1234", 1234)
    
    def _discover_local_repos(self):
        """Auto-discover local repos and detect capabilities."""
        for name, repo_path in REPO_PATHS.items():
            if not repo_path.exists():
                continue
            
            has_utilities = (repo_path / "config.py").exists()
            has_engine = (repo_path / "engine.py").exists() or (repo_path / "src" / "engine").exists()
            has_memory = (repo_path / "memory.py").exists() or (repo_path / "src" / "memory").exists()
            
            if name in self.services:
                self.services[name].has_utilities = has_utilities
                self.services[name].has_engine = has_engine
                self.services[name].has_memory = has_memory
                self.services[name].repo_path = str(repo_path)
                logger.info(f"Discovered {name}: utilities={has_utilities}, engine={has_engine}, memory={has_memory}")
    
    def discover_github_repos(self) -> List[str]:
        """Discover user's GitHub repos."""
        try:
            result = subprocess.run(
                ["gh", "api", "users/nrupala/repos", "--jq", ".[].full_name"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                repos = [r.strip() for r in result.stdout.strip().split("\n") if r.strip()]
                logger.info(f"Found {len(repos)} GitHub repos")
                return repos
        except Exception as e:
            logger.warning(f"Failed to fetch GitHub repos: {e}")
        return []
    
    def register(self, name: str, url: str, port: int, repo_path: str = ""):
        """Register a service."""
        self.services[name] = ServiceConfig(name=name, url=url, port=port, repo_path=repo_path or None)
        logger.info(f"Registered service: {name} at {url}")
    
    def get(self, name: str) -> Optional[ServiceConfig]:
        """Get a service by name."""
        return self.services.get(name)
    
    def get_url(self, name: str) -> Optional[str]:
        """Get service URL."""
        svc = self.services.get(name)
        return svc.url if svc else None
    
    def list_services(self) -> Dict[str, ServiceConfig]:
        """List all registered services."""
        return self.services.copy()
    
    def check_health(self, name: str) -> bool:
        """Check if a service is healthy."""
        import requests
        svc = self.services.get(name)
        if not svc:
            return False
        try:
            resp = requests.get(f"{svc.url}/health", timeout=2)
            return resp.status_code == 200
        except:
            return False
    
    async def check_health_async(self, name: str, session) -> bool:
        """Async health check."""
        if not aiohttp:
            return False
        svc = self.services.get(name)
        if not svc:
            return False
        try:
            async with session.get(f"{svc.url}/health", timeout=aiohttp.ClientTimeout(total=2)) as resp:
                return resp.status == 200
        except:
            return False
    
    async def check_all_health_async(self) -> Dict[str, bool]:
        """Check health of all services asynchronously."""
        if not aiohttp:
            return {}
        connector = aiohttp.TCPConnector(limit=10)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self.check_health_async(name, session) for name in self.services]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return {name: r for name, r in zip(self.services.keys(), results) if not isinstance(r, Exception)}
    
    def get_capabilities(self, name: str) -> Dict[str, bool]:
        """Get capabilities for a service."""
        svc = self.services.get(name)
        if not svc:
            return {}
        return {
            "has_utilities": svc.has_utilities,
            "has_engine": svc.has_engine,
            "has_memory": svc.has_memory,
        }
    
    def get_service_by_capability(self, capability: str) -> Optional[str]:
        """Find first service with given capability."""
        for name, svc in self.services.items():
            if getattr(svc, f"has_{capability}", False):
                return name
        return None


class CodeOrchestrator:
    """Orchestrates code generation across services."""
    
    def __init__(self):
        self.registry = ServiceRegistry()
    
    def generate_code(self, prompt: str, verify: bool = False) -> Dict[str, Any]:
        """Generate and optionally verify code."""
        result = {"prompt": prompt, "code": None, "verified": False, "errors": []}
        
        # Use local engine first (fastest)
        from engine import generate
        try:
            result["code"] = generate(prompt)
            logger.info(f"Generated code for: {prompt[:50]}...")
        except Exception as e:
            result["errors"].append(f"Generation failed: {e}")
        
        # Optionally verify with AxiomCode
        if verify and result["code"]:
            # TODO: Connect to axiomcode
            pass
        
        return result
    
    def chat_with_context(self, message: str, context: str = "") -> str:
        """Chat with UIS for context-aware responses."""
        # TODO: Connect to UIS
        return f"Response to: {message}"


# Global instances
registry = ServiceRegistry()
orchestrator = CodeOrchestrator()


def get_service(name: str) -> Optional[ServiceConfig]:
    return registry.get(name)

def list_all_services() -> Dict[str, ServiceConfig]:
    return registry.list_services()

def generate_code(prompt: str, verify: bool = False) -> Dict[str, Any]:
    return orchestrator.generate_code(prompt, verify)