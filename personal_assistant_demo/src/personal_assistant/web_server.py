# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Enhanced Web Server for Personal Assistant Demo

This module provides a modern web interface for the NeMo Agent Toolkit demo,
showcasing real-time agent interactions and tool usage visualization.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from nat.builder.workflow_builder import WorkflowBuilder
from nat.data_models.config import Config
from nat.cli.cli_utils.config_override import load_and_override_config
from nat.utils.data_models.schema_validator import validate_schema
from nat.runtime.loader import discover_and_register_plugins, PluginTypes
from .enhanced_react_handler import EnhancedReActHandler, ToolCallingHandler
from .tools._paths import DATA_DIR, data_path

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    message: str
    verbose: bool = True
    mode: str = "react"  # "react" | "tool-calling"
    model: str = "ollama"  # "ollama" | "nim"
    reset_memory: bool = False


class ChatResponse(BaseModel):
    response: str
    steps: Optional[List[Dict[str, Any]]] = None
    profiling: Optional[Dict[str, Any]] = None


class WebServer:
    """Enhanced web server for the Personal Assistant demo."""
    
    def __init__(self, config_file: str = "configs/config-ollama-react-enhanced.yml"):
        self.app = FastAPI(
            title="NVIDIA NeMo Agent Toolkit - Enterprise Assistant Demo",
            description="Real-time AI agent demonstration",
            version="1.0.0"
        )
        # Enable debug logging for troubleshooting
        self._enable_debug_logging()
        self.handler = None  # Conversation-aware handler (ReAct or ToolCalling)
        self.config_file = config_file
        self.workflow = None
        self.builder = None
        self._builder_context = None  # Deprecated: keep for backward compat
        self._builder_manager = None  # Keep async context manager alive
        self.current_mode: str = "react"
        self.current_model: str = "ollama"
        self.setup_routes()
        self.setup_static_files()
        
        # Add shutdown handler to clean up resources
        @self.app.on_event("shutdown")
        async def shutdown_handler():
            await self.cleanup()

    def _enable_debug_logging(self) -> None:
        """Enable DEBUG logging across relevant modules for troubleshooting."""
        try:
            # Ensure a console handler exists
            root_logger = logging.getLogger()
            if not root_logger.handlers:
                console = logging.StreamHandler()
                console.setLevel(logging.DEBUG)
                console.setFormatter(logging.Formatter(
                    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    datefmt="%H:%M:%S"
                ))
                root_logger.addHandler(console)
            # Root logger level
            root_logger.setLevel(logging.DEBUG)
            # Our modules and NAT
            for name in [
                __name__,
                "personal_assistant",
                "personal_assistant.tools",
                "nat",
                "nat.agent",
                "nat.builder",
                "nat.runtime",
                "nat.components",
                "nat.utils",
                "uvicorn",
                "uvicorn.error",
                "uvicorn.access",
            ]:
                lg = logging.getLogger(name)
                lg.setLevel(logging.DEBUG)
                lg.propagate = True
            logger.info("Debug logging enabled for personal_assistant, NAT, and uvicorn modules")
        except Exception as e:
            logger.warning(f"Failed to enable debug logging: {e}")
    
    def setup_static_files(self):
        """Setup static file serving for the web interface."""
        web_dir = Path(__file__).parent / "web"
        web_dir.mkdir(exist_ok=True)
        
        # Mount static files
        if web_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")
    
    def setup_routes(self):
        """Setup all the API routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def serve_index():
            """Serve the web interface."""
            template_path = Path(__file__).parent / "web" / "templates" / "index.html"
            
            if not template_path.exists():
                # Fallback to a simple response if template is missing
                return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head><title>NeMo Agent Demo</title></head>
                <body>
                    <h1>NeMo Agent Toolkit Demo</h1>
                    <p>Web interface is loading... Please ensure all files are in place.</p>
                </body>
                </html>
                """)
            
            with open(template_path, 'r', encoding='utf-8') as f:
                return HTMLResponse(f.read())
        
        @self.app.post("/api/chat", response_model=ChatResponse)
        async def chat_endpoint(chat_message: ChatMessage):
            """Handle chat messages and return agent responses."""
            start_time = time.time()
            initialization_time = None
            processing_time = None
            
            try:
                # Re-initialize if mode/model changed or workflow not initialized
                init_start = time.time()
                
                # Mode resolution logic - only apply heuristics for "auto" mode
                requested_mode = chat_message.mode
                resolved_mode = chat_message.mode
                reason = "explicit user choice"
                
                # Only use heuristics when mode is "auto"
                if chat_message.mode == "auto":
                    # Analyze message to determine best handler
                    message_lower = chat_message.message.lower()
                    # Queries that are clearly data-retrieval lists
                    list_markers = [
                        "list all", "show all", "get all", "find all",
                        "high-priority", "high priority", "medium priority", "low priority"
                    ]
                    # Action verbs implying structured tool operations
                    action_markers = [
                        "add ", "update", "edit", "schedule", "cancel", "complete", "delete", "create", "set "
                    ]
                    # Domain hints for structured updates
                    domain_markers = ["client", "meeting", "task", "email"]

                    use_tool_calling = (
                        any(marker in message_lower for marker in list_markers)
                        or any(marker in message_lower for marker in action_markers) and any(d in message_lower for d in domain_markers)
                    )
                    
                    if use_tool_calling:
                        resolved_mode = "tool-calling"
                        reason = "heuristic: structured query detected"
                    else:
                        resolved_mode = "react"
                        reason = "heuristic: conversational query detected"
                    
                    # Only update chat_message.mode if we're in auto mode
                    chat_message.mode = resolved_mode
                
                # Log mode resolution for debugging
                logger.info("Mode resolution: %s -> %s (reason: %s)", requested_mode, resolved_mode, reason)
                
                # Always resolve config path for profiling info
                resolved_config = self._resolve_config_path(
                    chat_message.model or self.current_model, 
                    chat_message.mode or self.current_mode
                )
                logger.info("Config selected -> model=%s mode=%s file=%s",
                            chat_message.model, chat_message.mode, resolved_config)
                
                if (
                    (self.workflow is None)
                    or (chat_message.mode and chat_message.mode != self.current_mode)
                    or (chat_message.model and chat_message.model != self.current_model)
                ):
                    # Update mode/model and initialize workflow
                    self.current_mode = chat_message.mode or self.current_mode
                    self.current_model = chat_message.model or self.current_model
                    await self.initialize_workflow(resolved_config, self.current_mode)
                
                # Log the final mode selection for this request
                logger.info("Final mode selected for request: %s", self.current_mode)
                
                initialization_time = time.time() - init_start
                
                processing_start = time.time()
                
                # Reset memory if requested
                if chat_message.reset_memory and self.handler and hasattr(self.handler, "memory"):
                    self.handler.memory.clear_session()

                # Use appropriate handler with conversation memory if available
                if self.handler:
                    # Use the appropriate handler based on resolved mode (no more heuristic overrides)
                    if self.current_mode == "tool-calling" and hasattr(self, 'tool_handler'):
                        self.handler = self.tool_handler
                    elif hasattr(self, 'react_handler'):
                        self.handler = self.react_handler
                    
                    logger.info(f"Processing message with NAT Handler [{self.handler.__class__.__name__}]: {chat_message.message}")
                    
                    # Use selected handler with conversation memory
                    logger.debug(
                        "WebServer: starting handler.handle_message with mode=%s model=%s",
                        self.current_mode,
                        self.current_model
                    )
                    result = await self.handler.handle_message(chat_message.message)
                    processing_time = time.time() - processing_start
                    logger.debug(
                        "WebServer: handler completed in %.2fs (keys=%s)",
                        processing_time,
                        list(result.keys()) if isinstance(result, dict) else type(result).__name__
                    )
                    
                    # Create profiling information
                    model_info = "NIM" if self.current_model == "nim" else "Ollama"
                    if self.current_model == "nim":
                        config = load_and_override_config(Path(resolved_config), ())
                        if "llms" in config and "nvidia_llm" in config["llms"]:
                            model_info += f" - {config['llms']['nvidia_llm'].get('model', 'unknown')}"
                    else:  # Ollama
                        config = load_and_override_config(Path(resolved_config), ())
                        if "llms" in config and "ollama_llm" in config["llms"]:
                            model_info += f" - {config['llms']['ollama_llm'].get('model_name', 'unknown')}"

                    profiling = {
                        "total_time_seconds": time.time() - start_time,
                        "processing_time_seconds": processing_time,
                        "initialization_time_seconds": initialization_time,
                        "handler_type": "ReAct" if self.current_mode == "react" else "ToolCalling",
                        "model_info": model_info,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    return ChatResponse(
                        response=result.get("response", "I couldn't process your request."),
                        steps=result.get("steps") if chat_message.verbose else None,
                        profiling=profiling
                    )
                else:
                    # Fallback to direct workflow execution
                    logger.info(f"Processing message with direct workflow: {chat_message.message}")
                    
                    # Track execution steps for verbose mode
                    steps = []
                    
                    if chat_message.verbose:
                        steps = [
                            {
                                "tool": "Understanding Query",
                                "action": "Parsing user intent and required actions",
                                "result": "Identified: " + chat_message.message[:50] + "..."
                            }
                        ]
                    
                    # Execute the workflow directly
                    result = await self.workflow.ainvoke(chat_message.message)
                    processing_time = time.time() - processing_start
                    
                    # Extract the actual response
                    if isinstance(result, list) and len(result) > 0:
                        response = str(result[0])
                    elif isinstance(result, str):
                        response = result
                    else:
                        response = str(result)
                    
                    # Add completion step for verbose mode
                    if chat_message.verbose:
                        steps.append({
                            "tool": "Response Generation",
                            "action": "Generating final response",
                            "result": "Task completed successfully"
                        })
                    
                    # Create profiling information
                    profiling = {
                        "total_time_seconds": time.time() - start_time,
                        "processing_time_seconds": processing_time,
                        "initialization_time_seconds": initialization_time,
                        "handler_type": "DirectWorkflow",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    return ChatResponse(
                        response=response,
                        steps=steps if chat_message.verbose else None,
                        profiling=profiling
                    )
                
            except Exception as e:
                logger.error(f"Chat endpoint error: {e}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Failed to process message: {str(e)}"
                )
        
        @self.app.get("/api/stats")
        async def get_stats():
            """Get dashboard statistics."""
            try:
                stats = await self.load_stats()
                return JSONResponse(stats)
            except Exception as e:
                logger.error(f"Stats endpoint error: {e}")
                return JSONResponse({
                    "clients": 0,
                    "meetings": 0,
                    "tasks": 0,
                    "completed_tasks": 0
                })
        
        @self.app.get("/api/activity")
        async def get_recent_activity():
            """Get recent activity for the dashboard."""
            try:
                activity = await self.load_recent_activity()
                return JSONResponse(activity)
            except Exception as e:
                logger.error(f"Activity endpoint error: {e}")
                return JSONResponse([])
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    async def initialize_workflow(self, config_path: Optional[str] = None, mode: str = "react"):
        """Initialize the NeMo Agent Toolkit workflow with selected config and mode."""
        try:
            # Clean up any existing builder first
            # Close any existing async context manager first
            if getattr(self, '_builder_manager', None):
                try:
                    await self._builder_manager.__aexit__(None, None, None)
                except Exception as cleanup_error:
                    logger.warning(f"Error during builder cleanup: {cleanup_error}")
                finally:
                    self._builder_manager = None
                    self._builder_context = None
            
            # Discover and register plugins first
            discover_and_register_plugins(PluginTypes.ALL)
            
            # Load configuration
            effective_config = Path(config_path or self.config_file)
            config_dict = load_and_override_config(effective_config, ())
            config = validate_schema(config_dict, Config)
            
            logger.info(f"Initializing workflow with config: {effective_config}")
            
            # Build the actual workflow using WorkflowBuilder with more robust error handling
            self._builder_manager = WorkflowBuilder.from_config(config)
            self._builder_context = await self._builder_manager.__aenter__()
            self.builder = self._builder_context
            
            # Get workflow with error handling
            try:
                self.workflow = self.builder.get_workflow()
            except Exception as workflow_error:
                logger.error(f"Failed to get workflow from builder: {workflow_error}")
                # Clean up the builder context if workflow creation fails
                if self._builder_manager:
                    await self._builder_manager.__aexit__(None, None, None)
                self._builder_manager = None
                self._builder_context = None
                raise workflow_error
            
            # Initialize both handlers for flexibility
            self.react_handler = EnhancedReActHandler(self.workflow, session_id="web_session")
            self.tool_handler = ToolCallingHandler(self.workflow, session_id="web_session")
            
            # Set the default handler based on mode
            self.handler = self.tool_handler if mode == "tool-calling" else self.react_handler
            logger.info("✅ NeMo Agent Toolkit workflow and handlers initialized successfully!")
            
        except Exception as e:
            logger.error(f"Failed to initialize workflow: {e}", exc_info=True)
            
            # Fallback to mock workflow for demo purposes
            logger.warning("Falling back to demo mode with simulated responses")
            
            class MockWorkflow:
                async def ainvoke(self, payload) -> list[str]:
                    """Mock workflow for demo purposes when real workflow fails."""
                    # Extract message from payload - handle both string and dict formats
                    if isinstance(payload, dict) and "input_message" in payload:
                        message = payload["input_message"]
                    elif isinstance(payload, str):
                        message = payload
                    else:
                        message = str(payload)
                    
                    if "client" in message.lower():
                        return ["✅ [DEMO MODE] Client management functionality - real implementation would execute your registered client tools"]
                    elif "task" in message.lower():
                        return ["✅ [DEMO MODE] Task management - real implementation would use your task management tools"]
                    elif "calculate" in message.lower() or "%" in message:
                        return ["🔢 [DEMO MODE] Business calculations - real implementation would execute your calculator tools"]
                    else:
                        return [f"🤖 [DEMO MODE] Would process: '{message}' with full NeMo Agent Toolkit functionality"]
            
            self.workflow = MockWorkflow()
            self.builder = None
            # Fallback handler defaults to tool-calling style
            self.handler = ToolCallingHandler(self.workflow, session_id="web_session")

    def _resolve_config_path(self, model: str, mode: str) -> str:
        """Map model/mode selections to config file paths."""
        base_dir = Path("configs")
        model = (model or "ollama").lower()
        mode = (mode or "react").lower()

        if model == "nim":
            return (
                base_dir / "config-nim-tool-calling-conversation.yml"
                if mode == "tool-calling"
                else base_dir / "config-nim-react-fixed.yml"
            )
        # ollama
        return (
            base_dir / "config-ollama-tool-calling.yml"
            if mode == "tool-calling"
            else base_dir / "config-ollama-react-enhanced.yml"
        )
        
    async def load_stats(self) -> Dict[str, int]:
        """Load dashboard statistics from data files."""
        try:
            stats = {
                "clients": 0,
                "meetings": 0,
                "tasks": 0,
                "completed_tasks": 0
            }
            
            # Load clients
            if data_path("clients.json").exists():
                clients = json.loads(data_path("clients.json").read_text(encoding="utf-8"))
                stats["clients"] = len(clients)
            
            # Load meetings
            if data_path("meetings.json").exists():
                meetings = json.loads(data_path("meetings.json").read_text(encoding="utf-8"))
                stats["meetings"] = len([m for m in meetings if m.get("status") == "scheduled"])
            
            # Load tasks
            if data_path("tasks.json").exists():
                tasks = json.loads(data_path("tasks.json").read_text(encoding="utf-8"))
                stats["tasks"] = len([t for t in tasks if not t.get("completed", False)])
                stats["completed_tasks"] = len([t for t in tasks if t.get("completed", False)])
            
            return stats
            
        except Exception as e:
            logger.error(f"Error loading stats: {e}")
            return {"clients": 0, "meetings": 0, "tasks": 0, "completed_tasks": 0}
    
    async def load_recent_activity(self) -> List[Dict[str, Any]]:
        """Load recent activity for the dashboard."""
        try:
            activity = []
            
            # Load recent clients
            if data_path("clients.json").exists():
                clients = json.loads(data_path("clients.json").read_text(encoding="utf-8"))
                for client in sorted(clients, key=lambda x: x.get("created_at", ""), reverse=True)[:3]:
                    created_str = client.get("created_at", "")
                    try:
                        created_dt = datetime.fromisoformat(created_str)
                        created_ts = created_dt.timestamp()
                    except Exception:
                        created_ts = 0
                    activity.append({
                        "id": f"client_{client['id']}",
                        "type": "Client Added",
                        "description": f"{client['name']} from {client['company']}",
                        "time": self.format_time(created_str),
                        "timestamp": created_str,
                        "ts": created_ts,
                        "icon": "fas fa-user-plus"
                    })
            
            # Load recent meetings
            if data_path("meetings.json").exists():
                meetings = json.loads(data_path("meetings.json").read_text(encoding="utf-8"))
                for meeting in sorted(meetings, key=lambda x: x.get("created_at", ""), reverse=True)[:3]:
                    created_str = meeting.get("created_at", "")
                    try:
                        created_dt = datetime.fromisoformat(created_str)
                        created_ts = created_dt.timestamp()
                    except Exception:
                        created_ts = 0
                    activity.append({
                        "id": f"meeting_{meeting['id']}",
                        "type": "Meeting Scheduled",
                        "description": meeting['title'],
                        "time": self.format_time(created_str),
                        "timestamp": created_str,
                        "ts": created_ts,
                        "icon": "fas fa-handshake"
                    })
            
            # Load recent tasks
            if data_path("tasks.json").exists():
                tasks = json.loads(data_path("tasks.json").read_text(encoding="utf-8"))
                for task in sorted(tasks, key=lambda x: x.get("created_at", ""), reverse=True)[:3]:
                    created_str = task.get("created_at", "")
                    try:
                        created_dt = datetime.fromisoformat(created_str)
                        created_ts = created_dt.timestamp()
                    except Exception:
                        created_ts = 0
                    activity.append({
                        "id": f"task_{task['id']}",
                        "type": "Task Created",
                        "description": task['description'][:50] + "..." if len(task['description']) > 50 else task['description'],
                        "time": self.format_time(created_str),
                        "timestamp": created_str,
                        "ts": created_ts,
                        "icon": "fas fa-tasks"
                    })
            
            # Sort by actual timestamp and limit
            activity.sort(key=lambda x: x.get('ts', 0), reverse=True)
            return activity[:10]
            
        except Exception as e:
            logger.error(f"Error loading activity: {e}")
            return []
    
    def format_time(self, timestamp_str: str) -> str:
        """Format timestamp for display."""
        try:
            if not timestamp_str:
                return "Unknown"
            
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            now = datetime.now()
            diff = now - dt
            
            if diff.days > 0:
                return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                return "Just now"
                
        except Exception:
            return "Unknown"
    
    async def cleanup(self):
        """Clean up resources when server shuts down."""
        try:
            if getattr(self, '_builder_manager', None):
                await self._builder_manager.__aexit__(None, None, None)
                self._builder_manager = None
                self._builder_context = None
                logger.info("✅ Workflow builder context cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Factory function for creating the app
def create_app(config_file: str = "configs/config-ollama.yml") -> FastAPI:
    """Create and configure the FastAPI app."""
    server = WebServer(config_file)
    return server.app


# For development server
if __name__ == "__main__":
    import uvicorn
    
    app = create_app()
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )
