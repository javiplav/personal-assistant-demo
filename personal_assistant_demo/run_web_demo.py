#!/usr/bin/env python3
"""
NVIDIA NeMo Agent Toolkit - Web Demo Launcher

This script launches the enhanced web interface for the Personal Assistant demo,
showcasing real-time agent interactions and enterprise capabilities.

Usage:
    python run_web_demo.py                    # Run with Ollama (default)
    python run_web_demo.py --nim              # Run with NVIDIA NIM
    python run_web_demo.py --config custom.yml # Run with custom config
"""

import argparse
import asyncio
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import uvicorn
import requests


def check_ollama_status():
    """Check if Ollama is running and ready."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            qwen_models = [m for m in models if 'qwen' in m.get('name', '').lower()]
            if qwen_models:
                return {"status": "ready", "model": qwen_models[0]['name']}
            else:
                return {"status": "no_model", "models": [m.get('name', '') for m in models]}
        return {"status": "error", "message": f"Ollama returned status {response.status_code}"}
    except requests.exceptions.RequestException:
        return {"status": "not_running"}


def check_nvidia_api_key():
    """Check if NVIDIA API key is configured."""
    return bool(os.environ.get('NVIDIA_API_KEY') or os.environ.get('OPENAI_API_KEY'))


def setup_environment():
    """Setup the Python environment and install dependencies."""
    print("🔧 Setting up environment...")
    
    try:
        # Check if we're in the right directory
        if not Path("pyproject.toml").exists():
            print("❌ Please run this script from the personal_assistant_demo directory")
            return False
        
        # Install the demo package
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", "."
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Failed to install package: {result.stderr}")
            return False
        
        print("✅ Environment setup complete")
        return True
        
    except Exception as e:
        print(f"❌ Environment setup failed: {e}")
        return False


async def run_web_server(config_file: str, host: str = "0.0.0.0", port: int = 8000):
    """Run the web server with the specified configuration."""
    try:
        # Import the web server
        from personal_assistant.web_server import create_app
        
        # Create the FastAPI app
        app = create_app(config_file)
        
        print(f"🚀 Starting NeMo Agent Toolkit Web Demo")
        print(f"📁 Config: {config_file}")
        print(f"🌐 URL: http://localhost:{port}")
        print(f"📚 API Docs: http://localhost:{port}/docs")
        print("=" * 60)
        
        # Run the server
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="debug",
            access_log=False
        )
        server = uvicorn.Server(config)
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(2)  # Wait for server to start
            webbrowser.open(f"http://localhost:{port}")
        
        # Start browser in background
        import threading
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Start server
        await server.serve()
        
    except Exception as e:
        print(f"❌ Failed to start web server: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="NVIDIA NeMo Agent Toolkit - Enhanced Web Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with Ollama (local LLM)
  python run_web_demo.py
  
  # Run with NVIDIA NIM (cloud LLM)
  python run_web_demo.py --nim
  
  # Run with custom configuration
  python run_web_demo.py --config configs/my_config.yml
  
  # Run on different port
  python run_web_demo.py --port 3000
        """
    )
    
    parser.add_argument(
        "--config",
        default=None,
        help="Configuration file to use"
    )
    
    parser.add_argument(
        "--nim",
        action="store_true",
        help="Use NVIDIA NIM configuration (requires API key)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the web server on (default: 8000)"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't automatically open browser"
    )
    
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Setup environment and install dependencies"
    )
    
    args = parser.parse_args()
    
    # Setup environment if requested
    if args.setup:
        if not setup_environment():
            sys.exit(1)
        return
    
    # Determine config file
    if args.config:
        config_file = args.config
    elif args.nim:
        config_file = "configs/config-nim-tool-calling.yml"  # Use the NIM tool-calling config
    else:
        config_file = "configs/config-ollama-react.yml"
    
    # Validate configuration
    if not Path(config_file).exists():
        print(f"❌ Configuration file not found: {config_file}")
        sys.exit(1)
    
    print("🎯 NVIDIA NeMo Agent Toolkit - Enhanced Web Demo")
    print("=" * 60)
    
    # Check LLM backend
    if "ollama" in config_file:
        print("🔍 Checking Ollama status...")
        ollama_status = check_ollama_status()
        
        if ollama_status["status"] == "ready":
            print(f"   ✅ Ollama ready with model: {ollama_status['model']}")
        elif ollama_status["status"] == "no_model":
            print("   ❌ Ollama running but no suitable model found")
            print("   💡 Run: ollama pull qwen2.5:7b")
            sys.exit(1)
        else:
            print("   ❌ Ollama not running")
            print("   💡 Start Ollama: ollama serve")
            sys.exit(1)
    
    elif args.nim or "nim" in config_file.lower():
        print("🔍 Checking NVIDIA NIM configuration...")
        if check_nvidia_api_key():
            # Map NVIDIA_API_KEY to OPENAI_API_KEY for OpenAI-compatible client
            if 'OPENAI_API_KEY' not in os.environ and 'NVIDIA_API_KEY' in os.environ:
                os.environ['OPENAI_API_KEY'] = os.environ['NVIDIA_API_KEY']
            # Ensure base URL is set for OpenAI-compatible client
            if 'OPENAI_BASE_URL' not in os.environ:
                os.environ['OPENAI_BASE_URL'] = 'https://integrate.api.nvidia.com/v1'
            print("   ✅ NVIDIA API key configured")
        else:
            print("   ❌ NVIDIA API key not found")
            print("   💡 Set environment variable: export NVIDIA_API_KEY=your_key")
            sys.exit(1)
    
    print("✅ All systems ready!")
    print()
    
    # Run the web server
    try:
        asyncio.run(run_web_server(
            config_file=config_file,
            host=args.host,
            port=args.port
        ))
    except KeyboardInterrupt:
        print("\n👋 Web demo stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
