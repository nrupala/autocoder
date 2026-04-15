"""
AutoCoder Process Manager
Manages concurrent processes: Ollama, LM Studio, Docker, etc.
"""

import os
import signal
import subprocess
import time
import logging
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Information about a running process."""
    name: str
    pid: int
    command: list[str]
    started_at: float
    status: str = "running"


class ProcessManager:
    """Manages background processes."""

    def __init__(self):
        self.processes: dict[str, ProcessInfo] = {}

    def start_process(self, name: str, command: list[str], cwd: str = None) -> ProcessInfo:
        """Start a background process."""
        env = os.environ.copy()
        
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            info = ProcessInfo(
                name=name,
                pid=process.pid,
                command=command,
                started_at=time.time(),
                status="running"
            )
            self.processes[name] = info
            logger.info(f"Started process: {name} (PID: {process.pid})")
            return info
            
        except Exception as e:
            logger.error(f"Failed to start {name}: {e}")
            raise

    def stop_process(self, name: str, timeout: int = 10) -> bool:
        """Stop a running process."""
        if name not in self.processes:
            return False

        info = self.processes[name]
        
        try:
            if os.name == 'nt':
                os.kill(info.pid, signal.CTRL_BREAK_EVENT)
            else:
                os.kill(info.pid, signal.SIGTERM)
            
            time.sleep(1)
            
            if info.pid in [p.pid for p in self.processes.values()]:
                os.kill(info.pid, signal.SIGKILL)
            
            info.status = "stopped"
            logger.info(f"Stopped process: {name}")
            return True
            
        except ProcessLookupError:
            info.status = "stopped"
            return True
        except Exception as e:
            logger.error(f"Failed to stop {name}: {e}")
            return False

    def get_status(self, name: str) -> Optional[ProcessInfo]:
        """Get process status."""
        return self.processes.get(name)

    def list_processes(self) -> list[ProcessInfo]:
        """List all managed processes."""
        return list(self.processes.values())


class OllamaManager:
    """Manages Ollama service."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.process_manager = ProcessManager()

    def is_running(self) -> bool:
        """Check if Ollama is running."""
        try:
            import requests
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except:
            return False

    def start(self, model: str = None) -> bool:
        """Start Ollama service."""
        if self.is_running():
            logger.info("Ollama is already running")
            return True

        try:
            cmd = ["ollama", "serve"]
            self.process_manager.start_process("ollama", cmd)
            time.sleep(3)
            
            if model:
                self.pull_model(model)
            
            return self.is_running()
            
        except Exception as e:
            logger.error(f"Failed to start Ollama: {e}")
            return False

    def stop(self) -> bool:
        """Stop Ollama service."""
        return self.process_manager.stop_process("ollama")

    def pull_model(self, model: str) -> bool:
        """Pull a model."""
        try:
            result = subprocess.run(
                ["ollama", "pull", model],
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to pull model {model}: {e}")
            return False

    def list_models(self) -> list[dict]:
        """List available models."""
        try:
            import requests
            resp = requests.get(f"{self.base_url}/api/tags", timeout=10)
            return resp.json().get("models", [])
        except:
            return []


class LMStudioManager:
    """Manages LM Studio service."""

    def __init__(self, base_url: str = "http://localhost:1234"):
        self.base_url = base_url
        self.process_manager = ProcessManager()

    def is_running(self) -> bool:
        """Check if LM Studio is running."""
        try:
            import requests
            resp = requests.get(f"{self.base_url}/v1/models", timeout=5)
            return resp.status_code == 200
        except:
            return False

    def start(self) -> bool:
        """Start LM Studio."""
        if self.is_running():
            return True

        lmstudio_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\LM Studio\LM Studio.exe"),
            r"C:\Program Files\LM Studio\LM Studio.exe",
        ]
        
        for path in lmstudio_paths:
            if Path(path).exists():
                try:
                    subprocess.Popen([path])
                    time.sleep(5)
                    return self.is_running()
                except:
                    pass
        
        logger.warning("LM Studio not found")
        return False


class DockerManager:
    """Manages Docker containers."""

    def is_available(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "version", "--format", "{{.Server.Version}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False

    def list_containers(self, all: bool = True) -> list[dict]:
        """List Docker containers."""
        if not self.is_available():
            return []

        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{.ID}}|{{.Names}}|{{.Status}}|{{.Image}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            containers = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|")
                    containers.append({
                        "id": parts[0],
                        "name": parts[1],
                        "status": parts[2],
                        "image": parts[3] if len(parts) > 3 else ""
                    })
            return containers
            
        except:
            return []

    def start_container(self, name: str) -> bool:
        """Start a container."""
        try:
            result = subprocess.run(
                ["docker", "start", name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False

    def stop_container(self, name: str) -> bool:
        """Stop a container."""
        try:
            result = subprocess.run(
                ["docker", "stop", name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False

    def run_container(self, image: str, name: str = None, ports: dict = None, detach: bool = True) -> str:
        """Run a container."""
        cmd = ["docker", "run"]
        
        if detach:
            cmd.append("-d")
        
        if name:
            cmd.extend(["--name", name])
        
        if ports:
            for host, container in ports.items():
                cmd.extend(["-p", f"{host}:{container}"])
        
        cmd.append(image)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return ""


class ServiceOrchestrator:
    """Orchestrates all services."""

    def __init__(self):
        self.ollama = OllamaManager()
        self.lmstudio = LMStudioManager()
        self.docker = DockerManager()

    def check_all_services(self) -> dict:
        """Check status of all services."""
        return {
            "ollama": {
                "running": self.ollama.is_running(),
                "models": self.ollama.list_models() if self.ollama.is_running() else []
            },
            "lmstudio": {
                "running": self.lmstudio.is_running()
            },
            "docker": {
                "available": self.docker.is_available(),
                "containers": self.docker.list_containers() if self.docker.is_available() else []
            }
        }

    def ensure_services(self, required: list[str] = None) -> dict:
        """Ensure required services are running."""
        if required is None:
            required = ["ollama"]
        
        results = {}
        
        if "ollama" in required:
            if not self.ollama.is_running():
                self.ollama.start()
            results["ollama"] = self.ollama.is_running()
        
        if "lmstudio" in required:
            if not self.lmstudio.is_running():
                self.lmstudio.start()
            results["lmstudio"] = self.lmstudio.is_running()
        
        return results

    def start_all(self) -> dict:
        """Start all available services."""
        return self.ensure_services(["ollama", "lmstudio"])
