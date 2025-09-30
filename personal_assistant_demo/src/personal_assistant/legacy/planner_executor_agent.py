"""
Planner-Executor Agent Implementation (ChatGPT Option A)

This implementation eliminates ReAct drift by separating planning from execution:
1. Planner: Creates JSON execution plan
2. Executor: Executes each step with JSON-only responses

Based on ChatGPT's NAT-friendly recommendations.
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class PlannerExecutorAgent:
    """
    Custom agent that implements the Planner → Executor pattern to eliminate ReAct drift.
    """
    
    def __init__(self, config_path: str):
        """Initialize the planner-executor agent."""
        # We'll implement this as a proof of concept
        # In a full implementation, this would integrate with NAT's agent framework
        self.config_path = Path(config_path)
        
    async def run_agent(self, user_request: str) -> str:
        """
        Main agent execution following ChatGPT's Option A pattern.
        
        Args:
            user_request: The user's multi-step request
            
        Returns:
            Final response after executing all planned steps
        """
        try:
            # Step 1: Create execution plan
            logger.info(f"🎯 Planning request: {user_request}")
            plan = await self._create_plan(user_request)
            logger.info(f"📋 Generated plan: {json.dumps(plan, indent=2)}")
            
            # Step 2: Execute plan step by step
            results = []
            for i, step in enumerate(plan["plan"], 1):
                remaining = len(plan["plan"]) - i + 1
                logger.info(f"⚡ Executing step {i}/{len(plan['plan'])}: {step['tool']}")
                
                result = await self._execute_step(
                    user_request=user_request,
                    plan=plan,
                    step_number=i,
                    remaining_steps=remaining,
                    current_step=step,
                    previous_results=results[-1] if results else None
                )
                
                results.append(result)
                logger.info(f"✅ Step {i} completed: {step['tool']}")
            
            # Step 3: Generate final response
            final_answer = await self._generate_final_response(
                user_request=user_request,
                plan=plan,
                results=results
            )
            
            logger.info(f"🎉 Agent completed successfully")
            return final_answer
            
        except Exception as e:
            logger.error(f"❌ Agent execution failed: {e}")
            return json.dumps({
                "success": False,
                "error": f"Agent execution failed: {str(e)}",
                "error_code": "AGENT_EXECUTION_ERROR"
            })
    
    async def _create_plan(self, user_request: str) -> Dict[str, Any]:
        """Create execution plan using planner prompt (JSON only)."""
        
        # Planner system prompt (from config)
        planner_prompt = """
        You will break the user request into an ordered plan of tool calls.
        
        Output ONLY valid JSON:
        { "plan": [ { "step": 1, "tool": "<tool_name>", "input": { /* json */ } }, ... ] }
        
        Rules:
        - Include every requested step in order
        - Use only available tools: [add_task, list_tasks, calculate_percentage]
        - No extra keys. No text outside JSON
        - For percentage calculations, use calculate_percentage with input: {"text": "X% of Y"}
        
        Example:
        {
          "plan": [
            {"step": 1, "tool": "add_task", "input": {"description": "Demo prep"}},
            {"step": 2, "tool": "list_tasks", "input": {}},
            {"step": 3, "tool": "calculate_percentage", "input": {"text": "25% of 200"}}
          ]
        }
        """
        
        # For demo purposes, let's simulate the planning step
        # In real implementation, this would call NAT's LLM
        
        # Parse the user request and create appropriate plan
        if "add" in user_request.lower() and "list" in user_request.lower() and "calculate" in user_request.lower():
            # Extract task name
            task_name = "Planner Test"
            if "'" in user_request:
                start = user_request.find("'") + 1
                end = user_request.find("'", start)
                if end > start:
                    task_name = user_request[start:end]
            
            # Extract percentage calculation
            percentage_text = "25% of 200"  # default
            if "%" in user_request:
                words = user_request.split()
                for i, word in enumerate(words):
                    if "%" in word and i < len(words) - 2:
                        if words[i+1].lower() == "of":
                            percentage_text = f"{word} of {words[i+2]}"
                            break
            
            plan = {
                "plan": [
                    {"step": 1, "tool": "add_task", "input": {"description": task_name}},
                    {"step": 2, "tool": "list_tasks", "input": {}},
                    {"step": 3, "tool": "calculate_percentage", "input": {"text": percentage_text}}
                ]
            }
        else:
            # Fallback plan
            plan = {
                "plan": [
                    {"step": 1, "tool": "current_time", "input": {}}
                ]
            }
        
        return plan
    
    async def _execute_step(
        self,
        user_request: str,
        plan: Dict[str, Any],
        step_number: int,
        remaining_steps: int,
        current_step: Dict[str, Any],
        previous_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute a single step using the tool system."""
        
        tool_name = current_step["tool"]
        tool_input = current_step["input"]
        
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
        
        # Parse the result to extract key information
        try:
            result_data = json.loads(result)
            return {
                "step": step_number,
                "tool": tool_name,
                "input": tool_input,
                "output": result_data,
                "success": result_data.get("success", False)
            }
        except json.JSONDecodeError:
            return {
                "step": step_number,
                "tool": tool_name,
                "input": tool_input,
                "output": {"raw_result": result},
                "success": False
            }
    
    async def _generate_final_response(
        self,
        user_request: str,
        plan: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> str:
        """Generate final response summarizing all executed steps."""
        
        success_count = sum(1 for r in results if r.get("success", False))
        total_steps = len(results)
        
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
            final_response = f"✅ Successfully completed all {total_steps} steps: {summary}."
        else:
            final_response = f"⚠️ Completed {success_count}/{total_steps} steps successfully."
        
        return final_response


# Demo function for testing
async def demo_planner_executor():
    """Demo the planner-executor agent with the original failing request."""
    
    agent = PlannerExecutorAgent("configs/config-planner-executor.yml")
    
    # Test the original 3-step request that caused ReAct drift
    test_request = "Add a task called 'Planner Success Test', then list all my tasks, and finally calculate 25% of 200"
    
    print("🚀 Testing Planner-Executor Agent (ChatGPT Option A)")
    print(f"📝 Request: {test_request}")
    print("=" * 60)
    
    result = await agent.run_agent(test_request)
    
    print("=" * 60)
    print(f"🎯 Final Result: {result}")
    print("🎉 Planner-Executor Demo Complete!")


if __name__ == "__main__":
    asyncio.run(demo_planner_executor())
