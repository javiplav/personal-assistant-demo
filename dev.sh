#!/bin/bash

# Development helper script for uv commands
# Usage: ./dev.sh [command]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv is not installed. Please install it first:${NC}"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Function to show usage
show_usage() {
    echo -e "${BLUE}🛠️  Development Helper Script${NC}"
    echo ""
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup     - Initial setup (create venv, install deps)"
    echo "  install   - Install/reinstall the demo package"
    echo "  test      - Run tests"
    echo "  run       - Run the demo with a sample query (NVIDIA NIM)"
    echo "  run-ollama - Run the demo with Ollama local LLM"
    echo "  serve     - Start the web UI (NVIDIA NIM)"
    echo "  serve-ollama - Start the web UI with Ollama local LLM"
    echo "  ui        - Start the web UI (requires backend running)"
    echo "  ui-setup  - Set up the web UI (install dependencies)"
    echo "  shell     - Activate the virtual environment"
    echo "  clean     - Clean up virtual environment"
    echo "  deps      - Show installed dependencies"
    echo ""
}

# Main command handling
case "${1:-help}" in
    "setup")
        echo -e "${GREEN}🚀 Setting up development environment...${NC}"
        uv venv
        echo -e "${GREEN}📦 Installing demo package...${NC}"
        cd personal_assistant_demo
        uv pip install -e .
        cd ..
        echo -e "${GREEN}✅ Setup complete!${NC}"
        echo -e "${YELLOW}💡 Don't forget to edit .env with your API keys${NC}"
        ;;
    
    "install")
        echo -e "${GREEN}📦 Installing demo package...${NC}"
        cd personal_assistant_demo
        uv pip install -e .
        cd ..
        echo -e "${GREEN}✅ Installation complete!${NC}"
        ;;
    
    "test")
        echo -e "${GREEN}🧪 Running tests...${NC}"
        cd personal_assistant_demo
        uv run pytest tests/ -v
        cd ..
        ;;
    
    "run")
        echo -e "${GREEN}🤖 Running demo...${NC}"
        cd personal_assistant_demo
        uv run nat run --config_file configs/config.yml --input "What time is it and what's 15 + 27?"
        cd ..
        ;;
    
    "run-ollama")
        echo -e "${GREEN}🤖 Running demo with Ollama...${NC}"
        echo -e "${YELLOW}💡 Make sure Ollama is running: ollama serve${NC}"
        cd personal_assistant_demo
        uv run nat run --config_file configs/config-ollama.yml --input "What time is it and what's 15 + 27?"
        cd ..
        ;;
    
    "serve")
        echo -e "${GREEN}🌐 Starting web UI...${NC}"
        echo -e "${YELLOW}💡 Open http://localhost:8000 in your browser${NC}"
        cd personal_assistant_demo
        uv run nat serve --config_file configs/config.yml
        cd ..
        ;;
    
    "serve-ollama")
        echo -e "${GREEN}🌐 Starting web UI with Ollama...${NC}"
        echo -e "${YELLOW}💡 Make sure Ollama is running: ollama serve${NC}"
        echo -e "${YELLOW}💡 Open http://localhost:8000 in your browser${NC}"
        cd personal_assistant_demo
        uv run nat serve --config_file configs/config-ollama.yml
        cd ..
        ;;
    
    "shell")
        echo -e "${GREEN}🐚 Activating virtual environment...${NC}"
        echo "Run: source .venv/bin/activate"
        ;;
    
    "clean")
        echo -e "${YELLOW}🧹 Cleaning up virtual environment...${NC}"
        rm -rf .venv
        echo -e "${GREEN}✅ Virtual environment removed${NC}"
        ;;
    
    "ui-setup")
        if [ ! -d "NeMo-Agent-Toolkit-develop/external/nat-ui" ]; then
            echo -e "${YELLOW}🎨 UI not found. Cloning NeMo Agent Toolkit UI...${NC}"
            git clone https://github.com/NVIDIA/NeMo-Agent-Toolkit-UI.git NeMo-Agent-Toolkit-develop/external/nat-ui
        fi
        echo -e "${GREEN}🎨 Setting up Web UI...${NC}"
        cd NeMo-Agent-Toolkit-develop/external/nat-ui
        npm ci
        echo -e "${GREEN}✅ UI setup complete!${NC}"
        echo -e "${YELLOW}💡 Run './dev.sh ui' to start the UI${NC}"
        cd ../../..
        ;;
    
    "ui")
        if [ ! -d "NeMo-Agent-Toolkit-develop/external/nat-ui" ]; then
            echo -e "${RED}❌ UI not found!${NC}"
            echo -e "${YELLOW}💡 Run './dev.sh ui-setup' first to install the UI${NC}"
            exit 1
        fi
        echo -e "${GREEN}🎨 Starting Web UI...${NC}"
        echo -e "${YELLOW}💡 Make sure the backend is running first:${NC}"
        echo -e "${YELLOW}   ./dev.sh serve (for NVIDIA NIM)${NC}"
        echo -e "${YELLOW}   ./dev.sh serve-ollama (for Ollama)${NC}"
        echo ""
        echo -e "${YELLOW}💡 UI will be available at: http://localhost:3000${NC}"
        cd NeMo-Agent-Toolkit-develop/external/nat-ui
        npm run dev
        cd ../../..
        ;;
    
    "deps")
        echo -e "${GREEN}📋 Installed dependencies:${NC}"
        uv pip list
        ;;
    
    "help"|*)
        show_usage
        ;;
esac
