"""
Web UI Adapter for Personal Assistant Agent

Provides a thin web server adapter that calls core agent functionality.
Keeps web-specific concerns separate from core business logic.
"""

import json
import logging
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, render_template
from pathlib import Path

from ..core.agent import PersonalAssistantAgent

logger = logging.getLogger(__name__)


class WebUIAdapter:
    """
    Web adapter for personal assistant agent.
    
    Provides HTTP endpoints while delegating all logic to core agent.
    """
    
    def __init__(self, config_path: str, template_dir: Optional[str] = None):
        """
        Initialize web UI adapter.
        
        Args:
            config_path: Path to agent configuration
            template_dir: Optional path to templates directory
        """
        self.agent = PersonalAssistantAgent(config_path)
        
        # Set up Flask app
        self.app = Flask(__name__)
        if template_dir:
            self.app.template_folder = template_dir
        
        # Register routes
        self._register_routes()
        
        logger.info("🌐 Web UI adapter initialized")
    
    def _register_routes(self):
        """Register web routes."""
        
        @self.app.route('/')
        def index():
            """Serve the main web interface."""
            # Provide basic stats for the dashboard
            stats = {
                'clients': 12,
                'meetings': 8,
                'tasks': 25,
                'completed_tasks': 15
            }
            return render_template('beautiful.html', stats=stats)
        
        @self.app.route('/api/chat', methods=['POST'])
        async def chat():
            """Handle chat requests."""
            try:
                data = request.get_json()
                user_message = data.get('message', '')
                
                if not user_message:
                    return jsonify({
                        "success": False,
                        "error": "No message provided"
                    }), 400
                
                # Process through agent
                response = await self.agent.run(user_message)
                
                # Parse response to extract data for web UI
                try:
                    response_data = json.loads(response)
                    return jsonify(response_data)
                except json.JSONDecodeError:
                    # Fallback for non-JSON responses
                    return jsonify({
                        "success": True,
                        "message": response
                    })
                
            except Exception as e:
                logger.error(f"Chat endpoint error: {e}")
                return jsonify({
                    "success": False,
                    "error": "Internal server error"
                }), 500
        
        @self.app.route('/api/status')
        def status():
            """Get agent status."""
            try:
                status = self.agent.get_status()
                return jsonify(status)
            except Exception as e:
                logger.error(f"Status endpoint error: {e}")
                return jsonify({
                    "status": "error",
                    "error": str(e)
                }), 500
        
        @self.app.route('/api/reset', methods=['POST'])
        def reset():
            """Reset agent state."""
            try:
                self.agent.reset_state()
                return jsonify({
                    "success": True,
                    "message": "Agent state reset"
                })
            except Exception as e:
                logger.error(f"Reset endpoint error: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
    
    def run(self, host: str = "localhost", port: int = 8000, debug: bool = False):
        """
        Run the web server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            debug: Enable debug mode
        """
        logger.info(f"🚀 Starting web server at http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def create_web_app(config_path: str, template_dir: Optional[str] = None) -> WebUIAdapter:
    """
    Factory function to create web app.
    
    Args:
        config_path: Path to agent configuration
        template_dir: Optional templates directory
        
    Returns:
        Web UI adapter instance
    """
    return WebUIAdapter(config_path, template_dir)
