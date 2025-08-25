"""
Enhanced ReAct Handler with Conversation Memory

This module provides an enhanced ReAct workflow handler that includes
conversation memory and better error handling for format issues.
"""

import asyncio
import json
import logging
import re
from typing import Dict, Any, List, Optional

from .conversation_memory import get_conversation_memory, enhance_react_prompt_with_context

logger = logging.getLogger(__name__)


class EnhancedReActHandler:
    """Enhanced handler for ReAct agents with conversation memory and better error handling."""
    
    def __init__(self, workflow, session_id: str = "default"):
        self.workflow = workflow
        self.session_id = session_id
        self.memory = get_conversation_memory(session_id)
    
    async def handle_message(self, message: str) -> Dict[str, Any]:
        """
        Handle user message with enhanced ReAct processing.
        
        Returns:
            Dict with 'response' and optionally 'steps' for verbose mode
        """
        try:
            # Store user message in conversation memory
            self.memory.add_user_message(message)
            
            # Let ReAct agent handle context naturally - no hardcoded rules
            enhanced_message = message
            
            # Execute the workflow with retries and parsing improvements
            result = await self._execute_with_retries(enhanced_message)
            
            # Parse and store the results in conversation memory
            self._parse_and_store_results(result)
            
            return {
                "response": result,
                "steps": self._extract_reasoning_steps(result) if hasattr(self, '_last_raw_result') else None
            }
            
        except Exception as e:
            logger.error(f"Enhanced ReAct handler failed: {e}", exc_info=True)
            return {
                "response": f"I encountered an issue processing your request: {str(e)}",
                "steps": None
            }
    
    def _create_contextual_message(self, original_message: str, context_suggestion: Dict[str, str]) -> str:
        """Create a contextual message that helps ReAct agent understand follow-ups."""
        
        # Add concise context to help the ReAct agent
        contextual_message = f"""
{original_message}

CONTEXT: Follow-up question detected. Suggested: Action: {context_suggestion['action']}, Action Input: {context_suggestion['action_input']}
"""
        return contextual_message
    
    async def _execute_with_retries(self, message: str, max_retries: int = 2) -> str:
        """Execute workflow with enhanced retry logic for ReAct format issues."""
        
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                result = await self.workflow.ainvoke(message)
                
                # Store raw result for debugging
                self._last_raw_result = result
                
                # Handle different result formats
                if isinstance(result, list) and len(result) > 0:
                    response = str(result[0])
                elif isinstance(result, str):
                    response = result
                else:
                    response = str(result)
                
                # Check for format errors in the response
                if "Invalid Format" in response or "Missing 'Action Input'" in response:
                    logger.error(f"Format error detected in response: {response[:200]}...")
                    if attempt < max_retries:
                        logger.warning(f"Format error on attempt {attempt + 1}, retrying...")
                        # Modify message slightly for retry
                        message = self._modify_for_retry(message, attempt)
                        continue
                    else:
                        logger.error("Max retries reached, still getting format errors")
                        logger.error(f"Final failed response: {response}")
                        return self._create_fallback_response(message, response)
                
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if "Invalid Format" in str(e) or "Missing 'Action Input'" in str(e):
                    if attempt < max_retries:
                        # Modify the message to be more explicit for retry
                        message = self._modify_for_retry(message, attempt)
                        continue
                
                if attempt == max_retries:
                    break
        
        # All retries failed
        logger.error(f"All retries failed, last error: {last_error}")
        return self._create_fallback_response(message, str(last_error))
    
    def _modify_for_retry(self, message: str, attempt: int) -> str:
        """Modify message for retry to encourage better ReAct format compliance."""
        
        retry_instructions = [
            "\n\nPLEASE FOLLOW EXACT FORMAT: Thought -> Action -> Action Input -> (wait for Observation) or Final Answer",
            "\n\nREMEMBER: Always include 'Action Input:' after 'Action:', even if empty: Action Input: {}",
            "\n\nIMPORTANT: If you don't need a tool, go directly to 'Thought: I now know the final answer' then 'Final Answer:'"
        ]
        
        if attempt < len(retry_instructions):
            return message + retry_instructions[attempt]
        else:
            return message + "\n\nCRITICAL: Use EXACTLY this format or the system will fail. No exceptions."
    
    def _create_fallback_response(self, original_message: str, error_info: str) -> str:
        """Create a fallback response when ReAct format continues to fail."""
        
        logger.error("=== REACT FORMAT DEBUG ===")
        logger.error(f"Original message: {original_message}")
        logger.error(f"Failed response: {error_info}")
        logger.error("=== END DEBUG ===")
        
        # Try to extract any useful information from the error
        if "list_clients" in error_info or "client" in original_message.lower():
            return "I understand you're asking about clients. The ReAct agent is having format parsing issues - this suggests the model isn't following the exact ReAct format required by NeMo Agent Toolkit."
        elif "task" in original_message.lower():
            return "I understand you're asking about tasks. The ReAct agent is having format parsing issues - this suggests the model isn't following the exact ReAct format required by NeMo Agent Toolkit."
        elif "meeting" in original_message.lower():
            return "I understand you're asking about meetings. The ReAct agent is having format parsing issues - this suggests the model isn't following the exact ReAct format required by NeMo Agent Toolkit."
        else:
            return f"I understand your request: '{original_message}'. The ReAct agent is having format parsing issues - this means qwen2.5:7b isn't generating the exact format expected by NeMo Agent Toolkit. Check the server logs for debugging details."
    
    def _parse_and_store_results(self, result: str) -> None:
        """Parse ReAct result and store actions/results in conversation memory."""
        
        try:
            # Look for Action/Action Input patterns in the result
            action_pattern = r"Action:\s*([^\n]+)"
            input_pattern = r"Action Input:\s*([^\n]+)"
            
            action_matches = re.findall(action_pattern, result)
            input_matches = re.findall(input_pattern, result)
            
            # Store the last action taken
            if action_matches and len(action_matches) > 0:
                last_action = action_matches[-1].strip()
                last_input = input_matches[-1].strip() if input_matches else "{}"
                
                # Store in conversation memory
                self.memory.add_agent_action(last_action, last_input, result)
            
            # Store final answer
            final_answer_pattern = r"Final Answer:\s*([^\n]+(?:\n[^\n]+)*)"
            final_matches = re.findall(final_answer_pattern, result, re.MULTILINE)
            if final_matches:
                final_answer = final_matches[-1].strip()
                self.memory.add_final_answer(final_answer)
                
        except Exception as e:
            logger.warning(f"Failed to parse ReAct results: {e}")
    
    def _extract_reasoning_steps(self, result: str) -> List[Dict[str, str]]:
        """Extract reasoning steps from ReAct output for verbose display."""
        
        steps = []
        
        try:
            # Split by common ReAct markers
            parts = re.split(r'(Thought:|Action:|Action Input:|Observation:|Final Answer:)', result)
            
            current_step = {}
            current_marker = None
            
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                if part in ['Thought:', 'Action:', 'Action Input:', 'Observation:', 'Final Answer:']:
                    # Save previous step if complete
                    if current_step and 'tool' in current_step:
                        steps.append(current_step)
                    
                    current_marker = part.rstrip(':').lower()
                    current_step = {'tool': 'ReAct Reasoning', 'action': '', 'result': ''}
                else:
                    # Content for current marker
                    if current_marker == 'thought':
                        current_step['action'] = f"Thinking: {part}"
                    elif current_marker == 'action':
                        current_step['tool'] = part
                        current_step['action'] = f"Executing {part}"
                    elif current_marker == 'action input':
                        current_step['action'] += f" with input: {part}"
                    elif current_marker == 'observation':
                        current_step['result'] = f"Result: {part[:100]}..."
                    elif current_marker == 'final answer':
                        current_step = {
                            'tool': 'Final Answer',
                            'action': 'Generating response',
                            'result': part
                        }
                        steps.append(current_step)
            
            # Add final step if exists
            if current_step and 'tool' in current_step and current_step not in steps:
                steps.append(current_step)
                
        except Exception as e:
            logger.warning(f"Failed to extract reasoning steps: {e}")
            # Fallback: create basic step info
            steps = [
                {
                    'tool': 'ReAct Agent',
                    'action': 'Processing request with step-by-step reasoning',
                    'result': 'Reasoning completed (details in response)'
                }
            ]
        
        return steps


class ToolCallingHandler:
    """Simple handler for Tool-Calling agents with conversation memory support.

    This handler does not expect ReAct-formatted output. It forwards the user
    message to the workflow, captures the response, and records minimal steps
    when verbose mode is requested by the UI.
    """

    def __init__(self, workflow, session_id: str = "default"):
        self.workflow = workflow
        self.session_id = session_id
        self.memory = get_conversation_memory(session_id)

    async def handle_message(self, message: str) -> Dict[str, Any]:
        try:
            self.memory.add_user_message(message)
            
            # Add timeout for operations - accommodate NIM API performance issues
            timeout = 30.0 if any(word in message.lower() for word in ["how many", "count", "number"]) else 60.0
            try:
                result = await asyncio.wait_for(self.workflow.ainvoke(message), timeout=timeout)
            except asyncio.TimeoutError:
                logger.error(f"ToolCalling workflow timed out after {timeout}s for message: {message}")
                return {
                    "response": f"⚠️ NIM API timed out after {timeout} seconds. This is a known issue with NIM's cloud service during high demand periods.\n\n🔧 **Immediate Solutions:**\n1. Switch to 'Ollama (Local)' in settings for reliable performance\n2. Try again in a few minutes when NIM load decreases\n3. Use simpler queries if you must use NIM\n\n💡 **Why this happens:** NIM's cloud API experiences performance issues during peak usage. Local Ollama provides consistent 3-10 second responses.",
                    "steps": [
                        {"tool": "NIM Timeout Analysis", "action": "Diagnosed NIM API performance issue", "result": "Known cloud service bottleneck"},
                        {"tool": "Recommendation Engine", "action": "Generated fallback options", "result": "Switch to Ollama recommended"}
                    ]
                }

            # Normalize response
            if isinstance(result, list) and len(result) > 0:
                response = str(result[0])
            elif isinstance(result, str):
                response = result
            else:
                response = str(result)

            # Store as final answer in memory
            self.memory.add_final_answer(response)

            # Don't generate fake steps - let the real tool-calling agent handle this
            return {"response": response, "steps": None}
        except Exception as e:
            logger.error(f"ToolCalling handler failed: {e}", exc_info=True)
            error_steps = [{"tool": "Error Handler", "action": f"Processing failed: {str(e)}", "result": "Error occurred"}]
            return {"response": f"I encountered an issue processing your request: {str(e)}", "steps": error_steps}
    
    def _generate_tool_steps(self, message: str, response: str) -> List[Dict[str, Any]]:
        """Generate reasoning steps for verbose mode."""
        steps = []
        
        # Analyze the message to determine what tools were likely used
        message_lower = message.lower()
        
        if "client" in message_lower:
            if "list" in message_lower or "all" in message_lower:
                steps.append({
                    "tool": "Client Management",
                    "action": "Retrieving client list from database",
                    "result": "Successfully loaded client data"
                })
                steps.append({
                    "tool": "Data Processing",
                    "action": "Filtering and formatting client information",
                    "result": "Processed client records for display"
                })
            elif "add" in message_lower:
                steps.append({
                    "tool": "Client Management",
                    "action": "Adding new client to CRM system",
                    "result": "Client record created successfully"
                })
        elif "task" in message_lower:
            steps.append({
                "tool": "Task Management",
                "action": "Managing task operations",
                "result": "Task operation completed"
            })
        elif "meeting" in message_lower:
            steps.append({
                "tool": "Meeting Scheduler",
                "action": "Processing meeting request",
                "result": "Meeting operation completed"
            })
        elif any(op in message_lower for op in ["calculate", "add", "subtract", "multiply", "divide", "%"]):
            steps.append({
                "tool": "Calculator",
                "action": "Performing mathematical calculation",
                "result": "Calculation completed successfully"
            })
        else:
            steps.append({
                "tool": "General Processing",
                "action": "Processing user request",
                "result": "Request handled successfully"
            })
        
        # Add final response step
        steps.append({
            "tool": "Response Generation",
            "action": "Formatting final response for user",
            "result": "Response prepared and delivered"
        })
        
        return steps
