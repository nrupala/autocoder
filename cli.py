"""
AutoCoder - Complete CLI with all integrations
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

os.environ.setdefault('AUTOCODER_PATH', str(Path(__file__).parent))

from core.nl_processor import IntentParser, ParsedIntent
from core.hardware import HardwareDetector, ExecutionConfig
from models.orchestrator import ModelOrchestrator, OllamaClient
from models.cache import LLMCache, ModelConfig
from memory.store import AutoCoderMemory
from security.key_store import KeyStore, AuditLog
from tools import ToolRegistry
from tools.process_manager import ServiceOrchestrator
from tools.ide_integration import IDEOrchestrator
import sys
import os

# Ensure UTF-8 encoding for output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from engine import get_engine

__version__ = "0.1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


BANNER = """
===============================================
           AUTOCODER
   Universal Autonomous Coding Agent
===============================================
"""


class AutoCoderEngine:
    """Main AutoCoder engine with all integrations."""

    def __init__(self):
        logger.info("Initializing AutoCoder Engine...")
        
        self.hardware = HardwareDetector()
        self.config = self.hardware.get_execution_config()
        self.orchestrator = ModelOrchestrator()
        self.intent_parser = IntentParser()
        self.tools = ToolRegistry()
        self.memory = AutoCoderMemory()
        self.key_store = KeyStore()
        self.audit = AuditLog()
        self.cache = LLMCache()
        self.model_config = ModelConfig()
        self.services = ServiceOrchestrator()
        self.ide = IDEOrchestrator()

    def process(self, user_input: str, use_cache: bool = True) -> dict:
        logger.info(f"Processing: {user_input}")
        self.audit.add_entry("process_start", {"input": user_input[:100]})

        if use_cache:
            cached = self.cache.get(self.config.model, user_input)
            if cached:
                logger.info("Using cached response")
                return {"status": "success", "code": cached, "cached": True}

        intent = self.intent_parser.parse(user_input)
        logger.info(f"  Intent: {intent.intent}, Language: {intent.entities.get('language')}")

        handlers = {
            "create": self._handle_code_generation,
            "modify": self._handle_code_generation,
            "explain": self._handle_explain,
            "search": self._handle_search,
            "test": self._handle_test,
            "run": self._handle_run,
            "debug": self._handle_debug,
        }

        handler = handlers.get(intent.intent, self._handle_general)
        result = handler(user_input, intent)

        if use_cache and result.get("code"):
            self.cache.put(self.config.model, user_input, result["code"])

        return result

    def _handle_code_generation(self, user_input: str, intent: ParsedIntent) -> dict:
        language = intent.entities.get("language", "python")
        framework = intent.entities.get("framework", "")
        
        prompt = self._build_code_prompt(user_input, language, framework)
        code = self.orchestrator.generate(prompt, provider="ollama")
        
        self.memory.store_interaction(user_input, ["generate_code"], code)
        self.audit.add_entry("code_generated", {"language": language})
        
        return {
            "status": "success",
            "intent": intent.intent,
            "language": language,
            "framework": framework,
            "code": code,
            "model_used": self.config.model
        }

    def _build_code_prompt(self, description: str, language: str, framework: str) -> str:
        return f"""You are AutoCoder, an expert programmer. Generate high-quality, production-ready code.

Requirements:
1. Write clean, well-structured code following best practices
2. Include proper error handling and validation
3. Add docstrings and comments
4. Follow {language} style guide
5. Include unit tests where appropriate
6. Use modern patterns

Task: {description}

Language: {language}
Framework: {framework or 'none'}

Generate complete, working code:"""

    def _handle_explain(self, user_input: str, intent: ParsedIntent) -> dict:
        query = user_input.replace("explain", "").replace("how does", "").strip()
        
        prompt = f"""Explain this code/concept clearly:

{query}

Provide:
1. What it does (brief)
2. How it works (step-by-step)
3. Why designed this way
4. Important considerations"""

        explanation = self.orchestrator.generate(prompt, provider="ollama")
        
        return {"status": "success", "explanation": explanation}

    def _handle_search(self, user_input: str, intent: ParsedIntent) -> dict:
        query = user_input.replace("find", "").replace("search", "").replace("look for", "").strip()
        
        results = self.tools.execute("web_search", query=query, num_results=5)
        
        return {"status": "success", "results": results}

    def _handle_test(self, user_input: str, intent: ParsedIntent) -> dict:
        language = intent.entities.get("language", "python")
        
        prompt = f"""Generate comprehensive unit tests:

{user_input}

Language: {language}

Generate tests:"""
        
        tests = self.orchestrator.generate(prompt, provider="ollama")
        
        return {"status": "success", "tests": tests, "language": language}

    def _handle_run(self, user_input: str, intent: ParsedIntent) -> dict:
        cmd = user_input.replace("run", "").replace("execute", "").strip()
        
        result = self.tools.execute("run_command", cmd=cmd)
        
        return {
            "status": "success" if result.get("success") else "error",
            "output": result.get("stdout", ""),
            "errors": result.get("stderr", ""),
            "returncode": result.get("returncode", -1)
        }

    def _handle_debug(self, user_input: str, intent: ParsedIntent) -> dict:
        prompt = f"""Debug and fix this issue:

{user_input}

Provide:
1. Root cause
2. The fix (with code)
3. Prevention"""

        diagnosis = self.orchestrator.generate(prompt, provider="ollama")
        
        return {"status": "success", "diagnosis": diagnosis}

    def _handle_general(self, user_input: str, intent: ParsedIntent) -> dict:
        response = self.orchestrator.generate(
            f"You are AutoCoder. {user_input}",
            provider="ollama"
        )
        
        return {"status": "success", "response": response}

    def status(self) -> dict:
        return {
            "version": __version__,
            "hardware": {
                "gpu": self.hardware.profile.gpu_name if self.hardware.profile.has_cuda else "CPU only",
                "cpu_cores": self.hardware.profile.cpu_count,
                "ram_gb": self.hardware.profile.ram_total / (1024**3)
            },
            "config": {
                "model": self.config.model,
                "quantization": self.config.model_quantization,
                "batch_size": self.config.batch_size
            },
            "services": self.services.check_all_services(),
            "cache": self.cache.get_stats()
        }


def run_autocoder(description: str, lang: str = None, model: str = None):
    print(BANNER)
    print(f"Generating code for: {description}\n")
    
    from engine import get_engine
    engine = get_engine()
    
    result = engine.generate(description, model=model or "template")
    
    print("\n" + "="*60)
    print("GENERATED CODE:")
    print("="*60)
    print(result)
    print("="*60)
    
    return result
    
def run_chat():
    """Interactive chat mode."""
    print(BANNER)
    print("AutoCoder Chat Mode")
    print("Type 'exit' to quit, 'status' for info\n")
    
    engine = AutoCoderEngine()
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            if user_input.lower() == "status":
                print(json.dumps(engine.status(), indent=2))
                continue
            if user_input.lower() == "clear":
                print("\n" * 50 + BANNER)
                continue
            
            result = engine.process(user_input)
            
            if result.get("code"):
                print(f"\nAutoCoder:\n{result['code']}")
            elif result.get("explanation"):
                print(f"\nAutoCoder:\n{result['explanation']}")
            else:
                print(f"\nAutoCoder: {result}")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        prog="autocoder",
        description="AutoCoder - Universal Autonomous Coding Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    sub = parser.add_subparsers(dest="command", required=False)
    
    p_gen = sub.add_parser("generate", help="Generate code from NL")
    p_gen.add_argument("description", nargs="+", help="Description of what to generate")
    p_gen.add_argument("--lang", "-l", default=None)
    p_gen.add_argument("--model", "-m", default=None)
    
    sub.add_parser("chat", help="Interactive chat mode")
    sub.add_parser("status", help="Show engine status")
    sub.add_parser("models", help="List available models")
    sub.add_parser("services", help="Check services status")
    sub.add_parser("daemon", help="Start daemon server")
    
    p_create = sub.add_parser("create", help="Create new project")
    p_create.add_argument("name", nargs="?", default="new-project")
    
    p_keys = sub.add_parser("keys", help="Key management")
    p_keys.add_argument("action", choices=["create", "list"])
    p_keys.add_argument("name", nargs="?", default=None)
    
    sub.add_parser("audit", help="Show audit log")
    sub.add_parser("cache", help="Show cache stats")
    sub.add_parser("help", help="Show help")
    
    parser.add_argument("--version", action="store_true")
    parser.add_argument("description", nargs=argparse.REMAINDER)

    args = parser.parse_args()

    if args.version:
        print(f"AutoCoder v{__version__}")
        return

    if not args.command and args.description:
        desc = " ".join(args.description)
        run_autocoder(desc, getattr(args, 'lang', None), getattr(args, 'model', None))
        return

    if args.command == "generate":
        desc = " ".join(args.description) if isinstance(args.description, list) else args.description
        run_autocoder(desc, args.lang, args.model)
    elif args.command == "chat":
        run_chat()
    elif args.command == "status":
        engine = AutoCoderEngine()
        print(json.dumps(engine.status(), indent=2))
    elif args.command == "models":
        try:
            import requests
            resp = requests.get("http://localhost:11434/api/tags", timeout=5)
            models = resp.json().get("models", [])
            for m in models:
                print(f"  {m['name']}")
        except Exception as e:
            print(f"Ollama not available: {e}")
    elif args.command == "services":
        engine = AutoCoderEngine()
        print(json.dumps(engine.services.check_all_services(), indent=2))
    elif args.command == "keys":
        ks = KeyStore()
        if args.action == "create" and args.name:
            kp = ks.create_key(args.name, "autocoder-default")
            print(f"Created key: {args.name} (ID: {kp.key_id})")
        elif args.action == "list":
            print("Keys:", list(ks.store_dir.glob("*.key")) if ks.store_dir.exists() else "None")
    elif args.command == "audit":
        audit = AuditLog()
        for e in audit.get_entries(10):
            print(f"{e.timestamp}: {e.action}")
    elif args.command == "cache":
        cache = LLMCache()
        print(json.dumps(cache.get_stats(), indent=2))
    elif args.command == "daemon":
        from daemon import AutoCoderDaemon
        daemon = AutoCoderDaemon()
        daemon.start_server()
    elif args.command == "create":
        from daemon import AutoCoderDaemon
        parts = args.name.split(":") if args.name else ["new-project", ".", "python"]
        name = parts[0] if len(parts) > 0 else "new-project"
        path = parts[1] if len(parts) > 1 else "."
        lang = parts[2] if len(parts) > 2 else "python"
        daemon = AutoCoderDaemon()
        success = daemon.create_project(name, path, lang)
        print(f"Created project: {name} at {path}" if success else "Failed to create project")
    else:
        print(BANNER)
        print("""
Usage: autocoder <command> [options]

Commands:
  generate <desc>   Generate code from description
  chat              Interactive chat mode
  status            Show engine status
  models            List available models
  services          Check services
  keys create <n>  Create signing key
  keys list         List keys
  audit             Show audit log
  cache             Show cache stats
  help              Show this help

Examples:
  autocoder "create a FastAPI for user auth"
  autocoder chat
  autocoder models
        """)


if __name__ == "__main__":
    main()
