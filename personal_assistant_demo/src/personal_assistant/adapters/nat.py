"""
NeMo Agent Toolkit (NAT) Adapter

Provides integration with the NAT framework while keeping core logic framework-agnostic.
This allows the personal assistant to work with NAT's infrastructure while maintaining
clean separation of concerns.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from ..core.agent import PersonalAssistantAgent

logger = logging.getLogger(__name__)


class NATPersonalAssistantAdapter:
    """
    Adapter that makes PersonalAssistantAgent compatible with NAT framework.
    
    This adapter handles:
    - NAT configuration integration
    - NAT logging integration  
    - NAT tool registration compatibility
    - Response format adaptation
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the NAT adapter.
        
        Args:
            config_path: Path to NAT configuration file
        """
        self.config_path = Path(config_path)
        self.agent = PersonalAssistantAgent(config_path)
        
        logger.info("🔌 NAT adapter initialized")
    
    async def process_request(self, request: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a request through the personal assistant agent.
        
        This method provides the interface that NAT expects.
        
        Args:
            request: User request string
            context: Optional context from NAT
            
        Returns:
            Agent response as JSON string
        """
        try:
            # Add any NAT-specific preprocessing here
            if context:
                logger.debug(f"NAT context: {context}")
            
            # Execute through our agent
            response = await self.agent.run(request)
            
            return response
            
        except Exception as e:
            logger.error(f"NAT adapter error: {e}")
            return '{"success": false, "error": "NAT adapter error", "message": "' + str(e) + '"}'
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status in NAT-compatible format."""
        status = self.agent.get_status()
        
        # Add NAT-specific status fields if needed
        status["adapter"] = "NAT"
        status["config_path"] = str(self.config_path)
        
        return status
    
    def reset_agent_state(self) -> None:
        """Reset agent state (for NAT lifecycle management)."""
        self.agent.reset_state()
        logger.info("🔄 NAT adapter state reset")


# Factory function for NAT integration
def create_nat_agent(config_path: str) -> NATPersonalAssistantAdapter:
    """
    Factory function to create NAT-compatible agent.
    
    Args:
        config_path: Path to NAT configuration
        
    Returns:
        NAT adapter instance
    """
    return NATPersonalAssistantAdapter(config_path)
