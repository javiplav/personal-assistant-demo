# Personal Assistant Demo - NeMo Agent Toolkit

A comprehensive demonstration of the NVIDIA NeMo Agent Toolkit featuring a personal assistant agent that showcases the toolkit's key capabilities for building intelligent agent workflows.

## 🚀 Quick Start - Enhanced Personal Assistant

**New in this version:** Advanced filtering, intelligent task descriptions, beautiful web UI, and production-grade architecture!

### ⚡ **Instant Setup & Launch**

**Option 1: Native Setup (Recommended)**
```bash
./setup.sh                    # First time setup
./scripts/quick_start.sh       # Start web interface
```

**Option 2: Docker (One-Click Deploy)**
```bash
docker-compose up --build     # Build and start container
# OR with local Ollama included:
docker-compose --profile with-ollama up --build
```

**→ Opens at http://localhost:8000**

### 🎯 **Key Features**
- 🔍 **Smart Filtering**: `"List security tasks"` → Shows only security tasks
- 🧠 **Intelligent Parsing**: Extracts meaningful task descriptions  
- 🎨 **Beautiful UI**: Professional interface with animations
- ⚡ **Multi-step Operations**: Natural language combining actions
- 🏗️ **Production Architecture**: Enterprise-ready with error handling

### 🏠 **LLM Provider Options**

**Option A: Ollama (Local) - Recommended**
- ✅ No API key required, runs locally, free
- ✅ Privacy-focused, works offline
- ⚠️ Requires: `ollama serve` + `ollama pull qwen2.5:7b`

**Option B: NVIDIA NIM (Cloud)**  
- ✅ More powerful models, no local setup
- ⚠️ Requires: NVIDIA API key

---

## Repository Structure

```
personal-assistant-demo/
├── personal_assistant_demo/           # 🎯 Main demo application
│   ├── src/personal_assistant/       # Production source code
│   │   ├── core/                    # 🏗️ Business logic (controller, agent, registry) 
│   │   ├── adapters/                # 🔌 Framework integrations (webui, NAT)
│   │   ├── tools/                   # 🛠️ Task management, calculations, clients
│   │   └── legacy/                  # 📚 Preserved old implementations
│   ├── demos/                       # 🎨 Demo applications & beautiful web UI
│   ├── configs/                     # ⚙️ Multiple configurations for different setups
│   │   ├── config-planner-executor.yml # 🎯 Main config (recommended)
│   │   ├── config-ollama-*.yml      # 🏠 Local Ollama configurations  
│   │   └── config-nim-*.yml         # ☁️ NVIDIA NIM configurations
│   ├── tests/                       # 🧪 Comprehensive test suite (unit/integration/e2e)
│   ├── docs/                        # 📖 Architecture guides and examples
│   └── data/                        # 💾 Persistent data storage
├── scripts/                          # 🚀 Utility scripts  
│   ├── quick_start.sh               # ⚡ One-click startup
│   ├── start_web.py                 # 🌐 Web server with API endpoints
│   └── test_api.sh                  # 🧪 API testing script
├── setup.sh & dev.sh                # 🛠️ Main user scripts
└── NeMo-Agent-Toolkit-develop/       # 📦 NVIDIA NeMo Agent Toolkit
```

## ✨ Enhanced Features in This Demo

This Personal Assistant showcases advanced capabilities built on top of the base toolkit:

### 🧠 **Intelligent Natural Language Processing**
- **Smart Task Extraction**: `"Add a task called Review architecture"` → Creates "Review Architecture" 
- **Advanced Filtering**: `"List security tasks"` → Shows only security-related tasks from your full task list
- **Multi-step Operations**: `"Add a task, then list all tasks"` → Executes both actions naturally

### 🎨 **Beautiful Production-Ready Interface**
- **Professional Design**: Modern UI with gradients, animations, and responsive layout
- **Real-time Interactions**: Instant feedback with loading states and status indicators
- **Multiple UI Options**: Beautiful, Classic, Simple, and Minimal templates

### 🏗️ **Enterprise Architecture**
- **Clean Code Organization**: Separated core logic, adapters, tools, and demos
- **Production Error Handling**: Comprehensive validation, logging, and graceful degradation  
- **Comprehensive Testing**: Unit, integration, and end-to-end test coverage
- **Performance Optimizations**: Caching, atomic operations, and efficient data handling

### 📊 **Advanced Task Management** 
- **Status Filtering**: `"List completed tasks"` → Shows detailed completion history
- **Search Capabilities**: Find tasks by keywords, client names, or content
- **Rich Task Details**: Meaningful descriptions instead of generic placeholders
- **Client Integration**: Associate tasks with specific clients and projects

---

## Configuration Guide

**Quick Reference:** Use `config-planner-executor.yml` (recommended) - it's already set as default.

| Config File | Best For | LLM Provider | Architecture |
|-------------|----------|--------------|--------------|
| **config-planner-executor.yml** | **🎯 Recommended** | Ollama | Planner-Executor (most reliable) |
| config-ollama-tool-calling.yml | Advanced users | Ollama | Tool-calling (faster) |  
| config-nim-tool-calling.yml | Cloud users | NVIDIA NIM | Tool-calling with cloud LLMs |
| config-ollama-react.yml | Experimental | Ollama | ReAct (can be verbose) |
| config-nim-react.yml | Experimental | NVIDIA NIM | ReAct with cloud LLMs |

**💡 Pro Tip:** The Planner-Executor architecture (default) provides the most consistent and reliable results for complex multi-step tasks.

---

## About NeMo Agent Toolkit

This enhanced demo uses the **NVIDIA NeMo Agent Toolkit**, a framework-agnostic library for building intelligent agents that features:

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

- ✅ **Detects active conda environments** (checks both `CONDA_DEFAULT_ENV` and `CONDA_PREFIX`)
- ✅ **Deactivates conda and clears environment variables** to prevent interference
- ✅ **Uses explicit Python path** (`uv pip install --python .venv/bin/python`) to force correct environment
- ✅ **Shows target Python path** during installation for transparency  
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

## 🎯 Example Interactions - Enhanced Capabilities

Experience the power of intelligent filtering and natural language processing:

### 🔍 **Smart Filtering (New!)**
```
"List security tasks"              → Shows only security-related tasks
"Show my completed tasks"          → Detailed completion history
"List API tasks"                  → Tasks containing "API" keyword  
"Show pending tasks for client X" → Filtered by status and client
```

### 🧠 **Intelligent Task Creation (Enhanced!)**
```
"Add a task called Review architecture"      → Creates: "Review Architecture"
"Create task Security audit for enterprise" → Creates: "Security Audit For Enterprise"  
"Add Fix login bug to my tasks"            → Creates: "Fix Login Bug"
```

### ⚡ **Multi-Step Operations (Improved!)**
```
"Add a task called Update docs, then list my tasks"
"Create client TechCorp, then add task Review contract"
"Calculate 25% of 200, then show current time"
```

### 🎨 **Beautiful Interface Features**
- **Professional Design**: Modern UI with gradients and animations
- **Real-Time Updates**: Instant feedback with loading states
- **Multiple Templates**: Beautiful, Classic, Simple, Minimal views
- **Responsive Layout**: Perfect on desktop, tablet, and mobile

### 📊 **Advanced Task Management**
```
"List my tasks"                   → Shows organized task list with status icons
"Show completed tasks"            → ✅ Detailed completion history
"List tasks for Microsoft"        → Client-specific task filtering
"Add client NVIDIA"              → 👤 Professional client management
```

### 🧮 **Calculations & Utilities**
```
"Calculate 25% of 200"           → 🧮 25.0% of 200.0 = 50.0
"What time is it?"               → 🕒 Current time: 03:41 PM
"Add 15 and 27"                  → ➕ 15 + 27 = 42
```

---

## 🔧 Configuration Options

**Quick Start:** The demo uses `config-planner-executor.yml` by default - no configuration needed!

### 📋 **Available Configurations**

| Config File | LLM Provider | Architecture | Status | Best For |
|-------------|--------------|--------------|--------|----------|
| **`config-planner-executor.yml`** | **Ollama** | **Planner-Executor** | **✅ Default** | **🎯 Recommended - Most reliable** |
| `config-ollama-tool-calling.yml` | Ollama | Tool-Calling | ⚡ Fast | Advanced users who want speed |
| `config-nim-tool-calling.yml` | NVIDIA NIM | Tool-Calling | ☁️ Cloud | Users with NVIDIA API keys |
| `config-ollama-react.yml` | Ollama | ReAct | 🧪 Experimental | Testing and experimentation |
| `config-nim-react.yml` | NVIDIA NIM | ReAct | 🧪 Experimental | Cloud-based ReAct workflows |

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
