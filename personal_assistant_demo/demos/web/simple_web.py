#!/usr/bin/env python3
"""
Simple Web Server for Personal Assistant Demo

Uses the reorganized WebUI adapter to provide a clean web interface for testing.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from personal_assistant.adapters.webui import create_web_app

def main():
    """Run the web server using our WebUI adapter."""
    
    # Configuration file path
    config_path = str(Path(__file__).parent.parent.parent / "configs" / "config-planner-executor.yml")
    
    # Template directory
    template_dir = str(Path(__file__).parent / "templates")
    
    print("🌐 Starting Personal Assistant Web Interface...")
    print(f"📁 Templates: {template_dir}")
    print(f"⚙️  Config: {config_path}")
    print("🚀 Server will start at: http://localhost:8000")
    print("")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Create and run web app
        web_app = create_web_app(config_path, template_dir)
        web_app.run(host="localhost", port=8000, debug=True)
        
    except KeyboardInterrupt:
        print("\n👋 Web server stopped")
    except Exception as e:
        print(f"❌ Error starting web server: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
