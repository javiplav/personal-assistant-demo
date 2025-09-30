#!/usr/bin/env python3
"""
Start Personal Assistant Web Interface
======================================

This script starts the Personal Assistant web interface using the
proper WebUI adapter with API endpoints for testing and interaction.
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent / "personal_assistant_demo" / "src"))

from personal_assistant.adapters.webui import create_web_app

def main():
    """Start the web application."""
    
    # Configuration file path
    config_path = str(Path(__file__).parent.parent / "personal_assistant_demo" / "configs" / "config-planner-executor.yml")
    
    # Template directory
    template_dir = str(Path(__file__).parent.parent / "personal_assistant_demo" / "demos" / "web" / "templates")
    
    print("🌐 Starting Personal Assistant Web Interface...")
    print(f"⚙️  Config: {config_path}")
    print(f"📁 Templates: {template_dir}")
    print("🚀 Server starting at: http://localhost:8000")
    print("")
    print("API Endpoints available:")
    print("  • GET  /api/status     - Agent status")
    print("  • POST /api/chat       - Chat with agent")  
    print("  • POST /api/reset      - Reset agent state")
    print("")
    print("Press Ctrl+C to stop the server")
    print("")
    
    try:
        # Create and run web app with proper API endpoints
        web_app = create_web_app(config_path, template_dir)
        web_app.run(host="localhost", port=8000, debug=True)
        
    except KeyboardInterrupt:
        print("\n👋 Web server stopped")
    except Exception as e:
        print(f"❌ Error starting web server: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
