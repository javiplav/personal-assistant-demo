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

# Create virtual environment and install dependencies
echo "🔧 Creating virtual environment with uv..."
uv venv

echo "📦 Installing demo package with dependencies..."
cd personal_assistant_demo
uv pip install -e .
cd ..

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
echo "   4. Activate virtual environment:"
echo "      source .venv/bin/activate  # On macOS/Linux"
echo "      # or .venv\\Scripts\\activate  # On Windows"
echo "   5. Run the demo:"
echo "      cd personal_assistant_demo"
echo "      nat run --config_file configs/config-ollama.yml --input \"What time is it?\""
echo ""
echo "☁️  Option B: NVIDIA NIM (Cloud) - For advanced users"
echo "   1. Get NVIDIA API key from https://build.nvidia.com/"
echo "   2. Edit .env file and add your NVIDIA_API_KEY"
echo "   3. Activate virtual environment:"
echo "      source .venv/bin/activate  # On macOS/Linux"
echo "      # or .venv\\Scripts\\activate  # On Windows"
echo "   4. Run the demo:"
echo "      cd personal_assistant_demo"
echo "      nat run --config_file configs/config.yml --input \"What time is it?\""
echo ""
echo "🌐 Web UI Experience (Optional):"
echo "   # Terminal 1: Start backend"
echo "   nat serve --config_file configs/config-ollama.yml  # For Ollama"
echo "   # or nat serve --config_file configs/config.yml    # For NVIDIA NIM"
echo "   # Terminal 2: Start web UI"
echo "   ./dev.sh ui-setup  # First time setup"
echo "   ./dev.sh ui        # Start the UI"
echo "   # Then open http://localhost:3001"
echo ""
echo "💡 Tips:"
echo "   - Use './dev.sh run-ollama' for quick Ollama demo"
echo "   - Use './dev.sh run' for quick NVIDIA NIM demo"
echo "   - Use './dev.sh help' to see all available commands"
echo "   - Use './dev.sh ui-setup' if UI setup was skipped"
echo ""
