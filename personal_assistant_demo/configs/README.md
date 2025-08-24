# Configuration Files

This demo includes two main configuration files:

## 🌐 **config.yml** - Cloud LLM (NIM)
**Default configuration** using NVIDIA's NIM cloud service with Llama 3.1 70B.

### Easy Model Switching
To use a different model, simply change the `model` field:

```yaml
llms:
  nvidia_llm:
    model: meta/llama-3.1-8b-instruct    # Faster, more cost-effective
    # model: mistralai/mistral-7b-instruct-v0.3  # Excellent for structured outputs
```

**Popular NIM models with function calling support:**
- `meta/llama-3.1-70b-instruct` ✅ (recommended - best balance)
- `meta/llama-3.1-8b-instruct` ✅ (faster, cheaper)
- `mistralai/mistral-7b-instruct-v0.3` ✅ (great for structured outputs)

## 🏠 **config-ollama.yml** - Local LLM 
Uses Ollama for **completely offline** operation with Qwen 2.5.

**Requirements:**
- Ollama installed locally
- Qwen model downloaded: `ollama pull qwen2.5:7b`

## 🚀 Usage

```bash
# Cloud NIM (recommended)
nat run --config_file configs/config.yml --input "your query"

# Local Ollama
nat run --config_file configs/config-ollama.yml --input "your query"

# Demo script
python demo/demo_showcase.py --config configs/config.yml
```

## 🔑 Environment Setup

For NIM cloud models, set your API key:
```bash
export NVIDIA_API_KEY="your-api-key-here"
```

Get your free API key at [build.nvidia.com](https://build.nvidia.com/)
