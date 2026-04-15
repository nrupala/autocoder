"""
Self-Learning Layer
Recursively improves from feedback and patterns
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict


logger = logging.getLogger(__name__)


@dataclass
class LearningEpisode:
    prompt: str
    response: str
    feedback: str
    improved_response: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    iterations: int = 1
    
    def to_dict(self) -> dict:
        return asdict(self)


class SelfLearner:
    """Learns from feedback to improve responses"""
    
    def __init__(self, memory_path: str = None):
        self.memory_path = Path(memory_path) if memory_path else Path("~/.autocoder/learn").expanduser()
        self.memory_path.mkdir(parents=True, exist_ok=True)
        
        self.episodes: List[LearningEpisode] = []
        self.improvements: Dict[str, str] = {}  # prompt_pattern -> improved_template
        self._load_improvements()
        
    def _load_improvements(self):
        """Load saved improvements"""
        for f in self.memory_path.glob("improvement_*.json"):
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    key = data.get("prompt_pattern", "")
                    if key:
                        self.improvements[key] = data.get("improved_response", "")
            except:
                pass
                
    def learn(self, prompt: str, response: str, feedback: str) -> LearningEpisode:
        """Learn from feedback"""
        episode = LearningEpisode(prompt=prompt, response=response, feedback=feedback)
        
        # Extract prompt pattern
        pattern = self._extract_pattern(prompt)
        
        # Try to improve
        improved = self._generate_improved(prompt, response, feedback)
        if improved and improved != response:
            episode.improved_response = improved
            episode.iterations = 2
            
            # Save improvement
            self.improvements[pattern] = improved
            self._save_improvement(pattern, improved, prompt)
            
        self.episodes.append(episode)
        return episode
    
    def _extract_pattern(self, prompt: str) -> str:
        """Extract key pattern from prompt"""
        prompt = prompt.lower()
        patterns = {
            "fastapi": "fastapi",
            "test": "pytest", 
            "docker": "docker",
            "class": "class",
            "function": "function",
            "algorithm": "algorithm",
            "api": "api",
        }
        for k, v in patterns.items():
            if k in prompt:
                return v
        return prompt[:30]
    
    def _generate_improved(self, prompt: str, original: str, feedback: str) -> Optional[str]:
        """Generate improved response based on feedback"""
        # Simple improvement rules
        feedback_lower = feedback.lower()
        
        # Extract what to improve
        if "short" in feedback_lower or "more" in feedback_lower:
            # Add more detail
            lines = original.split('\n')
            if len(lines) < 10:
                return original + "\n# TODO: Add more implementation details"
                
        if "error" in feedback_lower:
            # Add error handling
            if "try:" not in original:
                return "try:\n    " + original.replace("\n", "\n    ") + "\nexcept Exception as e:\n    print(f'Error: {e}')"
                
        if "test" in feedback_lower or "fail" in feedback_lower:
            # Add basic test
            if "def test_" not in original:
                return original + "\n\ndef test_basic():\n    assert True"
                
        return None
    
    def _save_improvement(self, pattern: str, improved: str, original_prompt: str):
        """Save improvement to disk"""
        path = self.memory_path / f"improvement_{pattern}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(path, 'w') as f:
            json.dump({
                "prompt_pattern": pattern,
                "original_prompt": original_prompt,
                "improved_response": improved,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
    
    def get_stats(self) -> dict:
        """Get learning statistics"""
        return {
            "total_episodes": len(self.episodes),
            "improvements_learned": len(self.improvements),
            "patterns": list(self.improvements.keys())
        }
    
    def get_improvement(self, prompt: str) -> Optional[str]:
        """Get improvement for prompt pattern"""
        pattern = self._extract_pattern(prompt)
        return self.improvements.get(pattern)


def get_learner() -> SelfLearner:
    global _learner
    if _learner is None:
        _learner = SelfLearner()
    return _learner


_learner = None