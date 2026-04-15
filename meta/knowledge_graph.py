"""
Knowledge Graph
User-visualizable memory of concepts and relationships
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class Concept:
    id: str
    name: str
    type: str  # code, concept, pattern, tool, language
    description: str
    connections: List[str] = field(default_factory=list)
    usage_count: int = 0
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return asdict(self)


class KnowledgeGraph:
    """Knowledge graph for visualization"""
    
    def __init__(self, memory_path: str = None):
        self.memory_path = Path(memory_path) if memory_path else Path("~/.autocoder/knowledge").expanduser()
        self.memory_path.mkdir(parents=True, exist_ok=True)
        
        self.concepts: Dict[str, Concept] = {}
        self.adjacency: Dict[str, Set[str]] = {}
        
        self._load_concepts()
        
    def _load_concepts(self):
        """Load saved concepts"""
        for f in self.memory_path.glob("concept_*.json"):
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    concept = Concept(**data)
                    self.concepts[concept.id] = concept
                    self.adjacency[concept.id] = set(concept.connections)
            except:
                pass
        logger.info(f"Loaded {len(self.concepts)} concepts")
    
    def add_concept(self, name: str, concept_type: str, description: str = "", connections: List[str] = None) -> Concept:
        """Add or update concept"""
        concept_id = name.lower().replace(" ", "_")
        
        if concept_id in self.concepts:
            concept = self.concepts[concept_id]
            concept.usage_count += 1
            concept.last_seen = datetime.now().isoformat()
            if connections:
                for c in connections:
                    self._connect(concept_id, c)
        else:
            concept = Concept(
                id=concept_id,
                name=name,
                type=concept_type,
                description=description,
                connections=connections or []
            )
            self.concepts[concept_id] = concept
            self.adjacency[concept_id] = set(connections or [])
            
            # Save to disk
            self._save_concept(concept)
            
        return concept
    
    def _connect(self, from_id: str, to_id: str):
        """Create connection between concepts"""
        if from_id not in self.adjacency:
            self.adjacency[from_id] = set()
        self.adjacency[from_id].add(to_id)
        
        # Update concept connections
        if from_id in self.concepts:
            self.concepts[from_id].connections = list(self.adjacency[from_id])
    
    def _save_concept(self, concept: Concept):
        """Save concept to disk"""
        path = self.memory_path / f"concept_{concept.id}.json"
        with open(path, 'w') as f:
            json.dump(concept.to_dict(), f, indent=2)
    
    def infer_from_prompt(self, prompt: str):
        """Infer concepts from prompt"""
        prompt_lower = prompt.lower()
        
        # Language concepts
        languages = {
            "python": ("Python", "language"),
            "javascript": ("JavaScript", "language"),
            "typescript": ("TypeScript", "language"),
            "go": ("Go", "language"),
            "rust": ("Rust", "language"),
        }
        for kw, (name, ctype) in languages.items():
            if kw in prompt_lower:
                self.add_concept(name, ctype, f"Programming language: {name}")
        
        # Framework concepts
        frameworks = {
            "fastapi": ("FastAPI", "framework"),
            "flask": ("Flask", "framework"),
            "django": ("Django", "framework"),
            "react": ("React", "framework"),
            "express": ("Express", "framework"),
        }
        for kw, (name, ctype) in frameworks.items():
            if kw in prompt_lower:
                self.add_concept(name, ctype, f"Web framework: {name}")
        
        # Pattern concepts
        patterns = {
            "api": ("REST API", "pattern"),
            "class": ("OOP", "pattern"),
            "function": ("Functional", "pattern"),
            "test": ("Testing", "pattern"),
            "docker": ("Docker", "tool"),
        }
        for kw, (name, ctype) in patterns.items():
            if kw in prompt_lower:
                self.add_concept(name, ctype, f"Code pattern: {name}")
        
        # Connect inferred concepts
        self._infer_connections(prompt_lower)
    
    def _infer_connections(self, prompt: str):
        """Infer and create connections"""
        known_groups = [
            ["python", "fastapi"],
            ["python", "test", "pytest"],
            ["javascript", "react"],
            ["docker", "fastapi"],
            ["python", "class"],
        ]
        
        for group in known_groups:
            present = [c for c in group if c in prompt]
            if len(present) >= 2:
                for i in range(len(present) - 1):
                    from_id = present[i].lower().replace(" ", "_")
                    to_id = present[i+1].lower().replace(" ", "_")
                    if from_id in self.concepts and to_id in self.concepts:
                        self._connect(from_id, to_id)
    
    def get_stats(self) -> dict:
        """Get statistics"""
        types = {}
        for c in self.concepts.values():
            types[c.type] = types.get(c.type, 0) + 1
            
        return {
            "total_concepts": len(self.concepts),
            "by_type": types,
            "total_connections": sum(len(s) for s in self.adjacency.values()),
        }
    
    def get_network(self) -> Dict:
        """Get network for visualization (nodes + edges)"""
        nodes = []
        edges = []
        
        for c in self.concepts.values():
            nodes.append({
                "id": c.id,
                "label": c.name,
                "type": c.type,
                "usage": c.usage_count
            })
        
        for from_id, connections in self.adjacency.items():
            for to_id in connections:
                edges.append({"from": from_id, "to": to_id})
        
        return {"nodes": nodes, "edges": edges}
    
    def export_d3_json(self, path: str = None) -> str:
        """Export for D3.js visualization"""
        path = path or str(self.memory_path / "graph_d3.json")
        network = self.get_network()
        
        with open(path, 'w') as f:
            json.dump(network, f, indent=2)
        return path
    
    def search(self, query: str) -> List[Concept]:
        """Search concepts"""
        query_lower = query.lower()
        return [c for c in self.concepts.values() 
                if query_lower in c.name.lower() or query_lower in c.description.lower()]


def get_knowledge_graph() -> KnowledgeGraph:
    global _kg
    if _kg is None:
        _kg = KnowledgeGraph()
    return _kg


_kg = None