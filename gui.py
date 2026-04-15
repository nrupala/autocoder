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
    from engine import generate as gen_code
    data = request.json
    prompt = data.get('prompt', '')
    mode = data.get('mode', 'standard')
    
    try:
        result = gen_code(prompt)
        return jsonify({"code": result})
    except Exception as e:
        logger.error(f"Generate error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/status', methods=['GET'])
def status():
    import psutil
    return jsonify({
        "status": "ok",
        "gpu": "CPU Only",
        "system": {
            "CPU": f"{psutil.cpu_count(logical=False)} cores",
            "RAM": f"{psutil.virtual_memory().total / (1024**3):.1f} GB"
        },
        "provider": "template"
    })


@app.route('/api/version', methods=['GET'])
def version():
    return jsonify({
        "version": "1.0.0",
        "name": "AutoCoder",
        "build": "2026.04.15"
    })


@app.route('/api/tasks', methods=['GET'])
def list_tasks():
    from tasks import get_tracker, get_stats
    return jsonify({
        "tasks": get_tracker().get_tasks(),
        "stats": get_stats()
    })


@app.route('/api/repos', methods=['GET'])
def list_repos():
    from tasks import get_tracker
    return jsonify(get_tracker().get_repos_status())


def run_gui(port=5000):
    logger.info(f"Starting AutoCoder on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    run_gui()