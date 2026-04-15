"""
AutoCoder System Checker
Checks all available build tools and services
"""

import os
import subprocess
import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class ToolInfo:
    name: str
    path: str
    version: str
    available: bool


def check_command(cmd: str, args: list = None) -> tuple[bool, str]:
    """Check if a command is available and get version."""
    try:
        result = subprocess.run(
            [cmd, "--version"] if args is None else [cmd, args],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0] if result.stdout else result.stderr.strip().split('\n')[0]
            return True, version
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return False, ""


def find_executable(paths: list[str]) -> Optional[str]:
    """Find executable from a list of possible paths."""
    for path in paths:
        expanded = os.path.expandvars(path)
        if os.path.exists(expanded):
            return expanded
    return None


class SystemChecker:
    """Check all available build tools."""

    def __init__(self):
        self.tools = {}

    def check_all(self) -> dict:
        """Check all tools."""
        self._check_language("Python", ["python", "py"], ["--version"])
        self._check_language("Node.js", ["node"], ["--version"])
        self._check_language("Docker", ["docker"], ["--version"])
        self._check_language("Git", ["git"], ["--version"])
        
        self._check_ide("VS Code", [
            r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
            r"%ProgramFiles%\Microsoft VS Code\Code.exe"
        ])
        self._check_ide("Cline", [
            r"%LOCALAPPDATA%\Programs\Cline\Cline.exe",
            r"%ProgramFiles%\Cline\Cline.exe",
            "cline"
        ])
        
        self._check_service("Ollama", "http://localhost:11434", "/api/tags")
        self._check_service("LM Studio", "http://localhost:1234", "/v1/models")
        
        self._check_language("npm", ["npm"], ["--version"])
        self._check_language("pip", ["pip"], ["--version"])
        
        self._check_gpu()
        
        return self.tools

    def _check_language(self, name: str, commands: list, args: list):
        for cmd in commands:
            available, version = check_command(cmd, args)
            if available:
                self.tools[name] = ToolInfo(name, cmd, version, True)
                return
        self.tools[name] = ToolInfo(name, "", "", False)

    def _check_ide(self, name: str, paths: list):
        path = find_executable(paths)
        if path:
            self.tools[name] = ToolInfo(name, path, "Found", True)
        else:
            self.tools[name] = ToolInfo(name, "", "", False)

    def _check_service(self, name: str, base_url: str, endpoint: str):
        try:
            import requests
            resp = requests.get(f"{base_url}{endpoint}", timeout=5)
            if resp.status_code == 200:
                self.tools[name] = ToolInfo(name, base_url, "Running", True)
                return
        except:
            pass
        self.tools[name] = ToolInfo(name, base_url, "", False)

    def _check_gpu(self):
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                gpu_count = torch.cuda.device_count()
                self.tools["GPU"] = ToolInfo("NVIDIA GPU", f"{gpu_count}x {gpu_name}", gpu_name, True)
                return
        except:
            pass
        
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                gpu_name = result.stdout.strip()
                self.tools["GPU"] = ToolInfo("NVIDIA GPU", "nvidia-smi", gpu_name, True)
                return
        except:
            pass
        
        self.tools["GPU"] = ToolInfo("GPU", "", "CPU only", False)

    def print_report(self):
        print("\n" + "="*60)
        print("AutoCoder System Check")
        print("="*60)
        
        categories = {
            "Languages": ["Python", "Node.js", "Docker", "Git"],
            "IDEs": ["VS Code", "Cline"],
            "Services": ["Ollama", "LM Studio"],
            "Package Managers": ["npm", "pip"],
            "Hardware": ["GPU"]
        }
        
        for category, items in categories.items():
            print(f"\n{category}:")
            for name in items:
                tool = self.tools.get(name)
                if tool:
                    status = "✓" if tool.available else "✗"
                    version = tool.version if tool.version else "Not found"
                    print(f"  {status} {name}: {version}")

    def get_recommendations(self) -> list[str]:
        """Get setup recommendations."""
        recs = []
        
        if not self.tools.get("Python", ToolInfo("", "", "", False)).available:
            recs.append("Install Python 3.10+ from python.org")
        if not self.tools.get("Node.js", ToolInfo("", "", "", False)).available:
            recs.append("Install Node.js from nodejs.org")
        if not self.tools.get("Docker", ToolInfo("", "", "", False)).available:
            recs.append("Install Docker Desktop from docker.com")
        if not self.tools.get("Ollama", ToolInfo("", "", "", False)).available:
            recs.append("Install Ollama from ollama.ai for local AI models")
        
        gpu = self.tools.get("GPU")
        if gpu and not gpu.available:
            recs.append("Consider adding NVIDIA GPU for faster AI processing")
        
        return recs


def main():
    checker = SystemChecker()
    results = checker.check_all()
    checker.print_report()
    
    recs = checker.get_recommendations()
    if recs:
        print("\n" + "="*60)
        print("Recommendations:")
        print("="*60)
        for rec in recs:
            print(f"  • {rec}")
    
    print("\n" + "="*60)
    print("To install all dependencies:")
    print("="*60)
    print("  pip install -r requirements.txt")
    print("  npm install -g typescript")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
