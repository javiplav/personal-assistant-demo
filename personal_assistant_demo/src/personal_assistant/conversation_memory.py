"""
Conversation Memory Management for Enhanced ReAct Agent

This module provides conversation state management to help ReAct agents
handle conversational follow-ups like "Who are those?" or "What about them?"
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manages conversation context for ReAct agents."""
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.conversation_history: List[Dict[str, Any]] = []
        self.last_action_context: Optional[Dict[str, Any]] = None
        self.last_results: Optional[Dict[str, Any]] = None
        
    def add_user_message(self, message: str) -> None:
        """Add user message to conversation history."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "user_message",
            "content": message,
            "message_lower": message.lower()
        }
        self.conversation_history.append(entry)
        logger.debug(f"Added user message: {message}")
    
    def add_agent_action(self, action: str, action_input: str, result: str) -> None:
        """Add agent action and result to conversation history."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "agent_action", 
            "action": action,
            "action_input": action_input,
            "result": result
        }
        self.conversation_history.append(entry)
        self.last_action_context = entry
        
        # Parse and store structured results for context
        if action == "list_clients":
            self._extract_client_context(result, action_input)
        elif action == "list_tasks":
            self._extract_task_context(result, action_input)
        elif action == "list_meetings":
            self._extract_meeting_context(result, action_input)
            
        logger.debug(f"Added agent action: {action} -> {result[:100]}...")
    
    def add_final_answer(self, answer: str) -> None:
        """Add final answer to conversation history."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "final_answer",
            "content": answer
        }
        self.conversation_history.append(entry)
        logger.debug(f"Added final answer: {answer[:100]}...")
    
    def get_context_for_followup(self, user_message: str) -> Optional[Dict[str, str]]:
        """
        Analyze user message and provide context for conversational follow-ups.
        
        Returns suggested action and input for messages like "Who are those?"
        """
        message_lower = user_message.lower()
        
        # Check for conversational reference words
        reference_words = [
            "who are those", "who are they", "which ones", "which clients",
            "what about them", "who are the", "list them", "show me those",
            "what about the", "who", "which", "those", "them", "these"
        ]
        
        if not any(ref in message_lower for ref in reference_words):
            return None
            
        # No previous context available
        if not self.last_action_context:
            return None
            
        last_action = self.last_action_context["action"]
        last_input = self.last_action_context["action_input"]
        
        logger.info(f"Detected follow-up question: '{user_message}'")
        logger.info(f"Last action context: {last_action} with input: {last_input}")
        
        # Map follow-up questions to appropriate actions
        if "medium" in message_lower and "priority" in message_lower:
            return {"action": "list_clients", "action_input": '{"filters": "medium"}'}
            
        elif "high" in message_lower and "priority" in message_lower:
            return {"action": "list_clients", "action_input": '{"filters": "high"}'}
            
        elif "low" in message_lower and "priority" in message_lower:
            return {"action": "list_clients", "action_input": '{"filters": "low"}'}
            
        elif any(word in message_lower for word in ["client", "who are those", "who are they", "who"]):
            # If last action was about clients, repeat with same filters
            if last_action == "list_clients":
                return {"action": "list_clients", "action_input": last_input}
            else:
                # Default to all clients
                return {"action": "list_clients", "action_input": '{"filters": ""}'}
                
        elif any(word in message_lower for word in ["task", "what about them"]):
            if last_action == "list_tasks":
                return {"action": "list_tasks", "action_input": last_input}
            else:
                return {"action": "list_tasks", "action_input": '{"filters": ""}'}
                
        elif any(word in message_lower for word in ["meeting", "schedule"]):
            if last_action == "list_meetings":
                return {"action": "list_meetings", "action_input": last_input}
            else:
                return {"action": "list_meetings", "action_input": '{}'}
        
        # Default: repeat the last action with same input
        return {"action": last_action, "action_input": last_input}
    
    def _extract_client_context(self, result: str, action_input: str) -> None:
        """Extract client information from list_clients result."""
        try:
            # Store context about what clients were just listed
            if "medium priority" in result.lower():
                self.last_results = {"type": "clients", "filter": "medium", "content": result}
            elif "high priority" in result.lower() or "high-priority" in result.lower():
                self.last_results = {"type": "clients", "filter": "high", "content": result}
            elif "low priority" in result.lower():
                self.last_results = {"type": "clients", "filter": "low", "content": result}
            else:
                self.last_results = {"type": "clients", "filter": "all", "content": result}
        except Exception as e:
            logger.warning(f"Failed to extract client context: {e}")
    
    def _extract_task_context(self, result: str, action_input: str) -> None:
        """Extract task information from list_tasks result."""
        try:
            self.last_results = {"type": "tasks", "content": result}
        except Exception as e:
            logger.warning(f"Failed to extract task context: {e}")
    
    def _extract_meeting_context(self, result: str, action_input: str) -> None:
        """Extract meeting information from list_meetings result."""
        try:
            self.last_results = {"type": "meetings", "content": result}
        except Exception as e:
            logger.warning(f"Failed to extract meeting context: {e}")
    
    def get_conversation_summary(self) -> str:
        """Get a summary of recent conversation for context."""
        if len(self.conversation_history) < 2:
            return ""
        
        # Get last few exchanges
        recent = self.conversation_history[-4:]  # Last 4 entries
        
        summary_parts = []
        for entry in recent:
            if entry["type"] == "user_message":
                summary_parts.append(f"User asked: {entry['content']}")
            elif entry["type"] == "final_answer":
                summary_parts.append(f"You answered: {entry['content']}")
            elif entry["type"] == "agent_action":
                summary_parts.append(f"You used {entry['action']} and got: {entry['result'][:100]}...")
        
        return " | ".join(summary_parts)
    
    def clear_session(self) -> None:
        """Clear conversation history for new session."""
        self.conversation_history.clear()
        self.last_action_context = None
        self.last_results = None
        logger.info(f"Cleared conversation history for session {self.session_id}")


# Global conversation memory instance
_conversation_memory = ConversationMemory()


def get_conversation_memory(session_id: str = "default") -> ConversationMemory:
    """Get conversation memory instance for session."""
    # For now, use single global instance
    # In production, you'd want per-session instances
    return _conversation_memory


def enhance_react_prompt_with_context(original_prompt: str, user_message: str) -> str:
    """
    Enhance ReAct prompt with conversation context to handle follow-ups better.
    """
    memory = get_conversation_memory()
    
    # Check if this is a follow-up question
    context_suggestion = memory.get_context_for_followup(user_message)
    
    if context_suggestion:
        # Add context to help the ReAct agent
        context_addition = f"""

CONVERSATION CONTEXT DETECTED:
Previous conversation indicates this is a follow-up question referring to recent results.
SUGGESTED ACTION for this follow-up: {context_suggestion['action']} 
SUGGESTED INPUT: {context_suggestion['action_input']}

Recent conversation summary: {memory.get_conversation_summary()}

When user asks "{user_message}", they likely want you to use the suggested action above.
"""
        return original_prompt + context_addition
    
    return original_prompt
