"""
Meta-Cognition Layer
=================
Self-learning, RAG-based experience, and knowledge graph
for recursive improvement of code generation.
"""

from .meta_cognition import MetaCognition, get_meta, GenerationSession
from .self_learner import SelfLearner, get_learner, LearningEpisode
from .experience_store import ExperienceStore, get_experience_store, Experience
from .knowledge_graph import KnowledgeGraph, get_knowledge_graph, Concept

__all__ = [
    "MetaCognition",
    "SelfLearner", 
    "ExperienceStore",
    "KnowledgeGraph",
    "get_meta",
    "get_learner",
    "get_experience_store",
    "get_knowledge_graph",
    "GenerationSession",
    "LearningEpisode",
    "Experience",
    "Concept",
]


def init_all():
    """Initialize all meta-cognition components"""
    meta = get_meta()
    learner = get_learner()
    store = get_experience_store()
    kg = get_knowledge_graph()
    
    return {
        "meta": meta,
        "learner": learner,
        "store": store,
        "kg": kg,
    }


def get_stats():
    """Get all stats"""
    return {
        "meta": get_meta().get_stats(),
        "learner": get_learner().get_stats(),
        "experience": get_experience_store().get_stats(),
        "knowledge": get_knowledge_graph().get_stats(),
    }


def integrated_generate(prompt: str, mode: str = "standard", **kwargs) -> str:
    """Generate with full meta-cognition integration"""
    import time
    from engine import generate as engine_generate
    
    start = time.time()
    
    # Get components
    meta = get_meta()
    learner = get_learner()
    store = get_experience_store()
    kg = get_knowledge_graph()
    
    # Start monitoring
    session = meta.start_session(prompt, mode)
    
    # Try retrieval from experiences (RAG)
    similar = store.retrieve(prompt)
    if similar and similar[0].quality > 0.7:
        # Use retrieved experience as base
        base_response = similar[0].response
        # Could blend with generation
    
    # Generate
    response = engine_generate(prompt, mode=mode, **kwargs)
    
    # End monitoring
    latency = (time.time() - start) * 1000
    quality = meta.end_session(session, response, latency)
    
    # Store experience
    store.store(prompt, response, mode, quality)
    
    # Update knowledge graph
    kg.infer_from_prompt(prompt)
    
    # Check for improvement
    improvement = learner.get_improvement(prompt)
    if improvement:
        response = improvement
    
    return response


if __name__ == "__main__":
    print("Meta-Cognition Layer")
    print("=" * 40)
    stats = get_stats()
    for comp, s in stats.items():
        print(f"\n{comp}: {s}")