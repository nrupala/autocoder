"""
AutoCoder Tools - File system and code operations
"""

import os
import subprocess
import shlex
from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class FileSystemTool:
    """File system operations."""

    @staticmethod
    def read_file(path: str, limit: int = None, offset: int = None) -> str:
        p = Path(path)
        if not p.exists():
            return f"Error: File not found: {path}"
        try:
            content = p.read_text(encoding="utf-8")
            if offset:
                lines = content.split("\n")
                content = "\n".join(lines[offset:])
            if limit:
                lines = content.split("\n")
                content = "\n".join(lines[:limit])
            return content
        except Exception as e:
            return f"Error reading file: {e}"

    @staticmethod
    def write_file(path: str, content: str, mode: str = "w") -> str:
        p = Path(path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"Written to {path}"
        except Exception as e:
            return f"Error writing file: {e}"

    @staticmethod
    def list_dir(path: str = ".") -> str:
        p = Path(path)
        if not p.exists():
            return f"Error: Directory not found: {path}"
        if not p.is_dir():
            return f"Error: Not a directory: {path}"
        
        items = []
        for item in sorted(p.iterdir()):
            size = item.stat().st_size if item.is_file() else 0
            items.append(f"{'d' if item.is_dir() else 'f'} {size:>10} {item.name}")
        return "\n".join(items)

    @staticmethod
    def glob(pattern: str, path: str = ".") -> list[str]:
        from glob import glob as _glob
        results = _glob(os.path.join(path, pattern))
        return results

    @staticmethod
    def grep(pattern: str, path: str = ".", include: str = "*") -> list[dict]:
        import re
        results = []
        path_obj = Path(path)
        
        for file_path in path_obj.rglob(include):
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(content.split("\n"), 1):
                    if re.search(pattern, line):
                        results.append({
                            "file": str(file_path),
                            "line": i,
                            "content": line.strip()
                        })
            except:
                pass
        return results


class CodeTool:
    """Code manipulation tools."""

    LANG_EXTENSIONS = {
        "python": ".py",
        "javascript": ".js",
        "typescript": ".ts",
        "rust": ".rs",
        "go": ".go",
        "java": ".java",
        "c": ".c",
        "cpp": ".cpp",
        "csharp": ".cs",
        "swift": ".swift",
        "kotlin": ".kt",
        "ruby": ".rb",
        "php": ".php",
        "html": ".html",
        "css": ".css",
    }

    @staticmethod
    def format_code(path: str, language: str = None) -> str:
        if not language:
            language = CodeTool._detect_language(path)
        
        try:
            if language == "python":
                result = subprocess.run(["black", path], capture_output=True, text=True)
                return result.stdout or "Formatted with black"
            elif language == "javascript" or language == "typescript":
                result = subprocess.run(["prettier", "--write", path], capture_output=True, text=True)
                return result.stdout or "Formatted with prettier"
            elif language == "rust":
                result = subprocess.run(["rustfmt", path], capture_output=True, text=True)
                return result.stdout or "Formatted with rustfmt"
            else:
                return f"No formatter available for {language}"
        except FileNotFoundError:
            return f"Formatter not installed for {language}"
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def lint_code(path: str, language: str = None) -> dict:
        if not language:
            language = CodeTool._detect_language(path)
        
        try:
            if language == "python":
                result = subprocess.run(
                    ["flake8", path, "--max-line-length=100"],
                    capture_output=True, text=True
                )
                return {"errors": result.stdout.split("\n"), "warnings": result.stderr.split("\n")}
            elif language == "javascript" or language == "typescript":
                result = subprocess.run(
                    ["eslint", path],
                    capture_output=True, text=True
                )
                return {"errors": result.stdout.split("\n")}
            else:
                return {"errors": [], "message": f"No linter for {language}"}
        except FileNotFoundError:
            return {"errors": [], "message": f"Linter not installed for {language}"}
        except Exception as e:
            return {"errors": [], "message": str(e)}

    @staticmethod
    def _detect_language(path: str) -> str:
        ext = Path(path).suffix.lower()
        for lang, extension in CodeTool.LANG_EXTENSIONS.items():
            if extension == ext:
                return lang
        return "unknown"

    @staticmethod
    def get_file_info(path: str) -> dict:
        p = Path(path)
        if not p.exists():
            return {"error": "File not found"}
        
        stat = p.stat()
        return {
            "path": str(p.absolute()),
            "name": p.name,
            "size": stat.st_size,
            "language": CodeTool._detect_language(path),
            "modified": stat.st_mtime,
        }


class ExecutionTool:
    """Shell command execution."""

    @staticmethod
    def run_command(cmd: str, timeout: int = 120, cwd: str = None) -> dict:
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def run_tests(path: str, framework: str = "pytest", verbose: bool = True) -> dict:
        cmd = {
            "pytest": f'pytest {path} {"-v" if verbose else ""}',
            "jest": f'npm test -- {path}',
            "go test": f'go test {path}',
            "cargo test": f'cargo test --manifest-path {Path(path).parent / "Cargo.toml"}',
            "npm test": f'npm test {path}',
            "dotnet test": f'dotnet test {path}',
        }.get(framework, f'{framework} {path}')
        
        return ExecutionTool.run_command(cmd, timeout=180)

    @staticmethod
    def install_dependencies(language: str, path: str = ".") -> dict:
        commands = {
            "python": "pip install -r requirements.txt",
            "javascript": "npm install",
            "rust": "cargo build",
            "go": "go mod download",
            "java": "mvn compile",
        }
        cmd = commands.get(language, "")
        if not cmd:
            return {"success": False, "error": f"Unknown language: {language}"}
        
        return ExecutionTool.run_command(cmd, cwd=path)


class WebTool:
    """Web search and fetch tools."""

    @staticmethod
    def search(query: str, num_results: int = 5) -> list[dict]:
        try:
            from exa_py import Exa
            exa = Exa(os.environ.get("EXA_API_KEY", ""))
            results = exa.search(query, num_results=num_results)
            return [{"title": r.title, "url": r.url, "text": r.text[:200]} for r in results]
        except ImportError:
            pass
        
        try:
            import requests
            params = {"q": query, "format": "json"}
            resp = requests.get("https://ddg-api.vercel.app/search", params=params, timeout=10)
            return resp.json()[:num_results]
        except:
            pass
        
        return [{"error": "No search engine available"}]

    @staticmethod
    def fetch_url(url: str) -> str:
        try:
            import requests
            resp = requests.get(url, timeout=30)
            return resp.text[:5000]
        except Exception as e:
            return f"Error fetching URL: {e}"


class ToolRegistry:
    """Central tool registry."""

    def __init__(self):
        self.fs = FileSystemTool()
        self.code = CodeTool()
        self.exec = ExecutionTool()
        self.web = WebTool()

    def execute(self, tool_name: str, **kwargs) -> Any:
        tool_map = {
            "read_file": self.fs.read_file,
            "write_file": self.fs.write_file,
            "list_dir": self.fs.list_dir,
            "glob": self.fs.glob,
            "grep": self.fs.grep,
            "format_code": self.code.format_code,
            "lint_code": self.code.lint_code,
            "run_command": self.exec.run_command,
            "run_tests": self.exec.run_tests,
            "web_search": self.web.search,
            "fetch_url": self.web.fetch_url,
        }
        
        if tool_name not in tool_map:
            return {"error": f"Unknown tool: {tool_name}"}
        
        return tool_map[tool_name](**kwargs)

    def list_tools(self) -> list[dict]:
        return [
            {"name": "read_file", "params": ["path"]},
            {"name": "write_file", "params": ["path", "content"]},
            {"name": "list_dir", "params": ["path"]},
            {"name": "glob", "params": ["pattern", "path"]},
            {"name": "grep", "params": ["pattern", "path", "include"]},
            {"name": "run_command", "params": ["cmd", "timeout"]},
            {"name": "run_tests", "params": ["path", "framework"]},
            {"name": "web_search", "params": ["query", "num_results"]},
            {"name": "fetch_url", "params": ["url"]},
        ]
