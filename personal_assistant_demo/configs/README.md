# Configuration Files

This demo includes several configuration files optimized for different use cases:

## 🌐 NIM Configurations (Cloud LLM)

### 1. `config.yml`
Base configuration using NVIDIA's NIM cloud service. Used primarily with CLI commands.

### 2. `config-nim-tool-calling-conversation.yml`
Enhanced configuration for the web UI using NIM with tool-calling capabilities and conversation memory.

### 3. `config-nim-react-fixed.yml`
Web UI configuration using NIM with ReAct agent for structured reasoning.

## 🏠 Ollama Configurations (Local LLM)

### 1. `config-ollama-react-enhanced.yml`
Primary configuration for web UI using Ollama with enhanced ReAct capabilities and conversation memory.

### 2. `config-ollama-tool-calling.yml`
Alternative web UI configuration using Ollama with direct tool-calling approach.

## 🚀 Usage

### Web Interface
```bash
# Run with Ollama (default)
python run_web_demo.py

# Run with NIM
python run_web_demo.py --nim

# Run with specific config
python run_web_demo.py --config configs/config-ollama-tool-calling.yml
```

### CLI Usage
```bash
# Using NIM (recommended for production)
nat run --config_file configs/config.yml --input "your query"

# Using Ollama (local development)
nat run --config_file configs/config-ollama-react-enhanced.yml --input "your query"
```

## 🔧 Requirements

### For NIM (Cloud)
1. Get your API key from [build.nvidia.com](https://build.nvidia.com/)
2. Set environment variable:
```bash
export NVIDIA_API_KEY="your-api-key-here"
```

### For Ollama (Local)
1. Install Ollama: [ollama.ai](https://ollama.ai)
2. Pull the Qwen model:
```bash
ollama pull qwen2.5:7b
```

## 🎯 Choosing the Right Configuration

1. **For Production/Enterprise:**
   - Use NIM configurations (`config.yml` or `config-nim-tool-calling-conversation.yml`)
   - Benefits: Better performance, no local GPU required, maintained by NVIDIA

2. **For Local Development/Testing:**
   - Use Ollama configurations (`config-ollama-react-enhanced.yml`)
   - Benefits: No API key needed, works offline, free to use

3. **For Web UI:**
   - Default (Ollama): `config-ollama-react-enhanced.yml`
   - Cloud (NIM): `config-nim-tool-calling-conversation.yml`
   - You can switch between ReAct and Tool-calling modes in the UI