"""
Agent Controller - Orchestrates planner-executor flow with production features

Handles:
- Plan creation and validation
- Step-by-step execution with retries
- Circuit breaker integration
- PII sanitization
- Performance monitoring
"""

import json
import logging
import asyncio
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

from .registry import ToolRegistry
from .circuit_breaker import ToolCircuitBreakerRegistry
from .sanitizer import sanitize_observation
from .validator import validate_plan, validate_executor_step
from .errors import PersonalAssistantError, ExecutionError, ErrorCodes, create_error_response

logger = logging.getLogger(__name__)


class AgentController:
    """
    Controller that orchestrates the planner-executor flow with production hardening.
    """
    
    def __init__(self, tool_registry: ToolRegistry, circuit_breakers: ToolCircuitBreakerRegistry, 
                 config_path: str):
        """
        Initialize the agent controller.
        
        Args:
            tool_registry: Production tool registry
            circuit_breakers: Circuit breaker registry
            config_path: Path to configuration file
        """
        self.tool_registry = tool_registry
        self.circuit_breakers = circuit_breakers
        self.config_path = Path(config_path)
        
        # Configuration defaults
        self.max_retries = 2
        self.per_step_timeout = 5.0
        self.overall_deadline = 20.0
        
        logger.info("🎛️ Agent controller initialized")
    
    async def execute_request(self, user_request: str, **kwargs) -> str:
        """
        Execute a user request through the planner-executor flow.
        
        Args:
            user_request: The user's request
            **kwargs: Additional parameters
            
        Returns:
            JSON response with results
        """
        start_time = time.time()
        
        try:
            # Step 1: Create and validate execution plan
            logger.info(f"📋 Planning request...")
            plan = await self._create_validated_plan(user_request)
            
            # Step 2: Execute plan step by step
            logger.info(f"⚡ Executing {len(plan['plan'])} steps...")
            results = []
            
            for i, step in enumerate(plan["plan"], 1):
                # Check deadline
                if time.time() - start_time > self.overall_deadline:
                    logger.warning(f"⏰ Deadline reached, providing partial results")
                    return self._create_partial_response(user_request, results, plan["plan"][i-1:])
                
                # Execute step
                result = await self._execute_step_with_retry(
                    user_request=user_request,
                    plan=plan,
                    step_number=i,
                    current_step=step,
                    previous_results=results[-1] if results else None
                )
                
                results.append(result)
                logger.info(f"✅ Step {i}/{len(plan['plan'])} completed")
            
            # Step 3: Generate final response
            final_answer = await self._generate_final_response(user_request, plan, results)
            
            return final_answer
            
        except Exception as e:
            logger.error(f"❌ Controller execution failed: {e}")
            return json.dumps(create_error_response(
                message=f"Execution failed: {str(e)}",
                error_code=ErrorCodes.E_UNKNOWN
            ))
    
    async def _create_validated_plan(self, user_request: str) -> Dict[str, Any]:
        """Create and validate execution plan."""
        # Simple demo planner - in production this would call LLM
        plan_steps = []
        step_num = 1
        
        request_lower = user_request.lower()
        
        # Parse for add task
        if "add" in request_lower and "task" in request_lower:
            task_desc = self._extract_task_description(user_request)
            plan_steps.append({
                "id": f"s{step_num}",
                "step": step_num,
                "tool": "add_task",
                "input": {"description": task_desc},
                "after": []
            })
            step_num += 1
        
        # Parse for list tasks with filtering support
        if "list" in request_lower and ("task" in request_lower or "all" in request_lower):
            import re
            
            # Build input parameters based on filtering requests
            list_input = {}
            
            # Status filtering
            if any(word in request_lower for word in ["pending", "incomplete", "active", "todo"]):
                list_input["status"] = "pending"
            elif any(word in request_lower for word in ["completed", "done", "finished"]):
                list_input["status"] = "completed"
            
            # Simplified Search/query filtering with direct patterns
            search_patterns = [
                # "tasks containing X", "tasks with X", "tasks about X"
                (r'tasks?\s+(?:containing|with|about)\s+([a-zA-Z][^,\n]*?)(?:\s*$|,)', "pattern1"),
                # "containing X tasks", "with X in them"
                (r'(?:containing|with)\s+([a-zA-Z][^,\n]*?)\s+tasks?', "pattern2"),
                # "search for X", "find X tasks" 
                (r'(?:search\s+for|find)\s+([a-zA-Z][^,\n]*?)\s*(?:tasks?|$)', "pattern3"),
                # "X tasks" - Direct word before tasks
                (r'\b([a-zA-Z]{4,})\s+tasks?\b', "pattern4"),
                # "tasks matching X"
                (r'tasks?\s+matching\s+([a-zA-Z][^,\n]*?)(?:\s*$|,)', "pattern5"),
                # "list X tasks" - capture X
                (r'list\s+([a-zA-Z]{3,})\s+tasks?\b', "pattern6")
            ]
            
            for i, (pattern, pattern_name) in enumerate(search_patterns):
                search_match = re.search(pattern, request_lower)
                if search_match:
                    search_term = search_match.group(1).strip()
                    # Clean up common words that get captured
                    search_term = re.sub(r'\b(my|the|all|some|any)\b', '', search_term).strip()
                    # Skip command words but allow descriptive terms
                    skip_words = ['list', 'show', 'get', 'find', 'task', 'tasks']
                    if len(search_term) > 2 and search_term.lower() not in skip_words:
                        list_input["query"] = search_term
                        break
            
            # Enhanced Client filtering
            client_patterns = [
                # "for client X", "for X client"
                r'for\s+(?:client\s+)?([A-Za-z][^,\n]*?)(?:\s*(?:,|and|then|client|$))',
                # "client X tasks", "X client tasks" 
                r'(?:client\s+)?([A-Za-z][^,\n]*?)\s+client\s+tasks?',
                # "tasks for X", "X tasks"
                r'tasks?\s+for\s+([A-Za-z][^,\n]*?)(?:\s*(?:,|and|then|$))',
                # "X's tasks"
                r"([A-Za-z][^,\n]*?)'s?\s+tasks?",
                # Direct client name matching when context suggests it
                r'(?:from|by)\s+([A-Za-z][^,\n]*?)(?:\s*(?:,|and|then|$))'
            ]
            
            for pattern in client_patterns:
                client_match = re.search(pattern, request_lower)
                if client_match:
                    client_name = client_match.group(1).strip()
                    # Clean up common words
                    client_name = re.sub(r'\b(the|my|our|this|that)\b', '', client_name).strip()
                    # Ensure it's a reasonable client name (not a command word)
                    if (len(client_name) > 2 and 
                        not any(cmd in client_name.lower() for cmd in ['list', 'show', 'get', 'find', 'task', 'all', 'my']) and
                        not client_name.lower() in ['pending', 'completed', 'done', 'finished']):
                        list_input["client_name"] = client_name.title()  # Proper case
                        break
            
            after_deps = ["s1"] if len(plan_steps) > 0 else []
            plan_steps.append({
                "id": f"s{step_num}",
                "step": step_num,
                "tool": "list_tasks",
                "input": list_input,
                "after": after_deps
            })
            step_num += 1
        
        # Parse for calculate percentage
        if "calculate" in request_lower and ("%" in user_request or "percent" in request_lower):
            after_deps = ["s1"] if len(plan_steps) > 0 else []
            plan_steps.append({
                "id": f"s{step_num}",
                "step": step_num,
                "tool": "calculate_percentage",
                "input": {"text": user_request},
                "after": after_deps
            })
            step_num += 1
        
        # Parse for add client
        if "add" in request_lower and "client" in request_lower:
            # Extract client name from request
            import re
            client_match = re.search(r'client\s+named\s+([^,]+)', user_request, re.IGNORECASE)
            client_name = client_match.group(1).strip() if client_match else "Test Client"
            
            plan_steps.append({
                "id": f"s{step_num}",
                "step": step_num,
                "tool": "add_client",
                "input": {"name": client_name, "company": "Test Company", "email": f"{client_name.lower().replace(' ', '.')}@example.com"},
                "after": []
            })
            step_num += 1
        
        # Parse for current time
        if "time" in request_lower or "what time" in request_lower:
            plan_steps.append({
                "id": f"s{step_num}",
                "step": step_num,
                "tool": "get_current_time",
                "input": {},
                "after": []
            })
            step_num += 1
        
        if not plan_steps:
            # Default single step
            plan_steps.append({
                "id": "s1",
                "step": 1,
                "tool": "list_tasks",
                "input": {},
                "after": []
            })
        
        plan = {"plan": plan_steps}
        
        # Validate plan using the validator
        validation_result = validate_plan(plan, self.tool_registry.registry_data)
        if not validation_result.valid:
            raise PersonalAssistantError(
                f"Plan validation failed: {validation_result.errors}",
                ErrorCodes.E_SCHEMA,
                {"errors": validation_result.errors}
            )
        
        return validation_result.normalized_plan
    
    async def _execute_step_with_retry(
        self,
        user_request: str,
        plan: Dict[str, Any],
        step_number: int,
        current_step: Dict[str, Any],
        previous_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute a single step with retries and circuit breaker protection."""
        
        tool_name = current_step["tool"]
        tool_input = current_step["input"]
        
        # Circuit breaker check
        if not self.circuit_breakers.allow_request(tool_name):
            logger.warning(f"🚫 Circuit breaker OPEN for {tool_name}")
            breaker_metrics = self.circuit_breakers.get_breaker(tool_name).get_metrics()
            return {
                "step": step_number,
                "tool": tool_name,
                "input": tool_input,
                "output": create_error_response(
                    message=f"Circuit breaker OPEN - {breaker_metrics['failure_rate']:.1%} failure rate",
                    error_code=ErrorCodes.E_CIRCUIT_OPEN
                ),
                "success": False,
                "circuit_breaker_blocked": True
            }
        
        # Check cache first
        cached_result = self.tool_registry.get_cached_result(tool_name, tool_input)
        if cached_result:
            logger.info(f"📦 Cache hit for {tool_name}")
            return {
                "step": step_number,
                "tool": tool_name,
                "input": tool_input,
                "output": json.loads(cached_result),
                "success": True,
                "cache_hit": True
            }
        
        # Execute with retries
        for attempt in range(self.max_retries + 1):
            try:
                start_time = time.time()
                
                # Execute the actual tool
                result = await self._execute_tool(tool_name, tool_input)
                execution_time = time.time() - start_time
                
                # Parse result
                result_data = json.loads(result) if isinstance(result, str) else result
                success = result_data.get("success", True)
                
                # Record circuit breaker result
                self.circuit_breakers.record_result(tool_name, success)
                
                if success:
                    # Cache successful results
                    self.tool_registry.cache_result(tool_name, tool_input, 
                                                  json.dumps(result_data))
                    
                    # Sanitize output
                    sanitized_output = self._sanitize_tool_output(result_data)
                    
                    return {
                        "step": step_number,
                        "tool": tool_name,
                        "input": tool_input,
                        "output": sanitized_output,
                        "success": True,
                        "execution_time": execution_time
                    }
                else:
                    # Handle failure with potential retry
                    error_code = result_data.get("error_code", ErrorCodes.E_TOOL_FAILED)
                    if attempt < self.max_retries and error_code in [ErrorCodes.E_TIMEOUT, ErrorCodes.E_RATE_LIMIT]:
                        wait_time = 0.25 * (2 ** attempt)
                        logger.warning(f"🔄 Retrying {tool_name} in {wait_time}s (attempt {attempt + 1})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        return {
                            "step": step_number,
                            "tool": tool_name,
                            "input": tool_input,
                            "output": self._sanitize_tool_output(result_data),
                            "success": False,
                            "error": result_data.get("error", "Tool execution failed")
                        }
                        
            except Exception as e:
                # Record exception as failure
                self.circuit_breakers.record_result(tool_name, False)
                
                if attempt < self.max_retries:
                    wait_time = 0.25 * (2 ** attempt)
                    logger.warning(f"🔄 Exception in {tool_name}, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    return {
                        "step": step_number,
                        "tool": tool_name,
                        "input": tool_input,
                        "output": create_error_response(
                            message=f"Tool execution failed: {str(e)}",
                            error_code=ErrorCodes.E_TOOL_FAILED
                        ),
                        "success": False
                    }
    
    async def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Execute the actual tool function."""
        
        # ChatGPT suggested debugging for add_client - log inputs before execution
        if tool_name == "add_client":
            logger.info(f"🔍 add_client.input: {tool_input}")
            
            # Validate input against schema as ChatGPT suggested
            try:
                from .validator import _schema_validate
                tool_metadata = self.tool_registry.get_tool_metadata(tool_name)
                if tool_metadata and 'input_schema' in tool_metadata:
                    validation_errors = _schema_validate(tool_input, tool_metadata['input_schema'])
                    if validation_errors:
                        logger.error(f"❌ add_client.schema_error: {validation_errors}")
                        return json.dumps(create_error_response(
                            message=f"Input validation failed: {validation_errors}",
                            error_code=ErrorCodes.E_SCHEMA
                        ))
            except Exception as e:
                logger.warning(f"⚠️ Schema validation failed: {e}")
        
        # Import and execute tool functions
        if tool_name == "add_task":
            from ..tools.tasks import add_task
            return await add_task(**tool_input)
        elif tool_name == "list_tasks":
            from ..tools.tasks import list_tasks
            return await list_tasks(**tool_input)
        elif tool_name == "calculate_percentage":
            from ..tools.calculator import calculate_percentage
            return await calculate_percentage(**tool_input)
        elif tool_name == "get_current_time":
            from ..tools.datetime_info import get_current_time
            return await get_current_time(**tool_input)
        elif tool_name == "add_client":
            from ..tools.client_management import add_client
            result = await add_client(**tool_input)
            
            # ChatGPT suggested debugging - log the tool result envelope
            logger.info(f"🔍 add_client.result: {result}")
            return result
        else:
            return json.dumps(create_error_response(
                message=f"Unknown tool: {tool_name}",
                error_code=ErrorCodes.E_TOOL_UNKNOWN
            ))
    
    def _extract_task_description(self, user_request: str) -> str:
        """Extract task description from user request."""
        import re
        
        # Try different patterns to extract task description
        patterns = [
            # Single or double quotes
            r"['\"]([^'\"]+)['\"]",
            # "Add a task called X"
            r"task called (.+?)(?:,|$|\.|then|and)",
            # "Add a task named X"  
            r"task named (.+?)(?:,|$|\.|then|and)",
            # "Add task X"
            r"add task (.+?)(?:,|$|\.|then|and)",
            # "Create task X"
            r"create task (.+?)(?:,|$|\.|then|and)",
            # "Add X to my tasks"
            r"add (.+?) to my tasks",
        ]
        
        request_lower = user_request.lower()
        
        for pattern in patterns:
            match = re.search(pattern, request_lower, re.IGNORECASE)
            if match:
                task_desc = match.group(1).strip()
                # Clean up common words that get captured
                task_desc = re.sub(r'^(a|an|the)\s+', '', task_desc, flags=re.IGNORECASE)
                if len(task_desc) > 2:  # Avoid single letters or very short captures
                    return task_desc.title()  # Capitalize properly
        
        # If no pattern matches, try to extract anything after "task"
        if "task" in request_lower:
            # Find content after the word "task"
            task_idx = request_lower.find("task")
            after_task = user_request[task_idx + 4:].strip()
            # Remove common prefixes
            after_task = re.sub(r'^(called|named|to|for|about|regarding)\s+', '', after_task, flags=re.IGNORECASE)
            if len(after_task) > 2:
                # Take first reasonable chunk (up to comma, period, or "then")
                chunk_match = re.match(r'([^,\.]+?)(?:\s*(?:,|\.|then|and)\s|$)', after_task, re.IGNORECASE)
                if chunk_match:
                    return chunk_match.group(1).strip().title()
        
        # Final fallback - try to get something meaningful from the request
        # Remove common words and take the most substantial remaining content
        cleaned = re.sub(r'\b(add|create|make|new|a|an|the|my|to|for|please|can|you|i|want|need)\b', '', request_lower, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        if len(cleaned) > 2:
            return cleaned.title()
        
        # Last resort fallback
        return "New Task"
    
    def _sanitize_tool_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Apply PII sanitization to tool output."""
        if not output:
            return output
        
        sanitized = output.copy()
        
        # Sanitize string fields
        for field in ['message', 'data', 'error', 'description']:
            if field in sanitized and isinstance(sanitized[field], str):
                sanitized[field] = sanitize_observation(sanitized[field])
        
        return sanitized
    
    def _create_partial_response(self, user_request: str, completed_results: List[Dict[str, Any]], 
                                remaining_steps: List[Dict[str, Any]]) -> str:
        """Create response for partial execution due to deadline."""
        return json.dumps(create_error_response(
            message=f"Partial execution: {len(completed_results)} steps completed, {len(remaining_steps)} remaining due to deadline",
            error_code=ErrorCodes.E_DEADLINE,
            data={
                "completed_steps": len(completed_results),
                "remaining_steps": len(remaining_steps),
                "results": completed_results
            }
        ))
    
    async def _generate_final_response(self, user_request: str, plan: Dict[str, Any], 
                                     results: List[Dict[str, Any]]) -> str:
        """Generate user-friendly final response from execution results."""
        success_count = sum(1 for r in results if r.get("success", True))
        total_steps = len(results)
        
        # Collect data from different tools
        response_data = {
            "steps_completed": total_steps,
            "execution_summary": f"{success_count}/{total_steps} steps successful"
        }
        
        if success_count == total_steps:
            # Generate user-friendly messages based on tools used
            message_parts = []
            
            for result in results:
                tool_name = result["tool"]
                if not result.get("success", True):
                    continue
                    
                output = result.get("output", {})
                
                if tool_name == "add_task":
                    # Extract task description from the result
                    task_desc = result.get("input", {}).get("description", "task")
                    message_parts.append(f"✅ Added task: '{task_desc}'")
                
                elif tool_name == "list_tasks":
                    data = output.get("data", {})
                    input_params = result.get("input", {})
                    
                    # Check if any filtering was applied
                    is_filtered = bool(input_params.get("status") or 
                                     input_params.get("query") or 
                                     input_params.get("client_name") or 
                                     input_params.get("client_id"))
                    
                    if isinstance(data, dict) and "tasks" in data:
                        tasks = data["tasks"]
                        total = len(tasks)
                        pending = data.get("pending_count", 0)
                        completed = data.get("completed_count", 0)
                        
                        if is_filtered:
                            # For filtered results, use the full detailed output from list_tasks
                            full_message = output.get("message", "")
                            if full_message:
                                message_parts.append(full_message)
                            else:
                                # Fallback to summary if no message
                                filter_desc = ""
                                if input_params.get("status"):
                                    filter_desc = f" ({input_params['status']} only)"
                                elif input_params.get("query"):
                                    filter_desc = f" matching '{input_params['query']}'"
                                elif input_params.get("client_name"):
                                    filter_desc = f" for {input_params['client_name']}"
                                
                                summary = f"📋 Found {total} tasks{filter_desc}"
                                message_parts.append(summary)
                        else:
                            # For unfiltered "list all tasks", use summary format
                            summary = f"📋 Found {total} tasks ({pending} pending, {completed} completed)"
                            
                            # Show up to 5 most recent tasks
                            recent_tasks = []
                            displayed_tasks = tasks[-5:] if len(tasks) > 5 else tasks
                            
                            for task in displayed_tasks:
                                status_icon = "✅" if task.get("completed", False) else "⏳"
                                task_desc = task.get("description", "Untitled task")
                                client_info = f" (for {task.get('client_name')})" if task.get('client_name') else ""
                                recent_tasks.append(f"{status_icon} {task_desc}{client_info}")
                            
                            if recent_tasks:
                                if len(tasks) > 5:
                                    task_list = f"\n\nRecent tasks:\n" + "\n".join(recent_tasks) + f"\n...and {len(tasks)-5} more"
                                else:
                                    task_list = f"\n\nYour tasks:\n" + "\n".join(recent_tasks)
                                message_parts.append(summary + task_list)
                            else:
                                message_parts.append(summary)
                                
                        response_data["task_data"] = data
                    else:
                        message_parts.append("📋 Listed your tasks")
                
                elif tool_name == "calculate_percentage":
                    calc_data = output.get("data", {})
                    if isinstance(calc_data, dict) and "result" in calc_data:
                        result_val = calc_data["result"]
                        expression = calc_data.get("expression", "calculation")
                        message_parts.append(f"🧮 {expression} = {result_val}")
                        response_data["calculation_result"] = calc_data
                    else:
                        message_parts.append("🧮 Calculation completed")
                
                elif tool_name == "get_current_time":
                    time_data = output.get("current_time", "")
                    if time_data:
                        message_parts.append(f"🕒 Current time: {time_data}")
                    else:
                        message_parts.append("🕒 Retrieved current time")
                
                elif tool_name == "add_client":
                    client_name = result.get("input", {}).get("name", "client")
                    message_parts.append(f"👤 Added client: '{client_name}'")
                
                else:
                    # Generic success message for other tools
                    tool_display = tool_name.replace("_", " ").title()
                    message_parts.append(f"✅ {tool_display} completed")
            
            # Create final message
            if message_parts:
                if len(message_parts) == 1:
                    message = message_parts[0]
                elif len(message_parts) == 2:
                    message = f"{message_parts[0]}, then {message_parts[1].lower()}"
                else:
                    message = f"{', '.join(message_parts[:-1])}, and {message_parts[-1].lower()}"
            else:
                message = "✅ All operations completed successfully"
            
            return json.dumps(create_error_response(
                success=True,
                message=message,
                data=response_data
            ))
        else:
            # Handle failures
            failed_steps = [r for r in results if not r.get("success", True)]
            failed_tools = [r["tool"].replace("_", " ").title() for r in failed_steps]
            
            if len(failed_tools) == 1:
                message = f"❌ {failed_tools[0]} failed"
            else:
                message = f"❌ {len(failed_steps)} operations failed: {', '.join(failed_tools)}"
                
            return json.dumps(create_error_response(
                message=message,
                error_code=ErrorCodes.E_TOOL_FAILED,
                data={
                    **response_data,
                    "steps_successful": success_count,
                    "failed_steps": failed_steps
                }
            ))
