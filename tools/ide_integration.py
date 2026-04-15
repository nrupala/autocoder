"""
AutoCoder Integration with VS Code, Cline, and Antigravity
"""

import os
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class IDEConfig:
    """IDE configuration."""
    name: str
    path: str
    workspace: str = None


class VSCodeIntegration:
    """VS Code integration."""

    def __init__(self, workspace: str = None):
        self.workspace = workspace or os.getcwd()
        
        self.code_paths = [
            r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
            r"%ProgramFiles%\Microsoft VS Code\Code.exe",
            r"%ProgramFiles(x86)%\Microsoft VS Code\Code.exe",
        ]
        
    def find_executable(self) -> Optional[str]:
        for path in self.code_paths:
            expanded = os.path.expandvars(path)
            if Path(expanded).exists():
                return expanded
        return None

    def open_workspace(self, path: str = None) -> bool:
        """Open workspace in VS Code."""
        code = self.find_executable()
        if not code:
            return False
        
        target = path or self.workspace
        
        try:
            subprocess.Popen([code, target])
            return True
        except:
            return False

    def open_file(self, file_path: str, line: int = None) -> bool:
        """Open file at specific line."""
        code = self.find_executable()
        if not code:
            return False
        
        target = file_path
        if line:
            target = f"{file_path}:{line}"
        
        try:
            subprocess.Popen([code, "--goto", target])
            return True
        except:
            return False

    def run_command(self, command: str, *args) -> dict:
        """Run VS Code command via CLI."""
        code = self.find_executable()
        if not code:
            return {"success": False, "error": "VS Code not found"}
        
        cmd = [code, command] + list(args)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class ClineIntegration:
    """Cline (Claude Code) integration."""

    def __init__(self):
        self.executable = self._find_executable()

    def _find_executable(self) -> Optional[str]:
        paths = [
            r"%LOCALAPPDATA%\Programs\Cline\Cline.exe",
            r"%ProgramFiles%\Cline\Cline.exe",
            "cline",  # If in PATH
        ]
        
        for path in paths:
            expanded = os.path.expandvars(path)
            if Path(expanded).exists():
                return expanded
            # Check if in PATH
            result = subprocess.run(
                ["where", path] if os.name == "nt" else ["which", path],
                capture_output=True
            )
            if result.returncode == 0:
                return path
        return None

    def is_available(self) -> bool:
        return self.executable is not None

    def run_command(self, args: list[str]) -> dict:
        """Run Cline command."""
        if not self.is_available():
            return {"success": False, "error": "Cline not found"}
        
        cmd = [self.executable] + args
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def chat(self, message: str) -> str:
        """Send message to Cline."""
        result = self.run_command(["chat", message])
        return result.get("output", "") if result.get("success") else str(result.get("error"))


class AntigravityIntegration:
    """Antigravity integration."""

    def __init__(self):
        self.base_url = os.environ.get("ANTIGRAVITY_URL", "http://localhost:8080")
        self.api_key = os.environ.get("ANTIGRAVITY_API_KEY", "")

    def is_available(self) -> bool:
        """Check if Antigravity is running."""
        try:
            import requests
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            return resp.status_code == 200
        except:
            return False

    def generate(self, prompt: str, **kwargs) -> dict:
        """Generate code via Antigravity."""
        try:
            import requests
            payload = {
                "prompt": prompt,
                **kwargs
            }
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            resp = requests.post(
                f"{self.base_url}/generate",
                json=payload,
                headers=headers,
                timeout=180
            )
            resp.raise_for_status()
            return {"success": True, "result": resp.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def embed_code(self, code: str, language: str = "python") -> dict:
        """Get code embeddings."""
        try:
            import requests
            payload = {"code": code, "language": language}
            resp = requests.post(
                f"{self.base_url}/embed",
                json=payload,
                timeout=30
            )
            resp.raise_for_status()
            return {"success": True, "embedding": resp.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}


class IDEOrchestrator:
    """Orchestrates all IDE integrations."""

    def __init__(self):
        self.vscode = VSCodeIntegration()
        self.cline = ClineIntegration()
        self.antigravity = AntigravityIntegration()

    def get_status(self) -> dict:
        """Get status of all integrations."""
        return {
            "vscode": {
                "available": self.vscode.find_executable() is not None,
                "path": self.vscode.find_executable()
            },
            "cline": {
                "available": self.cline.is_available()
            },
            "antigravity": {
                "available": self.antigravity.is_available(),
                "url": self.antigravity.base_url
            }
        }

    def open_in_vscode(self, path: str) -> bool:
        """Open path in VS Code."""
        return self.vscode.open_workspace(path)

    def generate_with_antigravity(self, prompt: str) -> dict:
        """Generate with Antigravity."""
        return self.antigravity.generate(prompt)

    def fallback_to_cline(self, prompt: str) -> str:
        """Fallback to Cline."""
        return self.cline.chat(prompt)
