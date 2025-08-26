# Personal Assistant Demo - NeMo Agent Toolkit

A comprehensive demonstration of the NVIDIA NeMo Agent Toolkit featuring a personal assistant agent that showcases the toolkit's key capabilities for building intelligent agent workflows.

## 🚀 Quick Start (Choose Your LLM Provider)

This demo supports **two LLM providers** - choose the one that fits your needs:

### 🏠 **Option A: Ollama (Local) - Recommended for Beginners**
- ✅ **No API key required** - runs completely locally
- ✅ **Privacy-focused** - everything stays on your machine
- ✅ **Free to use** - no usage costs or rate limits
- ✅ **Works offline** - no internet required after setup
- ❌ Requires local setup and hardware resources

### ☁️ **Option B: NVIDIA NIM (Cloud) - For Advanced Users**
- ✅ **More powerful models** - higher performance
- ✅ **No local setup** - just need an API key
- ✅ **Always available** - no hardware limitations
- ❌ Requires NVIDIA API key
- ❌ Network dependency and potential costs

---

## Repository Structure

```
personal-assistant-demo/
├── personal_assistant_demo/        # Personal assistant demo application
│   ├── src/                        # Demo source code
│   │   └── personal_assistant/     # Main package
│   │       ├── tools/              # Custom tools (weather, tasks, calculator, datetime)
│   │       ├── web/                # Web interface components
│   │       └── register.py         # Function registration
│   ├── configs/                    # Configuration files
│   │   ├── config.yml              # NVIDIA NIM configuration (cloud)
│   │   ├── config-ollama-react.yml # Ollama ReAct configuration
│   │   ├── config-ollama-tool-calling.yml # Ollama tool-calling epuration
│   │   ├── config-nim-react.yml    # NIM ReAct configuration
│   │   └── config-nim-tool-calling.yml # NIM tool-calling configuration
│   ├── tests/                      # Demo tests
│   ├── data/                       # Persistent data storage
│   ├── docs/                       # Demo documentation
│   ├── demo/                       # Demo scripts
│   ├── run_web_demo.py             # Web demo launcher
│   ├── .env.example                # Environment variables template
│   └── pyproject.toml              # Package configuration
├── .venv/                          # Virtual environment (created by uv, not synced)
├── .env                            # Your actual API keys (not synced)
├── .gitignore                      # Git ignore rules
├── setup.sh                        # Quick setup script (uses uv)
├── dev.sh                          # Development helper script
└── README.md                       # This file
```

## About NeMo Agent Toolkit

This demo uses the **NVIDIA NeMo Agent Toolkit**, a framework-agnostic library for building intelligent agents that features:

- **Framework Agnostic**: Works with LangChain, LlamaIndex, CrewAI, Semantic Kernel, and more
- **Reusable Components**: Composable agents, tools, and workflows
- **Rapid Development**: Pre-built components for quick customization
- **Profiling & Observability**: Built-in monitoring and debugging tools
- **Evaluation System**: Validate and maintain workflow accuracy
- **Full MCP Support**: Model Context Protocol client and server capabilities

📖 **[Official Documentation](https://docs.nvidia.com/nemo/agent-toolkit/latest)**

## Personal Assistant Demo

A comprehensive demonstration featuring a personal assistant agent with:

- **Task Management**: Create, list, complete, and delete personal tasks
- **Mathematical Operations**: Basic calculations (add, subtract, multiply, divide)
- **Date/Time Information**: Current date, time, and timezone information
- **Weather Information**: Current weather conditions (with API key)
- **Multi-step Reasoning**: ReAct agent for complex query handling

📖 **[Demo Documentation](./personal_assistant_demo/README.md)**

## 🎯 Getting Started

### Prerequisites

- Python 3.11 or 3.12
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- **Node.js 18+** and **npm** (optional, only if you want the web UI)

### 🐍 Important for Conda Users

This repository's setup script **automatically handles conda environment conflicts** that commonly cause `ModuleNotFoundError: No module named 'uvicorn'` errors. The script:

- ✅ **Detects active conda environments** and deactivates them during setup
- ✅ **Uses `uv pip` instead of conda's pip** to avoid package conflicts  
- ✅ **Verifies installation** to ensure all dependencies work correctly
- ✅ **Provides clear instructions** for proper virtual environment activation

**If you previously had issues with conda conflicts**, simply re-run `./setup.sh` and the improved script will resolve them automatically.

### Step 1: Install uv

```bash
# Install uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv

# Or using homebrew (macOS)
brew install uv
```

### Step 2: Choose Your LLM Provider

#### 🏠 **Option A: Ollama (Local) - Recommended for Beginners**

**Install Ollama:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Or using homebrew (macOS)
brew install ollama

# Start Ollama service
ollama serve

# Pull a model (in another terminal)
ollama pull qwen2.5:7b      # RECOMMENDED: Best for agents, excellent tool calling
# ollama pull llama3.2:3b   # Faster, smaller alternative
# ollama pull llama3.1:8b   # More capable, needs more RAM
```

#### ☁️ **Option B: NVIDIA NIM (Cloud) - For Advanced Users**

**Get NVIDIA API Key:**
1. Visit [build.nvidia.com](https://build.nvidia.com/)
2. Sign up for an account
3. Get your API key from the dashboard

### Step 3: Setup the Demo

**Clone and setup:**
```bash
# Clone the repository
git clone https://github.com/javiplav/personal-assistant-demo.git
cd personal-assistant-demo

# Run the setup script
./setup.sh
```

**Activate the virtual environment:**
```bash
source .venv/bin/activate  # macOS/Linux
# or .venv\Scripts\activate  # Windows
```

### Step 4: Run Your First Demo

#### 🏠 **With Ollama (Local):**

**Quick test:**
```bash
cd personal_assistant_demo
nat run --config_file configs/config-ollama-react.yml --input "What time is it?"
```

**Web UI experience:**
```bash
# Terminal 1: Start Ollama (if not already running)
ollama serve

# Terminal 2: Start the backend
cd personal_assistant_demo
nat serve --config_file configs/config-ollama-react.yml

# Terminal 3: Start the web UI (optional)
./dev.sh ui-setup  # First time setup
./dev.sh ui        # Start the UI
# Then open http://localhost:3001
```

#### ☁️ **With NVIDIA NIM (Cloud):**

**First, set your API key:**
```bash
# Edit .env file and add your NVIDIA API key
echo "NVIDIA_API_KEY=your_actual_api_key_here" >> .env
```

**Quick test:**
```bash
cd personal_assistant_demo
nat run --config_file configs/config.yml --input "What time is it?"
```

**Web UI experience:**
```bash
# Terminal 1: Start the backend
cd personal_assistant_demo
nat serve --config_file configs/config.yml

# Terminal 2: Start the web UI (optional)
./dev.sh ui-setup  # First time setup
./dev.sh ui        # Start the UI
# Then open http://localhost:3001
```

---

## 🎪 Example Interactions

Try these queries with your agent:

### Task Management
- "Add a task to buy groceries"
- "List all my tasks"
- "Mark the grocery task as completed"
- "Create a task to call mom tomorrow"

### Calculations
- "What's 15 multiplied by 8?"
- "Calculate 100 divided by 4"
- "Add 25 and 37"

### Date/Time
- "What time is it?"
- "What's today's date?"
- "What timezone am I in?"

### Complex Multi-step Queries
- "What's the weather in Paris and add a task to pack an umbrella if it's going to rain"
- "Calculate 20% of 150 and create a task to save that amount"
- "What time is it and how much is 8 hours from now?"

---

## 🔧 Configuration Options

### Config File Comparison

| Config File | LLM Provider | API Key Required | Agent Type | Best For |
|-------------|--------------|------------------|------------|----------|
| `config-ollama-react.yml` | Ollama (Local) | ❌ None | ReAct | Beginners, privacy, offline use |
| `config-ollama-tool-calling.yml` | Ollama (Local) | ❌ None | Tool Calling | Local development, alternative approach |
| `config.yml` | NVIDIA NIM (Cloud) | ✅ NVIDIA API Key | Tool Calling | Production, high performance |
| `config-nim-react.yml` | NVIDIA NIM (Cloud) | ✅ NVIDIA API Key | ReAct | Cloud-based reasoning workflows |
| `config-nim-tool-calling.yml` | NVIDIA NIM (Cloud) | ✅ NVIDIA API Key | Tool Calling | Cloud-based direct function calls |

### Choosing Between Agent Types

The demo supports different agent approaches for both local (Ollama) and cloud (NIM) providers:

```bash
# Ollama (Local) Options
nat run --config_file configs/config-ollama-react.yml --input "Hello!"           # ReAct agent
nat run --config_file configs/config-ollama-tool-calling.yml --input "Hello!"   # Tool-calling agent

# NVIDIA NIM (Cloud) Options  
nat run --config_file configs/config.yml --input "Hello!"                       # Tool-calling (default)
nat run --config_file configs/config-nim-react.yml --input "Hello!"            # ReAct agent
nat run --config_file configs/config-nim-tool-calling.yml --input "Hello!"     # Tool-calling (explicit)
```

**Agent Type Differences:**
- **ReAct**: Reasons through problems step-by-step, better for complex multi-step tasks
- **Tool Calling**: Direct function invocation, faster for straightforward tasks

### Development Helper Script

Use the `dev.sh` script for common tasks:

```bash
# Ollama commands
./dev.sh run-ollama    # Quick demo with Ollama
./dev.sh serve-ollama  # Web UI with Ollama

# NVIDIA commands
./dev.sh run           # Quick demo with NVIDIA NIM
./dev.sh serve         # Web UI with NVIDIA NIM

# Other commands
./dev.sh help          # Show all available commands
./dev.sh ui-setup      # Setup web UI
./dev.sh ui            # Start web UI
```

---

## 🌐 Web User Interface (Optional)

The **official NeMo Agent Toolkit Web UI** provides a modern chat interface for interacting with your agents.

### UI Features

- 🎨 **Modern Chat Interface**: Clean, responsive design
- 🔄 **Real-time Streaming**: Live response streaming
- 🤝 **Human-in-the-Loop**: Interactive approval workflows
- 🌙 **Theme Support**: Light and dark modes
- 🔌 **WebSocket Integration**: Real-time communication
- 📱 **Mobile Responsive**: Works on all devices

### UI Setup

```bash
# Use the enhanced web demo launcher (recommended)
python run_web_demo.py            # Ollama ReAct (default)
python run_web_demo.py --nim      # NIM tool-calling
python run_web_demo.py --config configs/config-nim-react.yml         # NIM ReAct

# Or use the development script for traditional NAT UI
./dev.sh ui-setup  # Clones and sets up the UI
./dev.sh ui        # Starts the UI server
```

The web interface will be available at `http://localhost:8000`

### Alternative: API Documentation

If you don't want the full UI, use the built-in API documentation at `http://localhost:8000/docs` when running the backend.

---

## 🎯 Key Features Demonstrated

### Agent Types
- **ReAct Agents**: Reasoning and acting in iterative cycles
- **Tool-Calling Agents**: Direct function invocation
- **ReWOO Agents**: Reasoning without observation
- **Mixture of Agents**: Combining multiple agent strategies

### LLM Providers
- **NVIDIA NIM**: Cloud-based, high-performance models (requires API key)
- **Ollama**: Local LLM execution, privacy-focused, no API key needed
- **OpenAI-Compatible**: Works with any OpenAI-compatible API server

#### Recommended Ollama Models for Agents

| Model | Size | Best For | Hardware |
|-------|------|----------|----------|
| **qwen2.5:7b** ⭐ | 4.7GB | General agents, excellent tool calling | 8GB+ RAM |
| **llama3.2:3b** | 2GB | Fast responses, limited resources | 4GB+ RAM |
| **llama3.1:8b** | 4.7GB | Complex reasoning, multi-step tasks | 8GB+ RAM |
| **phi3:3.8b** | 2.3GB | Efficient, good balance | 4GB+ RAM |

> **💡 Recommendation**: Use `qwen2.5:7b` for the best agent performance with tool calling and reasoning.

### Tool Integration
- **Custom Functions**: Weather, tasks, calculations, date/time
- **External APIs**: OpenWeatherMap integration
- **Persistent Storage**: JSON-based task storage
- **Error Handling**: Robust error management and user feedback

### Configuration Management
- **YAML-based Configuration**: Simple, readable workflow definitions
- **Environment Variables**: Secure API key management via `.env` files
- **Plugin System**: Modular component registration

---

## 🔐 Environment Variables

This demo uses a `.env` file for secure API key management:

1. **Copy the template**: `cp .env.example .env`
2. **Edit `.env`** with your actual API keys:
   - `NVIDIA_API_KEY`: Required for NVIDIA NIM (cloud) access
   - `OPENWEATHERMAP_API_KEY`: Optional for weather functionality
3. **Never commit `.env`** - it's automatically ignored by Git

The demo automatically loads environment variables using `python-dotenv`.

---

## 🛠️ Development

### Running Tests

```bash
cd personal_assistant_demo
uv run pytest tests/
```

### Development Helper Script

Use the `dev.sh` script for common development tasks:

```bash
./dev.sh setup     # Initial setup
./dev.sh test      # Run tests
./dev.sh run       # Run demo with NVIDIA NIM
./dev.sh run-ollama # Run demo with Ollama
./dev.sh serve     # Start web UI with NVIDIA NIM
./dev.sh serve-ollama # Start web UI with Ollama
./dev.sh clean     # Clean virtual environment
./dev.sh help      # Show all commands
```

### Code Quality

The project uses:
- **Ruff**: Code formatting and linting
- **Type Hints**: Full type annotation support
- **Logging**: Comprehensive logging throughout
- **Error Handling**: Graceful error management

---

## 📚 Documentation

- **[NeMo Agent Toolkit Documentation](https://docs.nvidia.com/nemo/agent-toolkit/latest)**
- **[GitHub Repository](https://github.com/NVIDIA/NeMo-Agent-Toolkit)**
- **[Official Examples](https://github.com/NVIDIA/NeMo-Agent-Toolkit/tree/main/examples)**
- **[API Reference](https://docs.nvidia.com/nemo/agent-toolkit/latest/reference/)**

---

## 🤝 Support

- **GitHub Issues**: [NeMo Agent Toolkit Issues](https://github.com/NVIDIA/NeMo-Agent-Toolkit/issues)
- **Documentation**: [Official Docs](https://docs.nvidia.com/nemo/agent-toolkit/latest)
- **Community**: Join the NVIDIA Developer community

---

## 📄 License

This project is licensed under the Apache License 2.0. See the [NeMo Agent Toolkit LICENSE](https://github.com/NVIDIA/NeMo-Agent-Toolkit/blob/main/LICENSE.md) for details.

---

**NVIDIA NeMo Agent Toolkit** - Build intelligent agents with ease.
