"""
DAG Parallel Execution Controller

Implements ChatGPT's parallel ready queue algorithm with:
- Topological sorting and cycle detection
- Safe parallel execution (parallel_safe tools only)
- Deterministic tie-breaking
- Failure propagation
- Concurrency limiting

Based on ChatGPT's controller pseudocode specifications.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from queue import PriorityQueue
from dataclasses import dataclass
from .validator import validate_plan, ValidationResult

logger = logging.getLogger(__name__)

@dataclass
class DAGNode:
    """DAG node representing a plan step."""
    id: str
    step: int
    tool: str
    input: Dict[str, Any]
    after: List[str]
    
    # Execution state
    status: str = "pending"  # pending, ready, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None

class DAGParallelController:
    """
    ChatGPT's DAG parallel execution controller with production features.
    
    Implements:
    - Topological sorting with cycle detection
    - Ready queue with deterministic ordering
    - Safe parallelism (parallel_safe tools only)
    - Concurrency limiting (CONCURRENCY_MAX=3)
    - Failure propagation
    """
    
    def __init__(self, tool_registry, concurrency_max: int = 3):
        """Initialize DAG controller."""
        self.tool_registry = tool_registry
        self.concurrency_max = concurrency_max
        self.nodes: Dict[str, DAGNode] = {}
        self.ready_queue = PriorityQueue()  # (priority, node_id, node)
        self.inflight: Dict[str, asyncio.Task] = {}
        self.completed: Set[str] = set()
        self.failed = False
        
    def load_plan(self, plan: Dict[str, Any]) -> None:
        """Load plan into DAG nodes with ChatGPT's bulletproof validation."""
        
        self.nodes.clear()
        self.ready_queue = PriorityQueue()
        self.inflight.clear()
        self.completed.clear()
        self.failed = False
        
        # Use ChatGPT's validator as front gate
        registry_data = self.tool_registry.registry_data
        validation_result = validate_plan(plan, registry_data)
        
        if not validation_result.valid:
            error_msg = f"Plan validation failed: {validation_result.errors}"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        logger.info("✅ Plan passed ChatGPT's front-gate validation")
        
        # Use normalized plan from validator
        normalized_plan = validation_result.normalized_plan
        topo_order = validation_result.topo_order_ids
        
        logger.info(f"🔧 Plan normalized with topo order: {topo_order}")
        
        # Create nodes from validated and normalized plan
        for step_data in normalized_plan["plan"]:
            node = DAGNode(
                id=step_data["id"],
                step=step_data["step"],
                tool=step_data["tool"],
                input=step_data["input"],
                after=step_data.get("after", [])
            )
            self.nodes[node.id] = node
        
        # Seed ready queue with nodes that have no dependencies
        self._update_ready_queue()
        
        logger.info(f"🔧 DAG loaded: {len(self.nodes)} nodes, {self.ready_queue.qsize()} ready")
    
    def _deps_satisfied(self, node: DAGNode) -> bool:
        """Check if all dependencies for a node are completed."""
        return all(dep in self.completed for dep in node.after)
    
    def _update_ready_queue(self) -> None:
        """Update ready queue with nodes whose dependencies are satisfied."""
        
        for node in self.nodes.values():
            if (node.status == "pending" and 
                node.id not in self.inflight and
                self._deps_satisfied(node)):
                
                # Deterministic tie-breaking: (min_step, tool_name, id)
                priority = (node.step, node.tool, node.id)
                self.ready_queue.put((priority, node.id, node))
                node.status = "ready"
        
        logger.debug(f"🔄 Ready queue updated: {self.ready_queue.qsize()} nodes ready")
    
    def _get_parallel_batch(self) -> List[DAGNode]:
        """Get batch of nodes for parallel execution following ChatGPT's rules."""
        
        batch = []
        
        # Fill up to CONCURRENCY_MAX with parallel_safe nodes
        while (len(self.inflight) + len(batch) < self.concurrency_max and 
               not self.ready_queue.empty()):
            
            _, node_id, node = self.ready_queue.get()
            
            if self.tool_registry.is_parallel_safe(node.tool):
                batch.append(node)
            else:
                # Impure/non-parallel-safe node
                if not self.inflight and not batch:
                    # Run impure node alone if nothing is running
                    batch.append(node)
                    break
                else:
                    # Requeue impure node until inflight clears
                    priority = (node.step, node.tool, node.id)
                    self.ready_queue.put((priority, node_id, node))
                    break
        
        return batch
    
    async def _execute_node(self, node: DAGNode, user_request: str) -> Dict[str, Any]:
        """Execute a single DAG node."""
        
        node.status = "running"
        node.start_time = time.time()
        
        try:
            logger.info(f"⚡ Executing DAG node {node.id}: {node.tool}")
            
            # Import and execute the tool (same logic as before)
            tool_name = node.tool
            tool_input = node.input
            
            # Use the enhanced step execution with all production features
            if tool_name == "add_task":
                from personal_assistant.tools.tasks import add_task
                result = await add_task(**tool_input)
                
            elif tool_name == "list_tasks":
                from personal_assistant.tools.tasks import list_tasks
                result = await list_tasks(**tool_input)
                
            elif tool_name == "calculate_percentage":
                from personal_assistant.tools.calculator import calculate_percentage
                result = await calculate_percentage(**tool_input)
                
            elif tool_name == "get_current_time":
                from personal_assistant.tools.datetime_info import get_current_time
                result = await get_current_time(**tool_input)
                
            else:
                result = json.dumps({
                    "success": False,
                    "error": f"Unknown tool: {tool_name}",
                    "error_code": "UNKNOWN_TOOL"
                })
            
            node.end_time = time.time()
            execution_time = node.end_time - node.start_time
            
            # Parse and validate result
            result_data = json.loads(result)
            success = result_data.get("success", True) or ("error" not in result_data)
            
            node.result = {
                "tool": tool_name,
                "input": tool_input,
                "output": result_data,
                "success": success,
                "execution_time": execution_time
            }
            
            if success:
                node.status = "completed"
                logger.info(f"✅ DAG node {node.id} completed in {execution_time:.3f}s")
            else:
                node.status = "failed"
                logger.error(f"❌ DAG node {node.id} failed: {result_data.get('error', 'Unknown error')}")
            
            return node.result
            
        except Exception as e:
            node.end_time = time.time()
            node.status = "failed"
            node.result = {
                "tool": node.tool,
                "input": node.input,
                "output": {"error": str(e)},
                "success": False,
                "execution_time": node.end_time - node.start_time if node.start_time else 0
            }
            
            logger.error(f"❌ DAG node {node.id} exception: {e}")
            return node.result
    
    async def execute_plan(self, user_request: str, deadline_ms: int = 20000) -> Dict[str, Any]:
        """
        Execute DAG plan with parallel execution following ChatGPT's algorithm.
        
        Returns execution results and metrics.
        """
        
        start_time = time.time()
        deadline = start_time + (deadline_ms / 1000.0)
        results = []
        
        logger.info(f"🚀 Starting DAG execution with {len(self.nodes)} nodes")
        
        # Main execution loop following ChatGPT's pseudocode
        while not self.ready_queue.empty() and not self.failed and time.time() < deadline:
            
            # Get parallel batch
            batch = self._get_parallel_batch()
            
            if not batch:
                # No ready nodes and nothing inflight - check if we're done
                if not self.inflight:
                    break
                
                # Wait a bit for inflight to complete
                await asyncio.sleep(0.01)
                continue
            
            # Launch batch in parallel
            for node in batch:
                task = asyncio.create_task(self._execute_node(node, user_request))
                self.inflight[node.id] = task
            
            logger.info(f"⚡ Launched batch of {len(batch)} nodes (total inflight: {len(self.inflight)})")
            
            # Wait for any completion
            if self.inflight:
                done_tasks, pending_tasks = await asyncio.wait(
                    list(self.inflight.values()),
                    timeout=min(5.0, deadline - time.time()),
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed nodes
                for task in done_tasks:
                    node_id = None
                    for nid, t in self.inflight.items():
                        if t == task:
                            node_id = nid
                            break
                    
                    if node_id:
                        del self.inflight[node_id]
                        node = self.nodes[node_id]
                        
                        try:
                            result = await task
                            results.append(result)
                            
                            if result["success"]:
                                self.completed.add(node_id)
                                # Update ready queue with newly satisfied dependencies
                                self._update_ready_queue()
                            else:
                                # Failure propagation
                                self.failed = True
                                logger.error(f"💥 Node {node_id} failed - cancelling remaining tasks")
                                
                                # Cancel all inflight tasks
                                for remaining_task in self.inflight.values():
                                    remaining_task.cancel()
                                break
                                
                        except Exception as e:
                            logger.error(f"❌ Task execution error for {node_id}: {e}")
                            self.failed = True
                            break
        
        # Handle completion
        total_time = time.time() - start_time
        
        if time.time() >= deadline:
            logger.warning(f"⏰ DAG execution hit deadline ({deadline_ms}ms)")
            status = "timeout"
        elif self.failed:
            logger.error(f"💥 DAG execution failed")
            status = "failed"
        elif len(self.completed) == len(self.nodes):
            logger.info(f"🎉 DAG execution completed successfully")
            status = "completed"
        else:
            logger.warning(f"⚠️ DAG execution incomplete")
            status = "incomplete"
        
        # Calculate metrics
        parallel_steps = len([r for r in results if len(batch) > 1])
        cache_hits = len([r for r in results if r.get("cache_hit", False)])
        
        execution_summary = {
            "status": status,
            "total_time_s": total_time,
            "nodes_completed": len(self.completed),
            "nodes_total": len(self.nodes),
            "parallel_steps": parallel_steps,
            "cache_hits": cache_hits,
            "results": results
        }
        
        logger.info(f"📊 DAG execution summary: {status}, {len(self.completed)}/{len(self.nodes)} nodes, {total_time:.3f}s")
        
        return execution_summary


# Demo function to showcase DAG parallel execution
async def demo_dag_parallel_execution():
    """Demo the DAG parallel controller with ChatGPT's features."""
    
    from production_tool_registry import ProductionToolRegistry
    
    print("⚡ DAG PARALLEL EXECUTION DEMO")
    print("=" * 50)
    
    # Initialize tool registry and controller
    registry_path = "/Users/jplavnick/Documents/NVIDIA/nemo-agent-toolkit-demo/personal_assistant_demo/src/personal_assistant/tool_registry.json"
    tool_registry = ProductionToolRegistry(registry_path)
    
    controller = DAGParallelController(tool_registry, concurrency_max=3)
    
    # Create sample DAG plan
    sample_plan = {
        "plan": [
            {
                "id": "task_add",
                "step": 1,
                "tool": "add_task",
                "input": {"description": "DAG Demo Task"},
                "after": []
            },
            {
                "id": "calc_1",
                "step": 2,
                "tool": "calculate_percentage",
                "input": {"text": "25% of 100"},
                "after": []  # Pure function, can run in parallel
            },
            {
                "id": "calc_2", 
                "step": 3,
                "tool": "calculate_percentage",
                "input": {"text": "50% of 200"},
                "after": []  # Pure function, can run in parallel
            },
            {
                "id": "list_tasks",
                "step": 4,
                "tool": "list_tasks",
                "input": {},
                "after": ["task_add"]  # Depends on task creation
            }
        ]
    }
    
    print("📋 Sample DAG Plan:")
    print(json.dumps(sample_plan, indent=2))
    
    # Load and execute plan
    controller.load_plan(sample_plan)
    
    print("\n🚀 Executing DAG plan with parallelism...")
    
    user_request = "Add task, calculate percentages, and list tasks"
    results = await controller.execute_plan(user_request, deadline_ms=10000)
    
    print("\n📊 Execution Results:")
    print(f"Status: {results['status']}")
    print(f"Total time: {results['total_time_s']:.3f}s")
    print(f"Nodes completed: {results['nodes_completed']}/{results['nodes_total']}")
    print(f"Parallel steps: {results['parallel_steps']}")
    print(f"Cache hits: {results['cache_hits']}")
    
    print("\n✅ DAG Parallel Execution Demo Complete!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo_dag_parallel_execution())
