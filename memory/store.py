# Copyright (c) 2026 AutoCoder Team.
# Licensed under the MIT License - see LICENSE at the repository root.
"""
Memory Store
============
The memory layer's public store API.

EpisodicMemory and KnowledgeGraph adapt the meta-cognition stores
(meta/) to the memory layer's base_path convention. PDCALearner
implements the Plan-Do-Check-Act self-improvement cycle, and
AutoCoderMemory is the facade the CLI uses to record interactions.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from meta.experience_store import Experience, ExperienceStore
from meta.knowledge_graph import KnowledgeGraph as _MetaKnowledgeGraph


class EpisodicMemory(ExperienceStore):
    """Episodic memory: stores and retrieves past interactions.

    An ExperienceStore addressed by base_path.
    """

    def __init__(self, base_path: str | None = None):
        super().__init__(memory_path=base_path)
        self.base_path = self.memory_path


class KnowledgeGraph(_MetaKnowledgeGraph):
    """Knowledge graph addressed by base_path (see meta.knowledge_graph)."""

    def __init__(self, base_path: str | None = None):
        super().__init__(memory_path=base_path)
        self.base_path = self.memory_path


class PDCALearner:
    """Plan-Do-Check-Act self-improvement cycle.

    plan() opens a cycle for a task, do() records executed steps,
    check() records the verified outcome against metrics, and act()
    archives the cycle with the adjustment it produced.
    """

    def __init__(self, base_path: str | None = None):
        self.base_path = Path(base_path) if base_path else Path("~/.autocoder/pdca").expanduser()
        self.current_plan: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []

    def plan(self, task: str, approach: str) -> dict[str, Any]:
        """Open a new PDCA cycle for a task."""
        self.current_plan = {
            "task": task,
            "approach": approach,
            "steps": [],
            "checks": [],
            "started_at": time.time(),
        }
        return self.current_plan

    def do(self, step: str, result: str) -> dict[str, Any]:
        """Record one executed step in the current cycle."""
        if not self.current_plan:
            self.plan("", "")
        entry = {"step": step, "result": result, "timestamp": time.time()}
        self.current_plan["steps"].append(entry)
        return entry

    def check(self, success: bool, metrics: dict | None = None) -> dict[str, Any]:
        """Record the checked outcome of the current cycle."""
        outcome = {
            "success": success,
            "metrics": metrics or {},
            "timestamp": time.time(),
        }
        if self.current_plan:
            self.current_plan.setdefault("checks", []).append(outcome)
        return outcome

    def act(self, adjustment: str) -> dict[str, Any]:
        """Archive the finished cycle with the adjustment it produced."""
        record = {
            "adjustment": adjustment,
            "plan": self.current_plan,
            "timestamp": time.time(),
        }
        self.history.append(record)
        return record


class AutoCoderMemory:
    """Facade over the memory stores, used by the CLI."""

    def __init__(self, base_path: str | None = None):
        self.base_path = Path(base_path) if base_path else Path("~/.autocoder/memory").expanduser()
        self.episodic = EpisodicMemory(str(self.base_path / "episodes"))
        self.knowledge = KnowledgeGraph(str(self.base_path / "knowledge"))
        self.learner = PDCALearner(str(self.base_path / "pdca"))

    def store_interaction(self, user_input: str, actions: list[str], code: str) -> Experience:
        """Store an interaction in episodic memory and update the graph."""
        experience = self.episodic.store(user_input, code, mode="interaction", tags=list(actions))
        self.knowledge.infer_from_prompt(user_input)
        return experience
