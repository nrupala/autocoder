"""
AutoCoder Web GUI Server
"""

from flask import Flask, render_template, request, jsonify
import logging

app = Flask(__name__, template_folder='web/templates', static_folder='web/static')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/generate', methods=['POST'])
def generate():
    from engine import get_engine
    
    data = request.json
    prompt = data.get('prompt', '')
    model = data.get('model', 'template')
    mode = data.get('mode', 'standard')
    
    try:
        result = get_engine().generate(prompt, model=model, mode=mode)
        
        if result.startswith("Error:") or "No LLM available" in result:
            return jsonify({"error": result}), 500
        else:
            return jsonify({"code": result})
            
    except Exception as e:
        logger.error(f"Generate error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/status', methods=['GET'])
def status():
    from engine import get_engine
    import psutil
    
    eng = get_engine()
    status = eng.get_status()
    
    result = {
        "ollama": status.get("ollama", False),
        "local": status.get("local", False),
        "models": status.get("models", []),
        "gpu": status.get("gpu", "CPU Only"),
        "system": {
            "CPU": f"{psutil.cpu_count(logical=False)} cores",
            "RAM": f"{psutil.virtual_memory().total / (1024**3):.1f} GB",
            "Python": f"{psutil.python_version()}"
        },
        "provider": status.get("provider", "template")
    }
    
    return jsonify(result)


@app.route('/api/meta/stats', methods=['GET'])
def meta_stats():
    """Get meta-cognition stats"""
    from meta import get_stats
    return jsonify(get_stats())


@app.route('/api/meta/graph', methods=['GET'])
def meta_graph():
    """Get knowledge graph for visualization"""
    from meta import get_knowledge_graph
    kg = get_knowledge_graph()
    return jsonify(kg.get_network())


@app.route('/api/experiences', methods=['GET'])
def list_experiences():
    """List recent experiences"""
    from meta import get_experience_store
    store = get_experience_store()
    exp = store.experiences[-10:] if store.experiences else []
    return jsonify([{
        "prompt": e.prompt[:50],
        "quality": e.quality,
        "tags": e.tags,
        "timestamp": e.timestamp
    } for e in exp])
    
    result = {
        "ollama": status.get("ollama", False),
        "local": status.get("local", False),
        "models": status.get("models", []),
        "gpu": status.get("gpu", "CPU Only"),
        "system": {
            "CPU": f"{psutil.cpu_count(logical=False)} cores",
            "RAM": f"{psutil.virtual_memory().total / (1024**3):.1f} GB",
            "Python": f"{psutil.python_version()}"
        },
        "provider": status.get("provider", "template")
    }
    
    return jsonify(result)


def run_gui(port=5000):
    logger.info(f"Starting AutoCoder GUI on http://localhost:{port}")
    logger.info("Press Ctrl+C to stop")
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    run_gui()
