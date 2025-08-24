# Personal Assistant Demo - NeMo Agent Toolkit

A comprehensive demonstration of the NVIDIA NeMo Agent Toolkit featuring a personal assistant agent that showcases the toolkit's key capabilities for building intelligent agent workflows.

## Repository Structure

```
personal-assistant-demo/
├── personal_assistant_demo/        # Personal assistant demo application
│   ├── src/                        # Demo source code
│   │   └── personal_assistant/     # Main package
│   │       ├── tools/              # Custom tools (weather, tasks, calculator, datetime)
│   │       ├── register.py         # Function registration
│   │       └── env_loader.py       # Environment variable loader
│   ├── configs/                    # Configuration files
│   │   ├── config.yml              # NVIDIA NIM configuration
│   │   ├── config-ollama.yml       # Ollama local LLM configuration
│   │   └── config-ollama-env.yml   # Ollama with environment variables
│   ├── tests/                      # Demo tests
│   ├── data/                       # Persistent data storage
│   └── pyproject.toml              # Package configuration
├── .venv/                          # Virtual environment (created by uv, not synced)
├── .env.example                    # Environment variables template
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

## Quick Start

### Prerequisites

- Python 3.11 or 3.12
- [uv](https://docs.astral.sh/uv/) - Fast Python package manager
- **Node.js 18+** and **npm** (optional, only if you want the web UI)
- **Choose one LLM provider:**
  - **NVIDIA API Key** from [build.nvidia.com](https://build.nvidia.com/) (cloud-based)
  - **OR [Ollama](https://ollama.com/)** for local LLM (privacy-focused, no API key needed)

#### Installing uv

```bash
# Install uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv

# Or using homebrew (macOS)
brew install uv
```

#### Installing Ollama (Optional - for local LLM)

If you prefer to run LLMs locally instead of using NVIDIA's cloud API:

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
# ollama pull codellama:7b  # Good for coding tasks
```

### Installation

#### Quick Setup (Recommended)

1. **Clone this repository**:
   ```bash
   git clone https://github.com/javiplav/personal-assistant-demo.git
   cd personal-assistant-demo
   ```

2. **Run the setup script**:
   ```bash
   ./setup.sh
   ```
   This will:
   - Check that uv is installed
   - Create virtual environment with `uv venv`
   - Create `.env` file from template
   - Install the demo package with `uv pip install`
   - Show you next steps

3. **Edit `.env` file** with your actual API keys

4. **Activate the virtual environment**:
   ```bash
   source .venv/bin/activate  # macOS/Linux
   # or .venv\Scripts\activate  # Windows
   ```

#### Manual Setup

1. **Clone this repository**:
   ```bash
   git clone https://github.com/javiplav/personal-assistant-demo.git
   cd personal-assistant-demo
   ```

2. **Set up environment variables**:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env file with your actual API keys
   # NVIDIA_API_KEY=your_actual_nvidia_api_key_here
   # OPENWEATHERMAP_API_KEY=your_actual_openweather_api_key_here  # Optional
   ```

3. **Create virtual environment**:
   ```bash
   uv venv
   source .venv/bin/activate  # macOS/Linux
   ```

4. **Install the toolkit** (choose one):
   
   **Option A: Stable Release**
   ```bash
   uv pip install nvidia-nat[all]
   ```
   
   **Option B: Development Version**
   ```bash
   cd NeMo-Agent-Toolkit-develop
   uv pip install -e .[all]
   ```

5. **Install the demo**:
   ```bash
   cd personal_assistant_demo
   uv pip install -e .
   ```

### Running Examples

#### With NVIDIA NIM (Cloud)

**Command Line**:
```bash
cd personal_assistant_demo
nat run --config_file configs/config.yml --input "What time is it and add a task to review the demo?"
```

**Web UI** (if you've set up the UI):
```bash
# Terminal 1: Start the backend
cd personal_assistant_demo
nat serve --config_file configs/config.yml

# Terminal 2: Start the web UI (if installed)
cd NeMo-Agent-Toolkit-develop/external/nat-ui
npm run dev

# Open http://localhost:3000 in your browser
```

**API Interface** (always available):
```bash
# Start the backend
cd personal_assistant_demo
nat serve --config_file configs/config.yml

# Open http://localhost:8000/docs in your browser
```

#### With Ollama (Local)

**Command Line**:
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Run the demo
cd personal_assistant_demo
nat run --config_file configs/config-ollama.yml --input "What time is it and add a task to review the demo?"
```

**Web UI** (if you've set up the UI):
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start the backend
cd personal_assistant_demo
nat serve --config_file configs/config-ollama.yml

# Terminal 3: Start the web UI (if installed)
cd NeMo-Agent-Toolkit-develop/external/nat-ui
npm run dev

# Open http://localhost:3000 in your browser
```

**API Interface** (always available):
```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start the backend
cd personal_assistant_demo
nat serve --config_file configs/config-ollama.yml

# Open http://localhost:8000/docs in your browser
```

#### Using the Development Script

```bash
# NVIDIA NIM
./dev.sh run       # Quick demo
./dev.sh serve     # Web UI

# Ollama Local
./dev.sh run-ollama    # Quick demo with Ollama
./dev.sh serve-ollama  # Web UI with Ollama
```

**More Examples**: Check out the [official NeMo Agent Toolkit examples](https://github.com/NVIDIA/NeMo-Agent-Toolkit/tree/main/examples) for additional demonstrations.

## 🌐 Web User Interface (Optional)

The **official NeMo Agent Toolkit Web UI** provides a modern chat interface for interacting with your agents. Since the full toolkit isn't synced to this repository, you'll need to set it up manually if you want the web UI.

### UI Features

- 🎨 **Modern Chat Interface**: Clean, responsive design
- 🔄 **Real-time Streaming**: Live response streaming
- 🤝 **Human-in-the-Loop**: Interactive approval workflows
- 🌙 **Theme Support**: Light and dark modes
- 🔌 **WebSocket Integration**: Real-time communication
- 📱 **Mobile Responsive**: Works on all devices

### UI Setup (Optional)

If you want the web UI, you'll need to set it up manually since it's not included in this repository:

```bash
# 1. Create the directory structure
mkdir -p NeMo-Agent-Toolkit-develop/external

# 2. Clone the UI repository
git clone https://github.com/NVIDIA/NeMo-Agent-Toolkit-UI.git NeMo-Agent-Toolkit-develop/external/nat-ui

# 3. Install dependencies
cd NeMo-Agent-Toolkit-develop/external/nat-ui
npm ci

# 4. Start the UI development server
npm run dev
```

**Or use the automated setup script:**
```bash
./dev.sh ui-setup  # Automatically clones and sets up the UI
./dev.sh ui        # Starts the UI server
```

The UI will be available at `http://localhost:3000`

### Alternative: Use API Documentation

If you don't want to set up the full UI, you can use the built-in API documentation interface at `http://localhost:8000/docs` when running the backend. This provides a simpler way to test your agent.

## Key Features Demonstrated

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

### Environment Variables

This demo uses a `.env` file for secure API key management:

1. **Copy the template**: `cp .env.example .env`
2. **Edit `.env`** with your actual API keys:
   - `NVIDIA_API_KEY`: Required for LLM access
   - `OPENWEATHERMAP_API_KEY`: Optional for weather functionality
3. **Never commit `.env`** - it's automatically ignored by Git

The demo automatically loads environment variables using `python-dotenv`.

### Development with uv

This project uses [uv](https://docs.astral.sh/uv/) for fast dependency management:

```bash
# Create virtual environment
uv venv

# Install dependencies
uv pip install -e personal_assistant_demo/

# Add new dependencies
uv add requests>=2.31.0

# Run commands in the virtual environment
uv run nat --help
uv run pytest tests/

# Sync dependencies (if using uv.lock)
uv sync
```

#### Development Helper Script

Use the `dev.sh` script for common development tasks:

```bash
./dev.sh setup     # Initial setup
./dev.sh test      # Run tests
./dev.sh run       # Run demo with sample query
./dev.sh serve     # Start web UI
./dev.sh clean     # Clean virtual environment
./dev.sh help      # Show all commands
```

## Development

### Running Tests

**Demo Tests**:
```bash
cd personal_assistant_demo
uv run pytest tests/
# or with activated venv: python -m pytest tests/
```

### Code Quality

The project uses:
- **Ruff**: Code formatting and linting
- **Type Hints**: Full type annotation support
- **Logging**: Comprehensive logging throughout
- **Error Handling**: Graceful error management

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Documentation

- **[NeMo Agent Toolkit Documentation](https://docs.nvidia.com/nemo/agent-toolkit/latest)**
- **[GitHub Repository](https://github.com/NVIDIA/NeMo-Agent-Toolkit)**
- **[Official Examples](https://github.com/NVIDIA/NeMo-Agent-Toolkit/tree/main/examples)**
- **[API Reference](https://docs.nvidia.com/nemo/agent-toolkit/latest/reference/)**

## License

This project is licensed under the Apache License 2.0. See the [NeMo Agent Toolkit LICENSE](https://github.com/NVIDIA/NeMo-Agent-Toolkit/blob/main/LICENSE.md) for details.

## Support

- **GitHub Issues**: [NeMo Agent Toolkit Issues](https://github.com/NVIDIA/NeMo-Agent-Toolkit/issues)
- **Documentation**: [Official Docs](https://docs.nvidia.com/nemo/agent-toolkit/latest)
- **Community**: Join the NVIDIA Developer community

---

**NVIDIA NeMo Agent Toolkit** - Build intelligent agents with ease.
