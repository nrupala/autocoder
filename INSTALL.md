# AutoCoder - System Requirements & Installation

## System Requirements

### Minimum
- Python 3.10+
- 4GB RAM
- Internet connection (for cloud models)

### Recommended
- Python 3.12+
- 16GB RAM
- NVIDIA GPU (8GB+ VRAM)
- Docker

## Quick Install

### 1. Clone & Setup
```bash
git clone https://github.com/your-org/autocoder.git
cd autocoder

# Run setup script
setup.bat
```

### 2. Manual Install
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies (optional)
pip install pytest ruff mypy
```

### 3. Run
```bash
# Basic usage
python cli.py "create a Python FastAPI for user authentication"

# Interactive chat
python cli.py chat

# Check system
python system_check.py
```

## Build Tools Available

| Tool | Status Check | Install |
|------|--------------|---------|
| Python | `python --version` | python.org |
| Node.js | `node --version` | nodejs.org |
| Docker | `docker --version` | docker.com |
| Ollama | `ollama --version` | ollama.ai |
| Git | `git --version` | git-scm.com |
| VS Code | Code.exe | code.visualstudio.com |
| Cline | cline | cline.ai |

## GPU Setup

### NVIDIA CUDA
```bash
# Check GPU
nvidia-smi

# Install PyTorch with CUDA
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

## Environment Variables

```bash
# API Keys (optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Ollama settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-coder:14b

# Paths
AUTOCODER_MEMORY_PATH=./memory
AUTOCODER_KEY_PATH=./keys
```

## Troubleshooting

### Ollama not found
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull deepseek-coder:14b
```

### GPU not detected
```bash
# Check NVIDIA drivers
nvidia-smi

# Reinstall PyTorch with CUDA
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```
