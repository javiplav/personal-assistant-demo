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
    echo "⚠️  Please edit .env file and add your API keys:"
    echo "   - NVIDIA_API_KEY (required)"
    echo "   - OPENWEATHERMAP_API_KEY (optional)"
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
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Activate the virtual environment:"
echo "   source .venv/bin/activate  # On macOS/Linux"
echo "   # or .venv\\Scripts\\activate  # On Windows"
echo ""
echo "3. Run the demo:"
echo "   cd personal_assistant_demo"
echo "   nat run --config_file configs/config.yml --input \"What time is it?\""
echo ""
echo "4. Or start the full web UI experience:"
echo "   # Terminal 1: Start backend"
echo "   nat serve --config_file configs/config.yml"
echo "   # Terminal 2: Start web UI"
echo "   ./dev.sh ui"
echo "   # Then open http://localhost:3001"
echo ""
echo "💡 Tips:"
echo "   - Use 'uv pip install <package>' for faster package installation"
echo "   - Use './dev.sh help' to see all available commands"
echo "   - Use './dev.sh ui-setup' if UI setup was skipped"
echo ""
