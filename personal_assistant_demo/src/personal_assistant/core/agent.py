"""
Personal Assistant Agent - Main entry point and facade

This is the primary interface for the personal assistant agent.
It orchestrates the planner-executor flow with production hardening.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

from .registry import ToolRegistry
from .circuit_breaker import ToolCircuitBreakerRegistry, BreakerConfig
from .sanitizer import sanitize_observation
from .controller import AgentController
from .errors import PersonalAssistantError, ErrorCodes, create_error_response

logger = logging.getLogger(__name__)


class PersonalAssistantAgent:
    """
    Production-grade personal assistant agent with enterprise hardening.
    
    Features:
    - Planner-Executor architecture (eliminates ReAct drift)
    - Circuit breaker protection
    - PII sanitization
    - Result caching and idempotency
    - Comprehensive validation
    - OpenTelemetry integration
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the personal assistant agent.
        
        Args:
            config_path: Path to agent configuration file
        """
        self.config_path = Path(config_path)
        
        # Initialize tool registry
        registry_path = Path(__file__).parent.parent / "data" / "tool_registry.json"
        self.tool_registry = ToolRegistry(str(registry_path))
        
        # Initialize circuit breakers
        breaker_config = BreakerConfig(
            window_seconds=300,  # 5 minutes
            buckets=10,         # 30s each
            min_requests=50,
            failure_threshold=0.7,  # 70%
            cooldown_seconds=60
        )
        self.circuit_breakers = ToolCircuitBreakerRegistry(breaker_config)
        
        # Initialize controller
        self.controller = AgentController(
            tool_registry=self.tool_registry,
            circuit_breakers=self.circuit_breakers,
            config_path=config_path
        )
        
        logger.info(f"🤖 Personal Assistant Agent initialized")
        logger.info(f"🔧 Tools: {len(self.tool_registry.available_tools)}")
        logger.info(f"🛡️ Circuit breakers: Active with 70% failure threshold")
    
    async def run(self, user_request: str, **kwargs) -> str:
        """
        Run the agent with a user request.
        
        Args:
            user_request: The user's natural language request
            **kwargs: Additional parameters (timeout, etc.)
            
        Returns:
            JSON response with results or error information
        """
        start_time = time.time()
        
        try:
            logger.info(f"🎯 Processing request: {user_request}")
            
            # Sanitize input
            sanitized_request = sanitize_observation(user_request)
            
            # Run through controller
            result = await self.controller.execute_request(sanitized_request, **kwargs)
            
            # Log performance metrics
            total_time = time.time() - start_time
            self._log_performance_metrics(result, total_time)
            
            return result
            
        except PersonalAssistantError as e:
            logger.error(f"❌ Agent error: {e.message}")
            return json.dumps(create_error_response(
                message=e.message,
                error_code=e.error_code,
                error_details=e.details
            ))
            
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return json.dumps(create_error_response(
                message=f"Internal agent error: {str(e)}",
                error_code=ErrorCodes.E_UNKNOWN
            ))
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status and metrics.
        
        Returns:
            Dictionary with agent status information
        """
        registry_stats = self.tool_registry.get_tool_stats()
        breaker_metrics = self.circuit_breakers.get_all_metrics()
        
        return {
            "status": "ready",
            "tools": {
                "total": len(self.tool_registry.available_tools),
                "cache_stats": {
                    "pure_cache_entries": registry_stats["pure_cache_entries"],
                    "read_cache_entries": registry_stats["read_cache_entries"]
                }
            },
            "circuit_breakers": {
                "total": len(breaker_metrics),
                "open": len([tool for tool, metrics in breaker_metrics.items() 
                           if metrics["state"] == "open"]),
                "metrics": breaker_metrics
            }
        }
    
    def reset_state(self) -> None:
        """Reset agent state (caches, circuit breakers, etc.)."""
        logger.info("🔄 Resetting agent state...")
        
        # Reset caches in tool registry
        self.tool_registry._pure_cache.clear()
        self.tool_registry._read_cache.clear()
        self.tool_registry._idempotency_keys.clear()
        
        # Reset circuit breakers
        self.circuit_breakers = ToolCircuitBreakerRegistry(BreakerConfig())
        
        logger.info("✅ Agent state reset complete")
    
    def _log_performance_metrics(self, result: str, total_time: float) -> None:
        """Log performance and operational metrics."""
        try:
            result_data = json.loads(result)
            success = result_data.get("success", True)
            
            logger.info(f"🎉 Request completed in {total_time:.2f}s - "
                       f"Status: {'SUCCESS' if success else 'FAILED'}")
            
            # Log tool registry stats
            stats = self.tool_registry.get_tool_stats()
            logger.info(f"📊 Cache stats: {stats['pure_cache_entries']} pure, "
                       f"{stats['read_cache_entries']} read_only cached")
            
            # Log circuit breaker stats
            breaker_metrics = self.circuit_breakers.get_all_metrics()
            open_breakers = [tool for tool, metrics in breaker_metrics.items() 
                           if metrics["state"] == "open"]
            
            if open_breakers:
                logger.warning(f"⚠️ Circuit breakers OPEN: {', '.join(open_breakers)}")
            else:
                logger.info("🛡️ All circuit breakers operational")
                
        except json.JSONDecodeError:
            logger.warning("Could not parse result for metrics logging")
        except Exception as e:
            logger.warning(f"Error logging metrics: {e}")
