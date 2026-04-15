"""
AutoCoder Test Suite
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.nl_processor import IntentParser, INTENT_PATTERNS, LANGUAGE_KEYWORDS
from core.hardware import HardwareDetector, ExecutionConfig
from models.orchestrator import OllamaClient, ModelOrchestrator


class TestIntentParser:
    """Test intent parsing."""

    def test_parse_create_intent(self):
        parser = IntentParser()
        result = parser.parse("create a Python FastAPI for user authentication")
        
        assert result.intent == "create"
        assert result.entities["language"] == "python"
        assert result.entities["framework"] == "fastapi"

    def test_parse_modify_intent(self):
        parser = IntentParser()
        result = parser.parse("fix the bug in src/auth.py")
        
        assert result.intent == "fix" or result.intent == "modify"

    def test_parse_explain_intent(self):
        parser = IntentParser()
        result = parser.parse("explain how binary search works")
        
        assert result.intent == "explain"

    def test_detect_language_python(self):
        parser = IntentParser()
        result = parser.parse("build a django app")
        
        assert result.entities["language"] == "python"

    def test_detect_language_javascript(self):
        parser = IntentParser()
        result = parser.parse("create a react component")
        
        assert result.entities["language"] == "javascript"

    def test_detect_language_rust(self):
        parser = IntentParser()
        result = parser.parse("write a rust program with cargo")
        
        assert result.entities["language"] == "rust"

    def test_detect_framework(self):
        parser = IntentParser()
        result = parser.parse("create a flask api")
        
        assert result.entities.get("framework") == "flask"

    def test_needs_tests(self):
        parser = IntentParser()
        result = parser.parse("create a function with tests")
        
        assert result.entities.get("needs_tests") == True

    def test_needs_docs(self):
        parser = IntentParser()
        result = parser.parse("create an endpoint with documentation")
        
        assert result.entities.get("needs_docs") == True

    def test_api_type_detection(self):
        parser = IntentParser()
        result = parser.parse("create a rest api endpoint")
        
        assert result.entities.get("api_type") == "rest"


class TestHardwareDetector:
    """Test hardware detection."""

    def test_hardware_detector_init(self):
        detector = HardwareDetector()
        
        assert detector.profile is not None
        assert detector.profile.cpu_count >= 1

    def test_execution_config_gpu(self):
        detector = HardwareDetector()
        config = detector.get_execution_config()
        
        assert isinstance(config, ExecutionConfig)
        assert config.model is not None
        assert config.batch_size >= 1

    def test_execution_config_cpu_only(self):
        detector = HardwareDetector()
        
        if not detector.profile.has_cuda:
            config = detector.get_execution_config()
            assert config.use_gpu == False


class TestOllamaClient:
    """Test Ollama client."""

    def test_ollama_init(self):
        client = OllamaClient()
        
        assert client.model == "deepseek-coder:14b"
        assert client.base_url == "http://localhost:11434"

    def test_ollama_is_available(self):
        client = OllamaClient()
        
        is_available = client.is_available()
        
        assert isinstance(is_available, bool)

    def test_ollama_list_models(self):
        client = OllamaClient()
        
        models = client.list_models()
        
        assert isinstance(models, list)


class TestModelOrchestrator:
    """Test model orchestrator."""

    def test_orchestrator_init(self):
        orchestrator = ModelOrchestrator()
        
        assert orchestrator.default_model is not None
        assert "ollama" in orchestrator.clients
        assert "openai" in orchestrator.clients
        assert "anthropic" in orchestrator.clients

    def test_select_model_code_generation(self):
        orchestrator = ModelOrchestrator()
        
        model = orchestrator.select_model("code_generation", use_gpu=True)
        
        assert model is not None
        assert isinstance(model, str)

    def test_select_model_natural_response(self):
        orchestrator = ModelOrchestrator()
        
        model = orchestrator.select_model("natural_response", use_gpu=False)
        
        assert model is not None


class TestSecurity:
    """Test security layer."""

    def test_key_store_init(self):
        from security.key_store import KeyStore
        
        ks = KeyStore(store_dir=".autocoder/test_keys")
        
        assert ks.store_dir is not None

    def test_audit_log_init(self):
        from security.key_store import AuditLog
        
        audit = AuditLog(log_file=".autocoder/test_audit.log")
        
        assert audit.log_file is not None

    def test_rate_limiter(self):
        from security.key_store import RateLimiter
        
        limiter = RateLimiter(max_calls=5, window_seconds=60)
        
        assert limiter.is_allowed("test_user") == True
        assert limiter.is_allowed("test_user") == True


class TestMemory:
    """Test memory system."""

    def test_episodic_memory_init(self):
        from memory.store import EpisodicMemory
        
        memory = EpisodicMemory(base_path=".autocoder/test_memory")
        
        assert memory.base_path is not None

    def test_knowledge_graph_init(self):
        from memory.store import KnowledgeGraph
        
        kg = KnowledgeGraph(base_path=".autocoder/test_memory")
        
        assert kg.base_path is not None

    def test_pdca_learner(self):
        from memory.store import PDCALearner
        
        learner = PDCALearner()
        
        plan = learner.plan("test task", "test approach")
        assert plan["task"] == "test task"
        
        learner.do("step 1", "result 1")
        assert len(learner.current_plan["steps"]) == 1
        
        check = learner.check(True, {"accuracy": 0.95})
        assert check["success"] == True


class TestTools:
    """Test tool registry."""

    def test_tool_registry_init(self):
        from tools import ToolRegistry
        
        registry = ToolRegistry()
        
        assert registry.fs is not None
        assert registry.code is not None
        assert registry.exec is not None

    def test_list_tools(self):
        from tools import ToolRegistry
        
        registry = ToolRegistry()
        tools = registry.list_tools()
        
        assert len(tools) > 0
        assert any(t["name"] == "read_file" for t in tools)
        assert any(t["name"] == "write_file" for t in tools)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
