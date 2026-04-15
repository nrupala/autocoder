# AutoCoder 🧠⚡

> Universal Autonomous Coding Agent - Write code, verify it, learn, evolve.

AutoCoder is a next-generation AI coding assistant with **built-in autonomous daemon** that works without external LLM dependencies:

- **Template-Based Generation** - 9 built-in code snippets for instant code generation
- **Daemon Service** - Persistent background server like OpenCode/Claude Code
- **Project Management** - Scaffold, build, test, and watch projects autonomously
- **Natural Language Understanding** - Code from plain English
- **Multi-Model Orchestration** - Ollama, OpenAI, Claude, Gemini (when available)
- **GPU Optimization** - Auto-scales from RTX 4090 to CPU
- **Formal Verification** - Lean 4 integration for proofs
- **Sovereign AI** - Your keys, your data, your intelligence
- **Self-Learning** - PDCA loop for continuous improvement

---

## Features

### 🌐 Multi-Language Support
- **Web**: Python, JavaScript, TypeScript, Go, Rust, Java, C#
- **System**: C, C++, Rust, Assembly
- **Scripting**: Ruby, PHP, Perl, PowerShell, Bash
- **Mobile**: Swift, Kotlin, React Native
- **Data**: SQL, GraphQL, JSON, YAML, Protobuf
- **Databases**: PostgreSQL, MySQL, MongoDB, Redis, SQLite

### 🧠 Intelligent Core
- **Intent Parsing** - Understands what you want to do
- **Entity Extraction** - Detects language, framework, requirements
- **Context Tracking** - Remembers session history
- **Multi-Model Routing** - Selects optimal model per task

### ⚡ Hardware Optimization
| GPU | Model | Quantization |
|-----|-------|---------------|
| RTX 4090+ | deepseek-coder:14b | q2_K |
| RTX 3090 | deepseek-coder:14b | q4_0 |
| RTX 2080 | qwen2.5-coder:7b | q4_0 |
| GTX 1060 | phi3:3b | q8_0 |
| CPU Only | llama3.2:3b | q5_1 |

### 🔐 Security (from axiomcode)
- **Key Store** - Zero-knowledge encryption
- **Audit Log** - Tamper-evident logging
- **Rate Limiter** - API protection
- **Code Signing** - Cryptographic verification

### 🧬 Self-Learning (from SLLM)
- **Episodic Memory** - Session history
- **Knowledge Graph** - Entity relationships
- **PDCA Loop** - Plan-Do-Check-Act improvement

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/autocoder.git
cd autocoder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install Ollama (for local models)
# https://ollama.ai
```

### Basic Usage

```bash
# Generate code
autocoder "create a Python FastAPI for user authentication"

# Generate with specific language
autocoder "build a React component for login form" --lang javascript

# Explain code
autocoder "explain how binary search works"

# List available models
autocoder models

# Show hardware config
autocoder config
```

### Interactive Mode

```bash
# Start interactive chat
python cli.py chat

# Or use guide mode
python cli.py guide
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      AutoCoder Core                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   NL         │  │  Orchestrator│  │   Hardware   │         │
│  │   Processor  │──│              │──│   Optimizer  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │                  Tool Registry                       │       │
│  │  • FileSystem  • Code  • Execution  • Web  • AI     │       │
│  └─────────────────────────────────────────────────────┘       │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐              │
│         ▼                    ▼                    ▼              │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐        │
│  │   Memory   │      │   Security │      │   Verify   │        │
│  │  System    │      │   Layer    │      │   Engine   │        │
│  └────────────┘      └────────────┘      └────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Commands

| Command | Description |
|---------|-------------|
| `autocoder generate <desc>` | Generate code from NL |
| `autocoder explain <code>` | Explain code/concept |
| `autocoder models` | List available models |
| `autocoder config` | Show hardware config |
| `autocoder keys create <name>` | Create signing key |
| `autocoder keys list` | List signing keys |
| `autocoder audit` | Show audit log |
| `autocoder help` | Show help |

---

## Environment Variables

```bash
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-coder:14b

# Paths
AUTOCODER_MEMORY_PATH=./memory
AUTOCODER_KEY_PATH=./keys
```

---

## Configuration

AutoCoder can be configured via `config/default.yaml`:

```yaml
model:
  default: deepseek-coder:14b
  code_generation: deepseek-coder:14b
  reasoning: deepseek-r1:7b
  natural_response: llama3.2:3b

hardware:
  gpu_detection: true
  auto_scale: true
  quantization: q4_0

security:
  enable_audit: true
  rate_limit: 100
  key_iterations: 600000
```

---

## Supported Models

### Local (Ollama)
- `deepseek-coder:14b` - Best for code generation
- `qwen2.5-coder:7b` - Good balance
- `llama3.2:3b` - General purpose
- `mistral:7b` - Fast reasoning
- `phi3:3b` - Low resource
- `stable-code:3b` - Verification

### Cloud
- OpenAI: GPT-4o, GPT-4 Turbo
- Anthropic: Claude Sonnet, Claude Haiku
- Gemini: Pro, Flash

---

## Development

```bash
# Run tests
pytest tests/ -v

# Type checking
mypy core/ models/ memory/ security/ tools/

# Linting
ruff check .

# Run in development
python cli.py "your request"
```

---

## License

MIT - Your intelligence should be free.

---

**Built with the best practices from: axiomcode, UIS, SLLM, Simplicity**
