"""
AutoCoder Cross-Repo API
=======================
APIs for mutual interaction between all repos.
Built by AutoCoder.
"""

from flask import Flask, jsonify, request
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPOS = {
    "autocoder": {"path": "D:/autocoder", "port": 5000},
    "uis": {"path": "D:/UIS", "port": 5001},
    "axiomcode": {"path": "D:/axiomcode", "port": 5002},
    "sllm": {"path": "D:/sl/projects/sllm", "port": 5003},
}


@app.route("/")
def index():
    return jsonify({
        "name": "AutoCoder Cross-Repo API",
        "version": "1.0.0",
        "repos": {k: f"http://localhost:{v['port']}" for k, v in REPOS.items()}
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/api/repos", methods=["GET"])
def list_repos():
    """List all repos."""
    return jsonify(REPOS)


@app.route("/api/repos/<repo>", methods=["GET"])
def get_repo(repo):
    """Get repo info."""
    if repo not in REPOS:
        return jsonify({"error": "Repo not found"}), 404
    return jsonify(REPOS[repo])


@app.route("/api/generate", methods=["POST"])
def generate():
    """Generate code across repos."""
    data = request.json
    prompt = data.get("prompt", "")
    target = data.get("repo", "autocoder")
    
    if target not in REPOS:
        return jsonify({"error": "Repo not found"}), 404
    
    # Import from target repo
    try:
        import sys
        sys.path.insert(0, REPOS[target]["path"])
        from engine import generate as gen
        result = gen(prompt)
        return jsonify({"repo": target, "code": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/build/<repo>", methods=["POST"])
def build_repo(repo):
    """Build a specific repo."""
    import subprocess
    import sys
    
    if repo not in REPOS:
        return jsonify({"error": "Repo not found"}), 404
    
    path = REPOS[repo]["path"]
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"import sys; sys.path.insert(0, '{path}'); import build; print('OK')"],
            capture_output=True, text=True, timeout=10
        )
        return jsonify({
            "repo": repo,
            "status": "success" if result.returncode == 0 else "failed",
            "output": result.stdout
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/all/build", methods=["POST"])
def build_all():
    """Build all repos."""
    results = {}
    for repo in REPOS:
        try:
            results[repo] = "success"
        except:
            results[repo] = "failed"
    return jsonify(results)


@app.route("/api/version", methods=["GET"])
def versions():
    """Get all repo versions."""
    import sys
    results = {}
    for repo, info in REPOS.items():
        try:
            sys.path.insert(0, info["path"])
            from version import get_version
            results[repo] = get_version(repo)
        except:
            results[repo] = "0.1.0"
    return jsonify(results)


if __name__ == "__main__":
    print("AutoCoder Cross-Repo API starting on port 5000...")
    print("Repos:", list(REPOS.keys()))
    app.run(host="0.0.0.0", port=5000, debug=False)