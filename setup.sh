#!/bin/bash

# Personal Assistant Demo Setup Script
# This script helps you set up the demo environment using uv

set -e

echo "🚀 Setting up Personal Assistant Demo with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   or visit: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo "✅ uv is installed"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "🔑 API Key Setup:"
    echo "   This demo supports two LLM providers:"
    echo ""
    echo "   🏠 Ollama (Local) - Recommended for beginners:"
    echo "      ✅ No API key required"
    echo "      ✅ Privacy-focused, runs locally"
    echo "      ✅ Free to use"
    echo "      ❌ Requires local setup"
    echo ""
    echo "   ☁️  NVIDIA NIM (Cloud) - For advanced users:"
    echo "      ✅ More powerful models"
    echo "      ✅ No local setup required"
    echo "      ❌ Requires NVIDIA API key"
    echo "      ❌ Network dependency and potential costs"
    echo ""
    echo "   If using NVIDIA NIM, edit .env file and add:"
    echo "   - NVIDIA_API_KEY (required for cloud LLM)"
    echo "   - OPENWEATHERMAP_API_KEY (optional for weather)"
    echo ""
else
    echo "✅ .env file already exists"
fi

# Handle conda interference (common issue)
echo "🔍 Checking for conda interference..."
if [[ "$CONDA_DEFAULT_ENV" != "" ]] || [[ "$CONDA_PREFIX" != "" ]]; then
    echo "⚠️  Conda environment detected: ${CONDA_DEFAULT_ENV:-$CONDA_PREFIX}"
    echo "   This may cause pip/python conflicts. Deactivating conda..."
    # Try to deactivate conda if it's active
    if command -v conda &> /dev/null; then
        conda deactivate 2>/dev/null || true
        # Unset conda environment variables to prevent interference
        unset CONDA_DEFAULT_ENV
        unset CONDA_PREFIX
        unset CONDA_PYTHON_EXE
        unset CONDA_EXE
        echo "   ✅ Conda deactivated and environment variables cleared"
    fi
else
    echo "✅ No conda interference detected"
fi

# Create virtual environment and install dependencies
echo "🔧 Creating clean virtual environment with uv..."
# Remove any existing broken venv
if [ -d ".venv" ]; then
    echo "   🧹 Removing existing virtual environment..."
    rm -rf .venv
fi
uv venv

echo "📦 Installing demo package with dependencies using uv pip..."
echo "   🐍 Target Python: $(realpath .venv/bin/python)"
cd personal_assistant_demo
# Use uv pip with explicit python path to avoid conda interference
uv pip install --python ..//.venv/bin/python -e .
cd ..

# Verify the installation works
echo "🧪 Verifying installation..."
if .venv/bin/python -c "import uvicorn, fastapi, personal_assistant; print('✅ Core dependencies verified')" 2>/dev/null; then
    echo "✅ Installation verification successful!"
else
    echo "❌ Installation verification failed. Dependencies may not be properly installed."
    echo "💡 Try running the commands manually:"
    echo "   cd personal_assistant_demo && uv pip install -e ."
    exit 1
fi

echo "🎨 Setting up Web UI..."
if [ -d "NeMo-Agent-Toolkit-develop/external/nat-ui" ]; then
    cd NeMo-Agent-Toolkit-develop/external/nat-ui
    if [ -f "package.json" ]; then
        echo "📦 Installing UI dependencies..."
        npm ci
        echo "✅ UI setup complete!"
    else
        echo "⚠️  UI package.json not found, skipping UI setup"
    fi
    cd ../../..
else
    echo "⚠️  UI directory not found, skipping UI setup"
    echo "💡 The UI may not be available until you clone it manually"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "🚀 Next steps - Choose your LLM provider:"
echo ""
echo "🏠 Option A: Ollama (Local) - Recommended for beginners"
echo "   1. Install Ollama: curl -fsSL https://ollama.com/install.sh | sh"
echo "   2. Start Ollama: ollama serve"
echo "   3. Pull a model: ollama pull qwen2.5:7b"
echo "   4. Activate virtual environment (REQUIRED for every session):"
echo "      source .venv/bin/activate  # On macOS/Linux"
echo "      # or .venv\\Scripts\\activate  # On Windows"
echo "   5. Run quick test:"
echo "      cd personal_assistant_demo"
echo "      nat run --config_file configs/config-ollama-react.yml --input \"What time is it?\""
echo "   6. Or run the full web interface:"
echo "      python run_web_demo.py  # Full web UI with chat interface"
echo ""
echo "☁️  Option B: NVIDIA NIM (Cloud) - For advanced users"
echo "   1. Get NVIDIA API key from https://build.nvidia.com/"
echo "   2. Edit .env file and add your NVIDIA_API_KEY"
echo "   3. Activate virtual environment (REQUIRED for every session):"
echo "      source .venv/bin/activate  # On macOS/Linux"
echo "      # or .venv\\Scripts\\activate  # On Windows"
echo "   4. Run quick test:"
echo "      cd personal_assistant_demo"
echo "      nat run --config_file configs/config.yml --input \"What time is it?\""
echo "   5. Or run the full web interface:"
echo "      python run_web_demo.py --nim  # Full web UI with cloud LLM"
echo ""
echo "🌐 Web UI Experience (Recommended):"
echo "   ⚠️  IMPORTANT: Don't run 'nat serve' and 'run_web_demo.py' together (port conflict)"
echo "   ✅ Use ONLY the web demo for the best experience:"
echo "      source .venv/bin/activate              # Activate environment"
echo "      cd personal_assistant_demo             # Navigate to demo"
echo "      python run_web_demo.py                 # For Ollama"
echo "      # or python run_web_demo.py --nim     # For NVIDIA NIM"
echo "   📱 Then open: http://localhost:8000"
echo ""
echo "💡 Tips:"
echo "   - ALWAYS activate virtual environment: source .venv/bin/activate"
echo "   - For conda users: The setup script handles conda deactivation automatically"
echo "   - Use './dev.sh run-ollama' for quick Ollama demo"
echo "   - Use './dev.sh run' for quick NVIDIA NIM demo"
echo "   - Use './dev.sh help' to see all available commands"
echo "   - If you get 'uvicorn not found' error, verify you activated the virtual environment"
echo ""
