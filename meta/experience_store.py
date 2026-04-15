"""
Experience Store for RAG
Stores generations for retrieval on similar prompts
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class Experience:
    prompt: str
    response: str
    mode: str
    quality: float = 0.0
    tags: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    used_count: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)


class ExperienceStore:
    """Stores and retrieves experiences for RAG"""
    
    def __init__(self, memory_path: str = None):
        self.memory_path = Path(memory_path) if memory_path else Path("~/.autocoder/experiences").expanduser()
        self.memory_path.mkdir(parents=True, exist_ok=True)
        
        self.experiences: List[Experience] = []
        self._load_experiences()
        
    def _load_experiences(self):
        """Load saved experiences"""
        for f in self.memory_path.glob("experience_*.json"):
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    exp = Experience(**data)
                    self.experiences.append(exp)
            except:
                pass
        logger.info(f"Loaded {len(self.experiences)} experiences")
    
    def store(self, prompt: str, response: str, mode: str = "standard", quality: float = 0.5, tags: List[str] = None):
        """Store new experience"""
        tags = tags or self._extract_tags(prompt)
        exp = Experience(prompt=prompt, response=response, mode=mode, quality=quality, tags=tags)
        self.experiences.append(exp)
        
        # Save to disk
        path = self.memory_path / f"experience_{len(self.experiences)}.json"
        with open(path, 'w') as f:
            json.dump(exp.to_dict(), f, indent=2)
        
        return exp
    
    def _extract_tags(self, prompt: str) -> List[str]:
        """Extract tags from prompt"""
        prompt = prompt.lower()
        tags = []
        keywords = {
            "fastapi": "api", "flask": "api", "django": "api",
            "test": "testing", "pytest": "testing", "unittest": "testing",
            "docker": "devops", "dockerfile": "devops",
            "class": "oop", "function": "functional",
            "algorithm": "algorithm",
            "react": "frontend", "vue": "frontend",
            "database": "data", "sql": "data",
        }
        for kw, tag in keywords.items():
            if kw in prompt and tag not in tags:
                tags.append(tag)
        return tags if tags else ["general"]
    
    def retrieve(self, prompt: str, limit: int = 3) -> List[Experience]:
        """Retrieve similar experiences"""
        prompt_lower = prompt.lower()
        scored = []
        
        for exp in self.experiences:
            score = 0
            
            # Tag matching
            exp_tags = set(exp.tags)
            prompt_tags = set(self._extract_tags(prompt))
            score += len(exp_tags & prompt_tags) * 2
            
            # Keyword matching
            for kw in exp.prompt.lower().split():
                if kw in prompt_lower:
                    score += 1
            
            # Mode matching
            if exp.mode in prompt.lower():
                score += 1
                
            scored.append((score, exp))
        
        # Sort by score
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Update usage
        result = []
        for score, exp in scored[:limit]:
            exp.used_count += 1
            result.append(exp)
            
        return result
    
    def get_stats(self) -> dict:
        """Get statistics"""
        if not self.experiences:
            return {"total": 0}
            
        qualities = [e.quality for e in self.experiences]
        all_tags = []
        for e in self.experiences:
            all_tags.extend(e.tags)
        
        return {
            "total": len(self.experiences),
            "avg_quality": round(sum(qualities) / len(qualities), 3),
            "top_tags": list(set(all_tags))[:10],
            "most_used": max(self.experiences, key=lambda e: e.used_count).prompt[:50] if self.experiences else ""
        }
    
    def search(self, query: str, limit: int = 5) -> List[Experience]:
        """Full-text search"""
        query_lower = query.lower()
        results = [e for e in self.experiences if query_lower in e.prompt.lower() or query_lower in e.response.lower()]
        return results[:limit]
    
    def export_json(self, path: str = None) -> str:
        """Export all experiences as JSON"""
        path = path or str(self.memory_path / "all_experiences.json")
        with open(path, 'w') as f:
            json.dump([e.to_dict() for e in self.experiences], f, indent=2)
        return path


def get_experience_store() -> ExperienceStore:
    global _store
    if _store is None:
        _store = ExperienceStore()
    return _store


_store = None