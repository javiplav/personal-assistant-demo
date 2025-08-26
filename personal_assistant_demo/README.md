<!--
SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# Personal Assistant Agent Demo

A comprehensive demonstration of the NeMo Agent Toolkit featuring a personal assistant agent that can help with daily tasks. This demo showcases the toolkit's key capabilities including custom function registration, multi-step reasoning, and framework-agnostic design.

## Table of Contents

- [Key Features](#key-features)
- [Installation and Setup](#installation-and-setup)
- [Running the Demo](#running-the-demo)
- [Example Interactions](#example-interactions)
- [Architecture Overview](#architecture-overview)
- [Customization](#customization)

---

## Key Features

### **Enterprise Solutions Architect Tools**
- **Client Management:** Add, track, and manage clients with CRM-like capabilities
- **Meeting Scheduler:** Schedule, manage, and coordinate meetings with participants
- **Task Management:** Create, list, and complete tasks with intelligent workflow orchestration
- **Business Intelligence:** Perform calculations, track metrics, and generate reports

### **Core Functionality**
- **Mathematical Operations:** Perform basic calculations (add, subtract, multiply, divide)
- **Date/Time Information:** Get current date, time, and timezone information
- **Weather Information:** Get current weather conditions for any city (requires API key)

### **Technical Excellence**
- **Multi-step Reasoning:** Uses ReAct agent to break down complex queries into sequential tool calls
- **Custom Function Registration:** Demonstrates the NeMo Agent Toolkit plugin system
- **YAML-based Configuration:** Fully configurable workflow through simple YAML files
- **Persistent Storage:** All data stored locally and persists between sessions
- **Enterprise Architecture:** Production-ready design with error handling and extensibility

---

## Installation and Setup

### Prerequisites

1. Python 3.11 or 3.12 installed
2. NeMo Agent Toolkit development environment set up
3. **Choose one LLM provider:**
   - **Ollama (Local)** - Recommended for beginners (no API key required)
   - **NVIDIA NIM (Cloud)** - For advanced users (requires API key)

### Install this Demo

From the root directory of this demo, run:

```bash
# Using uv (recommended - faster)
uv pip install -e .

# Or using pip
pip install -e .
```

### Set Up Your LLM Provider

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

**No API key required!** Ollama runs completely locally on your machine.

#### ☁️ **Option B: NVIDIA NIM (Cloud) - For Advanced Users**

**Get NVIDIA API Key:**
1. Visit [build.nvidia.com](https://build.nvidia.com/)
2. Sign up for an account
3. Get your API key from the dashboard

**Set up environment variables:**
```bash
# Create .env file
cp .env.example .env

# Edit .env file and add your API keys
export NVIDIA_API_KEY=<YOUR_NVIDIA_API_KEY>
export OPENWEATHERMAP_API_KEY=<YOUR_OPENWEATHERMAP_API_KEY>  # Optional
```

---

## Running the Demo

### 🏠 **With Ollama (Local) - Recommended**

**Quick test:**
```bash
nat run --config_file configs/config-ollama-react.yml --input "What time is it and add a task to review the demo?"
```

**Automated demo:**
```bash
python demo/demo_showcase.py
```

**Web UI experience:**
```bash
# Terminal 1: Start Ollama (if not already running)
ollama serve

# Terminal 2: Start the enhanced web demo (single command)
# Note: Do NOT run 'nat serve' and 'run_web_demo.py' at the same time (port conflict)
python run_web_demo.py            # Ollama ReAct (default) - Full web UI
# or
python run_web_demo.py --nim      # NIM tool-calling - Full web UI
```

### ☁️ **With NVIDIA NIM (Cloud)**

**Quick test:**
```bash
nat run --config_file configs/config.yml --input "What time is it and add a task to review the demo?"
```

**Web UI experience:**
Use the same launcher with `--nim`:
```bash
# Note: Do NOT run 'nat serve' and 'run_web_demo.py' at the same time (port conflict)
python run_web_demo.py --nim      # Full web UI with NIM
```

### Using Development Helper Script

```bash
# Ollama commands
./dev.sh run-ollama    # Quick demo with Ollama
./dev.sh serve-ollama  # Web UI with Ollama

# NVIDIA commands
./dev.sh run           # Quick demo with NVIDIA NIM
./dev.sh serve         # Web UI with NVIDIA NIM
```

### Documentation

- **Examples**: `docs/examples.md` - Comprehensive usage examples
- **Project Structure**: `docs/PROJECT_ORGANIZATION.md` - Complete project guide
- **Demo Verification**: `demo/DEMO_VERIFICATION.md` - Functionality verification
- **Web Demo**: `run_web_demo.py` - Launch the FastAPI web UI

### ⚠️ **Important: Avoiding Port Conflicts**

**Two Different Servers:**
- `nat serve` - Creates a basic API server (no web interface) 
- `run_web_demo.py` - Creates a full web application with chat UI

**Common Mistake - Port Conflict:**
```bash
# ❌ This causes a port conflict:
nat serve --config_file configs/config-ollama-tool-calling.yml  # Starts on port 8000
python run_web_demo.py                                          # Tries to use port 8000 too!
# Result: Second command fails, browser shows "Not Found"
```

**✅ Correct Approaches:**

**Option 1: Use Only Web Demo (Recommended)**
```bash
# Stop any running nat serve command (Ctrl+C)
python run_web_demo.py                    # Full web UI on port 8000
```

**Option 2: Use Different Ports**  
```bash
# Terminal 1: Keep nat serve
nat serve --config_file configs/config-ollama-tool-calling.yml --port 8001

# Terminal 2: Run web demo on default port
python run_web_demo.py                    # Web UI on port 8000
```

**Option 3: Web Demo on Different Port**
```bash
# Keep nat serve on port 8000
nat serve --config_file configs/config-ollama-tool-calling.yml

# Run web demo on different port  
python run_web_demo.py --port 3000       # Web UI on port 3000
```

**When to Use Each:**
- **Web Demo Only**: Best for interactive demos and showcasing capabilities
- **nat serve**: For API development, testing, or integrating with other applications
- **Both**: When you need both API access and web interface simultaneously

### Recent Changes (Troubleshooting + Performance)
- Centralized data paths with safety checks in `src/personal_assistant/tools/_paths.py`
- Added DEBUG logging for `web_server.py` and `ToolCallingHandler` to profile ainvoke timings
- Tool-calling payload shape fixed to `{"input_message": "..."}`
- Configs tuned for demos (timeouts, top_p, max_tokens) for both Ollama and NIM
- ReAct configs updated to escape braces and enforce single JSON Action Inputs
- Meetings/tools now support filters and slimmer outputs to improve second-turn latency

---

## Example Interactions

For comprehensive examples, see `docs/examples.md`.

Here are some example queries you can try:

### **Enterprise Solutions Architect Workflows**
- "Add client Microsoft with GPU cluster requirements, priority high"
- "Schedule technical review meeting tomorrow 10 AM for 2 hours"
- "Add task to prepare cost analysis by Friday"
- "Show me all high-priority clients and their meetings"

### **Client Management**
- "Add client TechCorp with requirements: AI infrastructure assessment"
- "List all high-priority clients"
- "Add note to client 1: Had productive call about implementation timeline"
- "Show me details for client Microsoft"

### **Meeting Coordination**
- "Schedule meeting with John and Sarah tomorrow 2 PM for 1 hour, title: AI Review"
- "Show me all meetings this week"
- "Cancel meeting 1, reason: Client requested reschedule"

### **Task Management**
- "Add a task to buy groceries"
- "List all my tasks"
- "Mark the grocery task as completed"
- "Create a task to call mom tomorrow"

### **Business Intelligence**
- "Calculate 20% of 500000 for project budget"
- "What's 15 multiplied by 8?"
- "Calculate 100 divided by 4"

### **Date/Time**
- "What time is it?"
- "What's today's date?"
- "What timezone am I in?"

### **Weather Queries (requires OpenWeatherMap API key)**
- "What's the weather like in San Francisco?"
- "Is it raining in London right now?"
- "What's the temperature in Tokyo?"

### **Complex Multi-step Queries**
- "Add client Fortune500 with multi-cloud requirements, schedule executive presentation next Friday 9 AM for 3 hours, add task to prepare ROI analysis, calculate 20% of 1000000 for project budget"
- "What's the weather in Paris and add a task to pack an umbrella if it's going to rain"
- "Calculate 20% of 150 and create a task to save that amount"

---

## Architecture Overview

This demo follows NeMo Agent Toolkit best practices:

```
personal_assistant_demo/
├── src/
│   └── personal_assistant/
│       ├── __init__.py
│       ├── register.py          # Custom function registration
│       └── tools/
│           ├── weather.py       # Weather API integration
│           ├── tasks.py         # Task management functions
│           ├── calculator.py    # Mathematical operations
│           └── datetime_info.py # Date/time utilities
├── configs/
│   ├── config.yml              # NVIDIA NIM configuration (cloud)
│   ├── config-ollama-react.yml # Ollama ReAct configuration
│   ├── config-ollama-tool-calling.yml # Ollama tool-calling configuration
│   ├── config-nim-react.yml    # NIM ReAct configuration
│   └── config-nim-tool-calling.yml # NIM tool-calling configuration
├── tests/
│   ├── test_weather.py
│   ├── test_tasks.py
│   └── test_calculator.py
├── data/
│   └── tasks.json              # Persistent task storage
├── pyproject.toml              # Package configuration
└── README.md
```

### Key Components

1. **Custom Functions**: Each tool is implemented as a custom function following NAT conventions
2. **ReAct Agent**: Uses reasoning and action cycles to handle complex queries
3. **Plugin System**: Functions are registered through the NAT plugin system
4. **Configuration**: All behavior is controlled through YAML configuration
5. **Persistence**: Tasks are stored in JSON format for persistence between sessions

---

## Configuration Options

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

---

## Customization

### Adding New Tools

To add a new tool:

1. Create a new function in `src/personal_assistant/tools/`
2. Register it in `src/personal_assistant/register.py`
3. Add it to the workflow configuration in `configs/config.yml`

### Modifying the Agent

You can customize the agent behavior by:

- Changing the LLM model in the configuration
- Adjusting the agent's system prompt
- Adding or removing tools from the workflow
- Modifying the agent type (ReAct, Tool Calling, etc.)

### Configuration Options

The configuration files allow you to:

- Switch between different LLM providers (NVIDIA NIM, Ollama, etc.)
- Adjust model parameters (temperature, max tokens)
- Enable/disable specific tools
- Configure tool-specific settings

---

## Troubleshooting

### Common Issues

1. **Port Conflicts**: If you get "Not Found" in browser, you may have both `nat serve` and `run_web_demo.py` trying to use port 8000. See the [Port Conflicts section](#️-important-avoiding-port-conflicts) above for solutions.
2. **Ollama Connection Issues**: Ensure Ollama is running with `ollama serve`
3. **NVIDIA API Key Issues**: Ensure your NVIDIA_API_KEY is set correctly
4. **Weather Not Working**: Check your OPENWEATHERMAP_API_KEY or disable weather tools
5. **Data Path Safety**: All tools read/write via `tools/_paths.py`; ensure the `data/` directory is writable
6. **Import Errors**: Make sure you've installed the package with `pip install -e .`

### Getting Help

- Check the [NeMo Agent Toolkit Documentation](https://docs.nvidia.com/nemo/agent-toolkit/latest)
- Review the [Troubleshooting Guide](https://docs.nvidia.com/nemo/agent-toolkit/latest/troubleshooting.html)
- File issues on the [GitHub Repository](https://github.com/NVIDIA/NeMo-Agent-Toolkit/issues)

---

## License

This demo is licensed under the Apache License 2.0. See the LICENSE file for details.
