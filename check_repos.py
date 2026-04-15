"""Check repo production readiness"""
from pathlib import Path

repos = {
    "autocoder": "D:/autocoder",
    "uis": "D:/UIS", 
    "axiomcode": "D:/axiomcode",
    "sllm": "D:/sl/projects/sllm",
}

print("=== Repo Production Readiness ===")
for name, path in repos.items():
    p = Path(path)
    has_readme = (p / "README.md").exists()
    has_reqs = (p / "requirements.txt").exists()
    has_wf = (p / ".github/workflows").exists()
    has_tests = any((p / "tests").glob("*.py")) or any(p.glob("test_*.py"))
    
    print(f"{name}:")
    print(f"  README: {'Y' if has_readme else 'N'}")
    print(f"  requirements: {'Y' if has_reqs else 'N'}")
    print(f"  GitHub Actions: {'Y' if has_wf else 'N'}")
    print(f"  Tests: {'Y' if has_tests else '?'}")
    print()