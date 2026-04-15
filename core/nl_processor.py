"""
AutoCoder Core - Natural Language Processor
"""

from dataclasses import dataclass
from typing import Any

INTENT_PATTERNS = {
    "create": ["create", "implement", "build", "make", "add", "new", "write"],
    "modify": ["fix", "update", "change", "modify", "edit", "refactor", "patch"],
    "explain": ["explain", "describe", "how", "what does", "why", "tell me"],
    "delete": ["delete", "remove", "cleanup", "drop"],
    "search": ["find", "search", "look for", "grep", "locate"],
    "test": ["test", "spec", "verify", "check"],
    "run": ["run", "execute", "start", "launch"],
    "debug": ["debug", "trace", "inspect", "diagnose"],
}

LANGUAGE_KEYWORDS = {
    "python": ["python", "py", "fastapi", "flask", "django", "pandas", "pytest"],
    "javascript": ["javascript", "js", "node", "react", "vue", "express", "npm"],
    "typescript": ["typescript", "ts", "tsx", "angular"],
    "rust": ["rust", "rs", "cargo", "wasm"],
    "go": ["go", "golang", "gin"],
    "java": ["java", "spring", "maven", "gradle"],
    "c": ["c", "clang"],
    "cpp": ["c++", "cpp", "cxx", "stl"],
    "csharp": ["c#", "csharp", ".net", "dotnet"],
    "swift": ["swift", "ios", "xcode"],
    "kotlin": ["kotlin", "android", "gradle"],
    "ruby": ["ruby", "rails"],
    "php": ["php", "laravel", "symfony"],
    "sql": ["sql", "postgres", "mysql", "mongodb", "redis"],
    "html": ["html", "css", "tailwind", "bootstrap"],
    "shell": ["bash", "sh", "shell", "powershell"],
}


@dataclass
class ParsedIntent:
    intent: str
    entities: dict[str, Any]
    context: dict[str, Any]
    sentiment: str
    raw_input: str


class IntentParser:
    """Parses natural language into actionable intents."""

    def __init__(self):
        self.context_history: list[dict] = []

    def parse(self, user_input: str) -> ParsedIntent:
        text = user_input.lower()

        intent = self._classify_intent(text)
        language = self._detect_language(text)
        entities = {"language": language}

        self._extract_framework(text, entities)
        self._extract_api_type(text, entities)
        self._extract_requirements(text, entities)

        return ParsedIntent(
            intent=intent,
            entities=entities,
            context={"history": self.context_history[-5:]},
            sentiment=self._analyze_sentiment(text),
            raw_input=user_input
        )

    def _classify_intent(self, text: str) -> str:
        for intent_name, keywords in INTENT_PATTERNS.items():
            if any(kw in text for kw in keywords):
                return intent_name
        return "general"

    def _detect_language(self, text: str) -> str:
        for lang, keywords in LANGUAGE_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return lang
        return "python"

    def _extract_framework(self, text: str, entities: dict):
        frameworks = {
            "fastapi": "fastapi", "flask": "flask", "django": "django",
            "react": "react", "vue": "vue", "angular": "angular", "next": "nextjs",
            "express": "express", "spring": "spring", "gin": "gin",
            "rails": "rails", "laravel": "laravel", "nextjs": "nextjs"
        }
        for fw in frameworks:
            if fw in text:
                entities["framework"] = frameworks[fw]
                return

    def _extract_api_type(self, text: str, entities: dict):
        if "api" in text or "rest" in text or "endpoint" in text:
            entities["api_type"] = "rest"
        if "grpc" in text:
            entities["api_type"] = "grpc"
        if "graphql" in text:
            entities["api_type"] = "graphql"
        if "websocket" in text:
            entities["api_type"] = "websocket"

    def _extract_requirements(self, text: str, entities: dict):
        entities["needs_tests"] = "test" in text
        entities["needs_docs"] = "document" in text or "readme" in text
        entities["needs_verification"] = "verify" in text or "proof" in text
        entities["needs_docker"] = "docker" in text or "container" in text
        entities["needs_ci"] = "ci" in text or "github action" in text

    def _analyze_sentiment(self, text: str) -> str:
        if any(w in text for w in ["please", "could", "would", "thanks", "thank"]):
            return "polite"
        if any(w in text for w in ["urgent", "asap", "quickly", "now"]):
            return "urgent"
        return "neutral"

    def add_to_history(self, intent: ParsedIntent):
        self.context_history.append({
            "intent": intent.intent,
            "language": intent.entities.get("language"),
            "timestamp": __import__("time").time()
        })
        if len(self.context_history) > 50:
            self.context_history = self.context_history[-50:]
