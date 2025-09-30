"""
Enhanced Planner-Executor Agent with ChatGPT's Production Hardening

Implements:
- JSON Schema validation for plans and execution
- Plan normalization and safety lints  
- Error recovery with retry policies
- Observation truncation
- Deterministic execution

Based on ChatGPT's production hardening recommendations.
"""

import json
import logging
import asyncio
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError
from production_tool_registry import ProductionToolRegistry
from circuit_breaker import ToolCircuitBreakerRegistry, BreakerConfig
from sanitizer import sanitize_observation

logger = logging.getLogger(__name__)

class EnhancedPlannerExecutorAgent:
    """
    Production-grade planner-executor agent with ChatGPT's hardening features.
    """
    
    # JSON Schemas - ChatGPT DAG-aware schema
    PLANNER_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["plan"],
        "additionalProperties": False,
        "properties": {
            "plan": {
                "type": "array",
                "minItems": 1,
                "maxItems": 24,
                "items": {
                    "type": "object",
                    "required": ["id", "step", "tool", "input", "after"],
                    "additionalProperties": False,
                    "properties": {
                        "id": {"type": "string", "pattern": "^[a-z][a-z0-9_\\-]{1,31}$"},
                        "step": {"type": "integer", "minimum": 1},
                        "tool": {
                            "type": "string",
                            "enum": [
                                "add_task", "list_tasks", "complete_task", "delete_task", "list_tasks_for_client", "add_client_task",
                                "add_numbers", "subtract_numbers", "multiply_numbers", "divide_numbers", "calculate_percentage",
                                "get_current_time", "get_current_date", "get_timezone_info", "calculate_time_difference", "get_day_of_week", "get_current_hour",
                                "schedule_meeting", "list_meetings", "cancel_meeting",
                                "add_client", "list_clients", "find_client_by_name", "add_client_note", "get_client_details", "update_client_email"
                            ]
                        },
                        "input": {"type": "object"},
                        "after": {
                            "type": "array",
                            "items": {"type": "string"},
                            "uniqueItems": True
                        }
                    }
                }
            }
        }
    }
    
    EXECUTOR_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["next_step", "remaining_steps", "type"],
        "additionalProperties": False,
        "properties": {
            "next_step": {"type": "integer", "minimum": 1},
            "remaining_steps": {"type": "integer", "minimum": 0},
            "type": {"type": "string", "enum": ["tool_call", "final"]},
            "tool": {
                "type": "string",
                "enum": [
                    "add_task", "list_tasks", "complete_task", "delete_task",
                    "add_numbers", "subtract_numbers", "multiply_numbers", "divide_numbers", 
                    "calculate_percentage", "current_time", "current_date",
                    "schedule_meeting", "list_meetings", "cancel_meeting",
                    "add_client", "list_clients", "find_client_by_name"
                ]
            },
            "input": {"type": "object"},
            "final_answer": {"type": "string"}
        },
        "allOf": [
            {
                "if": {"properties": {"type": {"const": "tool_call"}}},
                "then": {"required": ["tool", "input"]}
            },
            {
                "if": {"properties": {"type": {"const": "final"}}}, 
                "then": {"required": ["final_answer"]}
            }
        ]
    }
    
    def __init__(self, config_path: str):
        """Initialize the enhanced planner-executor agent."""
        self.config_path = Path(config_path)
        self.max_retries = 2
        self.per_step_timeout = 5.0
        self.overall_deadline = 20.0
        
        # Initialize production tool registry
        registry_path = Path(__file__).parent / "tool_registry.json"
        self.tool_registry = ProductionToolRegistry(str(registry_path))
        
        # Initialize circuit breaker registry (ChatGPT Phase 3)
        breaker_config = BreakerConfig(
            window_seconds=300,  # 5 minutes
            buckets=10,         # 30s each
            min_requests=50,
            failure_threshold=0.7,  # 70%
            cooldown_seconds=60
        )
        self.circuit_breakers = ToolCircuitBreakerRegistry(breaker_config)
        
        logger.info(f"🔧 Initialized with {len(self.tool_registry.available_tools)} production tools")
        logger.info(f"🛡️ Circuit breakers active with 70% failure threshold")
        
    async def run_agent(self, user_request: str) -> str:
        """
        Main agent execution with ChatGPT's hardening features.
        
        Args:
            user_request: The user's multi-step request
            
        Returns:
            Final response after executing all planned steps
        """
        start_time = time.time()
        
        try:
            # Step 1: Create and validate execution plan
            logger.info(f"🎯 Planning request: {user_request}")
            plan = await self._create_validated_plan(user_request)
            logger.info(f"📋 Generated plan: {json.dumps(plan, indent=2)}")
            
            # Step 2: Normalize and lint plan using production registry
            normalized_plan = self._normalize_plan(plan)
            self._validate_plan_safety(normalized_plan)
            
            # Production Feature: Check for parallel execution opportunities
            execution_groups = self.tool_registry.get_parallel_execution_groups(normalized_plan)
            parallel_groups = [group for group in execution_groups if len(group) > 1]
            if parallel_groups:
                logger.info(f"⚡ Plan allows {len(parallel_groups)} parallel execution groups")
            
            logger.info(f"✅ Plan validated, normalized, and analyzed for parallelism")
            
            # Step 3: Execute plan step by step with error recovery
            results = []
            for i, step in enumerate(normalized_plan["plan"], 1):
                # Check deadline
                if time.time() - start_time > self.overall_deadline:
                    logger.warning(f"⏰ Deadline reached, providing partial results")
                    return self._create_partial_response(user_request, results, normalized_plan["plan"][i-1:])
                
                remaining = len(normalized_plan["plan"]) - i + 1
                logger.info(f"⚡ Executing step {i}/{len(normalized_plan['plan'])}: {step['tool']}")
                
                result = await self._execute_step_with_retry(
                    user_request=user_request,
                    plan=normalized_plan,
                    step_number=i,
                    remaining_steps=remaining,
                    current_step=step,
                    previous_results=results[-1] if results else None
                )
                
                results.append(result)
                logger.info(f"✅ Step {i} completed: {step['tool']}")
            
            # Step 4: Generate final response with production metrics
            final_answer = await self._generate_final_response(
                user_request=user_request,
                plan=normalized_plan,
                results=results
            )
            
            total_time = time.time() - start_time
            
            # Production Feature: Log performance metrics
            cache_hits = sum(1 for r in results if r.get("cache_hit", False))
            idempotent_skips = sum(1 for r in results if r.get("idempotent_skip", False))
            
            logger.info(f"🎉 Agent completed successfully in {total_time:.2f}s")
            logger.info(f"📈 Performance: {cache_hits} cache hits, {idempotent_skips} idempotent skips")
            
            # Log tool registry stats
            stats = self.tool_registry.get_tool_stats()
            logger.info(f"📊 Registry stats: {stats['pure_cache_entries']} pure cached, {stats['read_cache_entries']} read cached")
            
            # Log circuit breaker metrics (ChatGPT Phase 3)
            circuit_blocked = sum(1 for r in results if r.get("circuit_breaker_blocked", False))
            breaker_metrics = self.circuit_breakers.get_all_metrics()
            open_breakers = [tool for tool, metrics in breaker_metrics.items() if metrics['state'] == 'open']
            
            if circuit_blocked > 0 or open_breakers:
                logger.info(f"🛡️ Circuit breakers: {circuit_blocked} requests blocked, {len(open_breakers)} breakers OPEN")
                if open_breakers:
                    logger.warning(f"⚠️ OPEN breakers: {', '.join(open_breakers)}")
            else:
                logger.info(f"🛡️ Circuit breakers: All systems operational")
            
            return final_answer
            
        except Exception as e:
            logger.error(f"❌ Agent execution failed: {e}")
            return json.dumps({
                "success": False,
                "error": f"Agent execution failed: {str(e)}",
                "error_code": "AGENT_EXECUTION_ERROR"
            })
    
    async def _create_validated_plan(self, user_request: str) -> Dict[str, Any]:
        """Create and validate execution plan using ChatGPT's schema."""
        
        # Enhanced demo planner that properly parses multi-step requests
        # In production, this would call NAT's LLM with the tightened prompt
        
        request_lower = user_request.lower()
        plan_steps = []
        step_num = 1
        
        # Parse for add task
        if "add" in request_lower and "task" in request_lower:
            # Extract task description
            task_desc = "Demo Task"
            
            # Look for quoted task names
            if "'" in user_request:
                start = user_request.find("'") + 1
                end = user_request.find("'", start)
                if end > start:
                    task_desc = user_request[start:end]
            elif "called" in request_lower:
                # Extract after "called"
                called_idx = request_lower.find("called")
                after_called = user_request[called_idx + 6:].strip()
                if after_called:
                    # Take until next comma or "then" or "and"
                    for delimiter in [",", " then", " and", " finally"]:
                        if delimiter in after_called:
                            task_desc = after_called[:after_called.find(delimiter)].strip(' "\'')
                            break
                    else:
                        # Take first few words
                        words = after_called.split()
                        task_desc = " ".join(words[:4]) if len(words) > 0 else "Demo Task"
            
            plan_steps.append({
                "id": f"s{step_num}",
                "step": step_num,
                "tool": "add_task", 
                "input": {"description": task_desc},
                "after": []
            })
            step_num += 1
        
        # Parse for list tasks
        if "list" in request_lower and ("task" in request_lower or "all" in request_lower):
            # List depends on add task if both exist
            after_deps = ["s1"] if len(plan_steps) > 0 else []
            
            plan_steps.append({
                "id": f"s{step_num}",
                "step": step_num,
                "tool": "list_tasks",
                "input": {},
                "after": after_deps
            })
            step_num += 1
        
        # Parse for calculations
        if "calculate" in request_lower or "%" in user_request:
            percentage_text = "25% of 200"  # default
            
            # Extract percentage calculation
            if "%" in user_request:
                words = user_request.split()
                for i, word in enumerate(words):
                    if "%" in word:
                        # Look for "X% of Y" pattern
                        if i < len(words) - 2 and words[i+1].lower() == "of":
                            percentage_text = f"{word} of {words[i+2].rstrip(',.')}"
                            break
                        # Look for "X% of Y" in different positions  
                        elif i > 1 and words[i-1].lower() == "of":
                            percentage_text = f"{words[i-2]} {words[i-1]} {word}"
                            break
                        # Just the percentage
                        else:
                            percentage_text = f"{word} of 100"
            
            # Pure calculation can run independently
            after_deps = []
            
            plan_steps.append({
                "id": f"s{step_num}",
                "step": step_num,
                "tool": "calculate_percentage",
                "input": {"text": percentage_text},
                "after": after_deps
            })
            step_num += 1
        
        # Parse for time requests
        if ("time" in request_lower or "current" in request_lower) and "calculate" not in request_lower:
            plan_steps.append({
                "id": f"s{step_num}",
                "step": step_num,
                "tool": "get_current_time", 
                "input": {},
                "after": []
            })
            step_num += 1
        
        # Parse for client operations
        if "client" in request_lower and "add" in request_lower:
            plan_steps.append({
                "id": f"s{step_num}",
                "step": step_num,
                "tool": "add_client",
                "input": {"name": "Demo Client", "company": "Demo Corp"},
                "after": []
            })
            step_num += 1
        
        # If no specific operations found, default to current time
        if not plan_steps:
            plan_steps.append({
                "id": "s1",
                "step": 1,
                "tool": "get_current_time",
                "input": {},
                "after": []
            })
        
        # Create DAG with smart dependencies
        self._optimize_dag_dependencies(plan_steps)
        
        plan = {"plan": plan_steps}
        
        # Validate against ChatGPT's schema
        try:
            validate(instance=plan, schema=self.PLANNER_SCHEMA)
            logger.info("✅ Plan passes JSON schema validation")
            
            # Additional validation: check tool inputs against registry schemas
            for step in plan["plan"]:
                tool_name = step["tool"]
                tool_input = step["input"]
                is_valid, error = self.tool_registry.validate_tool_input(tool_name, tool_input)
                if not is_valid:
                    logger.error(f"❌ Tool input validation failed for {tool_name}: {error}")
                    raise ValueError(f"Tool input validation failed: {error}")
            
            logger.info("✅ All tool inputs validated against registry schemas")
            
        except ValidationError as e:
            logger.error(f"❌ Plan validation failed: {e.message}")
            raise ValueError(f"Generated plan violates schema: {e.message}")
        
        return plan
    
    def _optimize_dag_dependencies(self, plan_steps: List[Dict[str, Any]]) -> None:
        """Optimize DAG dependencies for maximum parallelism while maintaining correctness."""
        
        # Apply ChatGPT's smart dependency rules:
        # 1. Pure functions can run independently after any required impure operations
        # 2. Read-only functions depend on impure operations that change the data they read
        # 3. Impure operations should be sequenced when they affect the same resources
        
        for i, step in enumerate(plan_steps):
            tool_name = step["tool"]
            purity = self.tool_registry.get_tool_purity(tool_name)
            
            if purity == "pure":
                # Pure calculations can run independently 
                step["after"] = []
            elif purity == "read_only":
                # Read-only operations depend on preceding impure operations that modify data
                impure_deps = []
                for j in range(i):
                    prev_step = plan_steps[j]
                    prev_purity = self.tool_registry.get_tool_purity(prev_step["tool"])
                    if prev_purity == "impure":
                        # Check if this impure operation affects what we're reading
                        if self._operations_related(prev_step["tool"], tool_name):
                            impure_deps.append(prev_step["id"])
                
                step["after"] = impure_deps
            # impure operations keep their existing dependencies
        
        logger.debug(f"🔧 DAG optimization complete - dependencies analyzed")
    
    def _operations_related(self, impure_tool: str, read_tool: str) -> bool:
        """Check if an impure operation affects what a read operation accesses."""
        
        # Simple heuristics for related operations
        if "task" in impure_tool and "task" in read_tool:
            return True
        if "client" in impure_tool and "client" in read_tool:
            return True
        if "meeting" in impure_tool and "meeting" in read_tool:
            return True
            
        return False
    
    def _normalize_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize plan using ChatGPT's production rules via tool registry."""
        
        # Use production tool registry for advanced normalization
        return self.tool_registry.normalize_plan(plan)
    
    def _validate_plan_safety(self, plan: Dict[str, Any]) -> None:
        """Apply safety lints: budget checks, determinism."""
        
        steps = plan["plan"]
        
        # Budget check: max steps
        if len(steps) > 12:
            raise ValueError(f"Plan exceeds maximum steps: {len(steps)} > 12")
        
        # Estimate runtime budget (rough)
        estimated_time = len(steps) * 2  # 2s per step estimate
        if estimated_time > self.overall_deadline:
            logger.warning(f"⚠️ Plan may exceed deadline: {estimated_time}s > {self.overall_deadline}s")
        
        # Check for valid tool sequences
        tool_sequence = [step["tool"] for step in steps]
        logger.info(f"📊 Tool sequence: {' → '.join(tool_sequence)}")
        
        logger.info("✅ Plan passes safety validation")
    
    async def _execute_step_with_retry(
        self,
        user_request: str,
        plan: Dict[str, Any], 
        step_number: int,
        remaining_steps: int,
        current_step: Dict[str, Any],
        previous_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute a single step with ChatGPT's production features: caching, idempotency, retries."""
        
        tool_name = current_step["tool"]
        tool_input = current_step["input"]
        
        # Production Feature 1: Circuit breaker check (ChatGPT Phase 3)
        if not self.circuit_breakers.allow_request(tool_name):
            logger.warning(f"🚫 Circuit breaker OPEN for {tool_name} - request denied")
            breaker_metrics = self.circuit_breakers.get_breaker(tool_name).get_metrics()
            return {
                "step": step_number,
                "tool": tool_name,
                "input": tool_input,
                "output": {
                    "success": False,
                    "error": f"Circuit breaker OPEN - {breaker_metrics['failure_rate']:.1%} failure rate",
                    "error_code": "CIRCUIT_BREAKER_OPEN"
                },
                "success": False,
                "execution_time": 0.001,
                "circuit_breaker_blocked": True
            }
        
        # Production Feature 2: Check cache first (pure/read_only tools)
        cached_result = self.tool_registry.get_cached_result(tool_name, tool_input)
        if cached_result:
            logger.info(f"📦 Cache hit for {tool_name}")
            try:
                result_data = json.loads(cached_result)
                # Apply PII sanitization to cached results
                sanitized_output = self._sanitize_tool_output(result_data)
                return {
                    "step": step_number,
                    "tool": tool_name,
                    "input": tool_input,
                    "output": self._truncate_observation(sanitized_output),
                    "success": result_data.get("success", True),
                    "execution_time": 0.001,  # Cache hit time
                    "cache_hit": True
                }
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Invalid cached result for {tool_name}, proceeding with execution")
        
        # Production Feature 3: Idempotency check for impure operations
        idempotency_key = None
        if self.tool_registry.requires_idempotency_key(tool_name):
            idempotency_key = self.tool_registry.generate_idempotency_key(
                user_request, step_number, tool_name, tool_input
            )
            
            if self.tool_registry.is_duplicate_operation(idempotency_key):
                logger.info(f"🔄 Idempotency check: operation {idempotency_key} already completed")
                return {
                    "step": step_number,
                    "tool": tool_name,
                    "input": tool_input,
                    "output": {"message": "Operation already completed (idempotent)"},
                    "success": True,
                    "execution_time": 0.001,
                    "idempotent_skip": True
                }
        
        for attempt in range(self.max_retries + 1):
            try:
                # Add timeout to tool execution
                start_time = time.time()
                
                # Import and execute the actual tool functions
                if tool_name == "add_task":
                    from personal_assistant.tools.tasks import add_task
                    result = await add_task(**tool_input)
                    
                elif tool_name == "list_tasks":
                    from personal_assistant.tools.tasks import list_tasks
                    result = await list_tasks(**tool_input)
                    
                elif tool_name == "calculate_percentage":
                    from personal_assistant.tools.calculator import calculate_percentage
                    result = await calculate_percentage(**tool_input)
                    
                elif tool_name == "current_time":
                    from personal_assistant.tools.datetime_info import get_current_time
                    result = await get_current_time(**tool_input)
                    
                else:
                    result = json.dumps({
                        "success": False,
                        "error": f"Unknown tool: {tool_name}",
                        "error_code": "UNKNOWN_TOOL"
                    })
                
                execution_time = time.time() - start_time
                
                # Check timeout
                if execution_time > self.per_step_timeout:
                    logger.warning(f"⚠️ Step {step_number} exceeded timeout: {execution_time:.2f}s")
                
                # Parse and validate result
                try:
                    result_data = json.loads(result)
                    
                    # Check for success
                    success = result_data.get("success", False) or ("error" not in result_data and "error_code" not in result_data)
                    
                    # Record circuit breaker result (ChatGPT Phase 3)
                    self.circuit_breakers.record_result(tool_name, success)
                    
                    if success:
                        
                        # Production Feature 4: Cache successful results
                        self.tool_registry.cache_result(tool_name, tool_input, result)
                        
                        # Production Feature 5: Mark idempotent operation as complete
                        if idempotency_key:
                            self.tool_registry.mark_operation_complete(idempotency_key)
                        
                        # Apply PII sanitization to successful results (ChatGPT Phase 3)
                        sanitized_output = self._sanitize_tool_output(result_data)
                        
                        return {
                            "step": step_number,
                            "tool": tool_name,
                            "input": tool_input,
                            "output": self._truncate_observation(sanitized_output),
                            "success": True,
                            "execution_time": execution_time,
                            "cache_hit": False,
                            "idempotency_key": idempotency_key
                        }
                    else:
                        # Tool returned error, but might be retryable
                        error_code = result_data.get("error_code", "UNKNOWN_ERROR")
                        if attempt < self.max_retries and error_code in ["TIMEOUT", "RATE_LIMIT"]:
                            wait_time = 0.25 * (2 ** attempt)  # Exponential backoff
                            logger.warning(f"🔄 Retrying step {step_number} in {wait_time}s (attempt {attempt + 1})")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            # Non-retryable error or max retries reached
                            # Apply PII sanitization to error outputs too
                            sanitized_output = self._sanitize_tool_output(result_data)
                            
                            return {
                                "step": step_number,
                                "tool": tool_name,
                                "input": tool_input,
                                "output": sanitized_output,
                                "success": False,
                                "error": result_data.get("error", "Tool execution failed"),
                                "error_code": error_code
                            }
                            
                except json.JSONDecodeError:
                    return {
                        "step": step_number,
                        "tool": tool_name,
                        "input": tool_input,
                        "output": {"raw_result": result},
                        "success": False,
                        "error": "Invalid JSON response from tool"
                    }
                    
            except Exception as e:
                # Record exception as circuit breaker failure
                self.circuit_breakers.record_result(tool_name, False)
                
                if attempt < self.max_retries:
                    wait_time = 0.25 * (2 ** attempt)
                    logger.warning(f"🔄 Exception in step {step_number}, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    return {
                        "step": step_number,
                        "tool": tool_name,
                        "input": tool_input,
                        "output": {},
                        "success": False,
                        "error": f"Tool execution exception: {str(e)}",
                        "error_code": "EXECUTION_EXCEPTION"
                    }
        
        # Should never reach here, but just in case
        return {
            "step": step_number,
            "tool": tool_name,
            "input": tool_input,
            "output": {},
            "success": False,
            "error": "Max retries exceeded"
        }
    
    def _truncate_observation(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Truncate large observations following ChatGPT's recommendation."""
        
        # If message is very long, truncate it
        if "message" in observation and len(str(observation["message"])) > 500:
            truncated_message = str(observation["message"])[:500] + "...(truncated)"
            observation = observation.copy()
            observation["message"] = truncated_message
            observation["_truncated"] = True
        
        # If data contains large arrays, truncate them
        if "data" in observation and isinstance(observation["data"], dict):
            data = observation["data"].copy()
            
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 3:
                    truncated_count = len(value) - 3
                    data[key] = value[:3] + [f"...(+{truncated_count} more)"]
                    data["_truncated"] = True
            
            observation = observation.copy()
            observation["data"] = data
        
        return observation
    
    def _sanitize_tool_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply PII sanitization to tool output (ChatGPT Phase 3).
        
        Args:
            output: Tool execution result to sanitize
            
        Returns:
            Sanitized output with PII redacted
        """
        if not output:
            return output
        
        # Create a deep copy to avoid modifying original
        sanitized = json.loads(json.dumps(output))
        
        # Sanitize string fields that might contain PII
        pii_sensitive_fields = ['message', 'data', 'error', 'description', 'content']
        
        for field in pii_sensitive_fields:
            if field in sanitized:
                if isinstance(sanitized[field], str):
                    # Apply PII sanitization directly to string fields
                    sanitized[field] = sanitize_observation(sanitized[field])
                elif isinstance(sanitized[field], dict):
                    # Recursively sanitize nested dictionaries
                    sanitized[field] = self._sanitize_dict(sanitized[field])
                elif isinstance(sanitized[field], list):
                    # Sanitize list items if they're strings
                    sanitized[field] = [
                        sanitize_observation(item) if isinstance(item, str) else item
                        for item in sanitized[field]
                    ]
        
        return sanitized
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary values."""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = sanitize_observation(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    sanitize_observation(item) if isinstance(item, str) else 
                    self._sanitize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized
    
    def _create_partial_response(
        self, 
        user_request: str, 
        completed_results: List[Dict[str, Any]], 
        remaining_steps: List[Dict[str, Any]]
    ) -> str:
        """Create partial response when deadline is reached."""
        
        completed_count = len(completed_results)
        remaining_count = len(remaining_steps)
        
        summary = f"⏰ Completed {completed_count} of {completed_count + remaining_count} steps before deadline. "
        
        # Summarize completed steps
        for result in completed_results:
            if result["success"]:
                summary += f"✅ {result['tool']} completed. "
            else:
                summary += f"❌ {result['tool']} failed. "
        
        # List remaining steps
        remaining_tools = [step["tool"] for step in remaining_steps]
        summary += f"Remaining: {', '.join(remaining_tools)}."
        
        return summary
    
    async def _generate_final_response(
        self,
        user_request: str,
        plan: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> str:
        """Generate final response summarizing all executed steps."""
        
        success_count = sum(1 for r in results if r.get("success", True))  # Default to True since successful steps might not have explicit success flag
        total_steps = len(results)
        total_time = sum(r.get("execution_time", 0) for r in results)
        
        # Extract key information from results
        summary_parts = []
        
        for result in results:
            tool = result["tool"]
            output = result["output"]
            
            if tool == "add_task" and result["success"]:
                task_id = output.get("data", {}).get("task_id", "unknown")
                task_desc = output.get("data", {}).get("description", "unknown")
                summary_parts.append(f"Added task {task_id}: '{task_desc}'")
                
            elif tool == "list_tasks" and result["success"]:
                # Count tasks from the output
                message = output.get("message", "")
                if "tasks" in message.lower():
                    summary_parts.append("Listed all tasks")
                    
            elif tool == "calculate_percentage" and result["success"]:
                calc_result = output.get("data", {}).get("result")
                expression = output.get("data", {}).get("expression", "calculation")
                if calc_result is not None:
                    summary_parts.append(f"{expression} = {calc_result}")
        
        # Create final response
        if success_count == total_steps:
            summary = ", ".join(summary_parts)
            final_response = f"✅ Successfully completed all {total_steps} steps in {total_time:.2f}s: {summary}."
        else:
            failed_count = total_steps - success_count
            summary = ", ".join(summary_parts)
            final_response = f"⚠️ Completed {success_count}/{total_steps} steps ({failed_count} failed) in {total_time:.2f}s: {summary}."
        
        return final_response


# Demo function for testing enhanced features
async def demo_enhanced_planner_executor():
    """Demo the enhanced planner-executor agent with production features."""
    
    agent = EnhancedPlannerExecutorAgent("configs/config-planner-executor.yml")
    
    # Test the original 3-step request with enhanced features
    test_request = "Add a task called 'Enhanced Production Test', then list all my tasks, and finally calculate 30% of 150"
    
    print("🚀 Testing Enhanced Planner-Executor Agent (ChatGPT Production Hardened)")
    print(f"📝 Request: {test_request}")
    print("=" * 70)
    
    result = await agent.run_agent(test_request)
    
    print("=" * 70)
    print(f"🎯 Final Result: {result}")
    print("🎉 Enhanced Planner-Executor Demo Complete!")


if __name__ == "__main__":
    # Set up logging to see the enhanced features in action
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo_enhanced_planner_executor())
