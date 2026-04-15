"""
MetaCognition Layer
Monitors generation quality, patterns, and self-improvement
"""

import json
import time
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path


@dataclass
class GenerationSession:
    prompt: str
    mode: str
    response: str = ""
    quality_score: float = 0.0
    latency_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    feedback: Optional[str] = None
    improvements: List[str] = field(default_factory=list)
    token_count: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)


class MetaCognition:
    """Monitors and evaluates generation quality"""
    
    def __init__(self, memory_path: str = None):
        self.memory_path = Path(memory_path) if memory_path else Path("~/.autocoder/meta").expanduser()
        self.memory_path.mkdir(parents=True, exist_ok=True)
        
        self.sessions: List[GenerationSession] = []
        self.quality_history: List[float] = []
        self.patterns: Dict[str, int] = {}
        self.start_time = time.time()
        
    def start_session(self, prompt: str, mode: str) -> GenerationSession:
        return GenerationSession(prompt=prompt, mode=mode, timestamp=datetime.now().isoformat())
    
    def end_session(self, session: GenerationSession, response: str, latency_ms: float):
        session.response = response
        session.latency_ms = latency_ms
        session.token_count = len(response.split())
        
        # Evaluate quality
        session.quality_score = self._evaluate_quality(session)
        
        self.sessions.append(session)
        self.quality_history.append(session.quality_score)
        
        # Update patterns
        self._update_patterns(session.prompt)
        
        # Save
        self._save_session(session)
        
        return session.quality_score
    
    def _evaluate_quality(self, session: GenerationSession) -> float:
        """Evaluate response quality"""
        score = 0.5
        
        response = session.response
        prompt = session.prompt.lower()
        
        # Check for code structure
        if "def " in response or "class " in response or "import " in response:
            score += 0.1
        if "return " in response:
            score += 0.05
            
        # Check completeness based on prompt
        if "api" in prompt or "fastapi" in prompt:
            if "@app" in response or "def " in response:
                score += 0.1
        if "test" in prompt:
            if "def test_" in response or "assert " in response:
                score += 0.1
        if "docker" in prompt:
            if "FROM" in response and "CMD" in response:
                score += 0.1
                
        # Penalize empty/short responses
        if len(response) < 50:
            score -= 0.2
            
        # Penalize error indicators
        if "Error:" in response or "not found" in response.lower():
            score -= 0.15
            
        return max(0.0, min(1.0, score))
    
    def _update_patterns(self, prompt: str):
        """Track prompt patterns"""
        keywords = ["fastapi", "test", "docker", "react", "api", "class", "function", "algorithm"]
        for kw in keywords:
            if kw in prompt.lower():
                self.patterns[kw] = self.patterns.get(kw, 0) + 1
    
    def _save_session(self, session: GenerationSession):
        """Save session to disk"""
        path = self.memory_path / f"session_{session.timestamp.replace(':', '-')}.json"
        with open(path, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)
    
    def get_stats(self) -> dict:
        """Get statistics"""
        avg_quality = sum(self.quality_history) / len(self.quality_history) if self.quality_history else 0
        uptime = time.time() - self.start_time
        
        return {
            "total_generations": len(self.sessions),
            "avg_quality": round(avg_quality, 3),
            "patterns": self.patterns,
            "uptime_seconds": int(uptime),
            "sessions_today": len([s for s in self.sessions if s.timestamp.startswith(datetime.now().strftime("%Y-%m-%d"))])
        }
    
    def get_recent_patterns(self, limit: int = 5) -> List[tuple]:
        """Get most used patterns"""
        sorted_patterns = sorted(self.patterns.items(), key=lambda x: x[1], reverse=True)
        return sorted_patterns[:limit]


def get_meta() -> MetaCognition:
    global _meta
    if _meta is None:
        _meta = MetaCognition()
    return _meta


_meta = None