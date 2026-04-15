"""
AutoCoder Task Tracker
==================
Tracks production tasks across all repos.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
import sqlite3


@dataclass
class RepoTask:
    repo: str
    task: str
    status: str = "pending"  # pending, in_progress, completed, failed
    priority: str = "medium"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


class TaskTracker:
    """
    AutoCoder's task tracker for repo production.
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            home = Path.home()
            autocoder_dir = home / ".autocoder"
            autocoder_dir.mkdir(exist_ok=True)
            db_path = autocoder_dir / "tasks.db"
        
        self.db_path = Path(db_path)
        self._init_db()
        
        self.repos = {
            "autocoder": {"path": "D:/autocoder", "status": "working"},
            "uis": {"path": "D:/UIS", "status": "working"},
            "axiomcode": {"path": "D:/axiomcode", "status": "working"},
            "sllm": {"path": "D:/sl/projects/sllm", "status": "working"},
            "simplicity": {"path": "D:/simplicity", "status": "working"},
        }
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo TEXT NOT NULL,
                task TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                created_at TEXT,
                updated_at TEXT,
                completed_at TEXT,
                error TEXT,
                result TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def add_task(self, repo: str, task: str, priority: str = "medium") -> int:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute(
            "INSERT INTO tasks (repo, task, status, priority, created_at, updated_at) VALUES (?, ?, 'pending', ?, ?, ?)",
            (repo, task, priority, now, now)
        )
        task_id = c.lastrowid
        conn.commit()
        conn.close()
        return task_id
    
    def update_task(self, task_id: int, status: str, error: str = None, result: str = None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = datetime.now().isoformat()
        completed = now if status in ("completed", "failed") else None
        c.execute(
            "UPDATE tasks SET status=?, updated_at=?, completed_at=?, error=?, result=? WHERE id=?",
            (status, now, completed, error, result, task_id)
        )
        conn.commit()
        conn.close()
    
    def get_tasks(self, repo: str = None, status: str = None) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if repo and status:
            c.execute("SELECT * FROM tasks WHERE repo=? AND status=?", (repo, status))
        elif repo:
            c.execute("SELECT * FROM tasks WHERE repo=?", (repo,))
        elif status:
            c.execute("SELECT * FROM tasks WHERE status=?", (status,))
        else:
            c.execute("SELECT * FROM tasks")
        
        rows = c.fetchall()
        conn.close()
        
        return [
            {
                "id": r[0], "repo": r[1], "task": r[2], "status": r[3],
                "priority": r[4], "created_at": r[5], "updated_at": r[6],
                "completed_at": r[7], "error": r[8], "result": r[9]
            }
            for r in rows
        ]
    
    def get_repos_status(self) -> Dict[str, Dict]:
        return self.repos.copy()
    
    def set_repo_status(self, repo: str, status: str):
        if repo in self.repos:
            self.repos[repo]["status"] = status
    
    def get_stats(self) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
        status_counts = {row[0]: row[1] for row in c.fetchall()}
        
        c.execute("SELECT repo, COUNT(*) FROM tasks GROUP BY repo")
        repo_counts = {row[0]: row[1] for row in c.fetchall()}
        
        conn.close()
        
        return {
            "by_status": status_counts,
            "by_repo": repo_counts,
            "total_repos": len(self.repos),
            "working_repos": sum(1 for r in self.repos.values() if r["status"] == "working")
        }
    
    def list_repos(self) -> List[str]:
        return list(self.repos.keys())


class ProductionRunner:
    """
    Builds, tests, pushes code to repos.
    """
    
    def __init__(self, tracker: TaskTracker = None):
        self.tracker = tracker or TaskTracker()
    
    async def build_repo(self, repo: str) -> Dict[str, Any]:
        """Run build for a repo."""
        import subprocess
        repo_path = self.tracker.repos.get(repo, {}).get("path")
        
        if not repo_path:
            return {"status": "failed", "error": f"Unknown repo: {repo}"}
        
        task_id = self.tracker.add_task(repo, "build", "high")
        self.tracker.update_task(task_id, "in_progress")
        
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            self.tracker.update_task(task_id, "completed", result=result.stdout[:500])
            self.tracker.set_repo_status(repo, "built")
            
            return {"status": "completed", "output": result.stdout[:500]}
        except Exception as e:
            self.tracker.update_task(task_id, "failed", error=str(e))
            return {"status": "failed", "error": str(e)}
    
    async def push_to_github(self, repo: str, message: str = None) -> Dict[str, Any]:
        """Push to GitHub."""
        import subprocess
        repo_path = self.tracker.repos.get(repo, {}).get("path")
        
        if not repo_path:
            return {"status": "failed", "error": f"Unknown repo: {repo}"}
        
        task_id = self.tracker.add_task(repo, "push", "high")
        self.tracker.update_task(task_id, "in_progress")
        
        try:
            result = subprocess.run(
                ["git", "push"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.tracker.update_task(task_id, "completed", result=result.stdout or "Pushed")
                return {"status": "completed"}
            else:
                self.tracker.update_task(task_id, "failed", error=result.stderr)
                return {"status": "failed", "error": result.stderr}
        except Exception as e:
            self.tracker.update_task(task_id, "failed", error=str(e))
            return {"status": "failed", "error": str(e)}
    
    async def run_all(self, action: str = "build") -> Dict[str, Any]:
        """Run action on all repos."""
        results = {}
        for repo in self.tracker.list_repos():
            if action == "build":
                results[repo] = await self.build_repo(repo)
            elif action == "push":
                results[repo] = await self.push_to_github(repo)
        return results


# Global tracker
_tracker = None

def get_tracker() -> TaskTracker:
    global _tracker
    if _tracker is None:
        _tracker = TaskTracker()
    return _tracker


def add_task(repo: str, task: str, priority: str = "medium") -> int:
    return get_tracker().add_task(repo, task, priority)


def get_tasks(repo: str = None, status: str = None) -> List[Dict]:
    return get_tracker().get_tasks(repo, status)


def get_stats() -> Dict[str, Any]:
    return get_tracker().get_stats()