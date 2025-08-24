# Demo Configuration Guide

The Personal Assistant Demo supports multiple LLM configurations. This guide explains how to run the demo with different setups.

## 🚀 Quick Start

### Default (Ollama - Recommended for Local Development)
```bash
# Run with default Ollama configuration
python demo/demo_showcase.py

# Or explicitly specify
python demo/demo_showcase.py --config configs/config-ollama.yml
```

### NIM (Cloud-based - Recommended for Production)
```bash
# Set your NVIDIA API key first
export NVIDIA_API_KEY="your_api_key_here"

# Run with NIM configuration
python demo/demo_showcase.py --config configs/config.yml
```

### Ollama with Environment Variables
```bash
# Optional: Set custom Ollama settings
export OLLAMA_BASE_URL="http://localhost:11434/v1"
export OLLAMA_MODEL="qwen2.5:7b"

# Run with environment-based config
python demo/demo_showcase.py --config configs/config-ollama-env.yml
```

## 📋 Configuration Details

### 1. `configs/config-ollama.yml` (Default)
- **LLM Backend**: Ollama (Local)
- **Model**: qwen2.5:7b
- **Requirements**: 
  - Ollama running locally
  - qwen2.5:7b model downloaded (`ollama pull qwen2.5:7b`)
- **Benefits**: 
  - ✅ Privacy (fully local)
  - ✅ No API costs
  - ✅ Fast response times
  - ✅ Works offline

### 2. `configs/config.yml` (NIM)
- **LLM Backend**: NVIDIA NIM
- **Model**: nvidia/llama-3.1-nemotron-70b-instruct
- **Requirements**: 
  - Valid NVIDIA API key
  - Internet connection
- **Benefits**: 
  - ✅ Enterprise-grade model (70B parameters)
  - ✅ Optimized for tool calling
  - ✅ No local compute requirements
  - ✅ Production-ready scalability

### 3. `configs/config-ollama-env.yml` (Flexible Ollama)
- **LLM Backend**: Ollama (Local with Environment Variables)
- **Model**: Configurable via `OLLAMA_MODEL`
- **Requirements**: 
  - Ollama running locally
  - Model specified in environment
- **Benefits**: 
  - ✅ Flexible model selection
  - ✅ Environment-based configuration
  - ✅ Easy deployment variations

## 🛠️ Setup Instructions

### For Ollama Configurations

1. **Install Ollama**
   ```bash
   # macOS
   brew install ollama
   
   # Or download from https://ollama.ai
   ```

2. **Start Ollama Service**
   ```bash
   ollama serve
   ```

3. **Download Required Model**
   ```bash
   ollama pull qwen2.5:7b
   ```

4. **Verify Installation**
   ```bash
   ollama list  # Should show qwen2.5:7b
   ```

### For NIM Configuration

1. **Get NVIDIA API Key**
   - Visit [NVIDIA Developer Portal](https://developer.nvidia.com/)
   - Create account and generate API key

2. **Set Environment Variable**
   ```bash
   # Add to your ~/.zshrc or ~/.bashrc
   export NVIDIA_API_KEY="your_api_key_here"
   
   # Or set temporarily
   export NVIDIA_API_KEY="your_api_key_here"
   ```

3. **Test API Access**
   ```bash
   curl -H "Authorization: Bearer $NVIDIA_API_KEY" \
        https://integrate.api.nvidia.com/v1/models
   ```

## 🔧 Troubleshooting

### Ollama Issues

**Problem**: `Ollama is not running`
```bash
# Solution: Start Ollama service
ollama serve
```

**Problem**: `qwen2.5 model not found`
```bash
# Solution: Download the model
ollama pull qwen2.5:7b
```

**Problem**: `Connection refused to localhost:11434`
```bash
# Check if Ollama is running
ps aux | grep ollama

# Restart Ollama
ollama serve
```

### NIM Issues

**Problem**: `[401] Unauthorized`
```bash
# Solution: Set valid API key
export NVIDIA_API_KEY="your_valid_key"
```

**Problem**: `API key is required for the hosted NIM`
```bash
# Solution: Check environment variable
echo $NVIDIA_API_KEY

# Set if missing
export NVIDIA_API_KEY="your_api_key"
```

### General Issues

**Problem**: `Command failed with return code 1`
```bash
# Check NAT installation
nat --version

# Reinstall if needed
pip install nemo-agent-toolkit
```

**Problem**: `find_client_by_name not found`
```bash
# Ensure you're using updated configurations
# All configs should include find_client_by_name in functions and tool_names
```

## 🎯 Choosing the Right Configuration

### Use **Ollama** (`config-ollama.yml`) when:
- 🏠 Developing locally
- 🔒 Privacy is important
- 💰 Want to avoid API costs
- 🌐 Working offline
- 🔧 Learning and experimentation

### Use **NIM** (`config.yml`) when:
- 🏢 Production deployment
- 💪 Need best model performance
- ☁️ Cloud-based infrastructure
- 📈 Scalability requirements
- 🚀 Enterprise features needed

### Use **Ollama + Env** (`config-ollama-env.yml`) when:
- 🔄 Multiple deployment environments
- 🎛️ Need configuration flexibility
- 📦 Container-based deployment
- 🔧 CI/CD pipeline integration

## 📊 Performance Comparison

| Configuration | Response Time | Model Size | Setup Complexity | Cost |
|---------------|---------------|------------|------------------|------|
| Ollama        | ~8-12s        | 7B params  | Medium          | Free |
| NIM           | ~3-8s         | 70B params | Low             | Pay-per-use |
| Ollama + Env  | ~8-12s        | Variable   | Medium          | Free |

## 🎉 Success Indicators

When everything is working correctly, you should see:

```
🚀 NeMo Agent Toolkit: Enterprise Solutions Architect Demo
=================================================================
📋 Configuration: [Your Config Type]
🔧 Config File: [Your Config File]
=================================================================

🔍 Validating system requirements...

1️⃣ Checking [LLM Service]...
   ✅ [Service] is running with model: [model_name]
2️⃣ Checking NAT installation...
   ✅ NAT is working correctly
3️⃣ Configuration validated
   ✅ Test result: [Calculation result]

🎉 All systems ready! Starting enterprise demo...
```

## 📞 Support

If you encounter issues:

1. Check this troubleshooting guide
2. Verify your configuration matches the examples
3. Test with a simple calculation first
4. Check logs for specific error messages
5. Ensure all dependencies are installed

For more help, refer to the main [README.md](../README.md) or NVIDIA NeMo Agent Toolkit documentation.
