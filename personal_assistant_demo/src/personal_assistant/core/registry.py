"""
Tool Registry - Production metadata for tools with purity, schemas, and parallelism hints

Provides centralized tool metadata management including:
- Tool input/output schemas
- Purity levels (pure, read_only, impure)
- Parallelization safety hints
- Caching TTL policies
- Idempotency requirements
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Set, Optional
import time
import hashlib

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    Production tool registry with metadata for optimization and safety.
    """
    
    def __init__(self, registry_path: str):
        """
        Initialize tool registry from JSON file.
        
        Args:
            registry_path: Path to tool_registry.json file
        """
        self.registry_path = Path(registry_path)
        self.registry_data = self._load_registry()
        self.available_tools = set(self.registry_data.get("tools", {}).keys())
        
        # Caches for performance
        self._pure_cache = {}
        self._read_cache = {}
        self._idempotency_keys = set()
        
        logger.info(f"🔧 Tool registry loaded: {len(self.available_tools)} tools")
        
    def _load_registry(self) -> Dict[str, Any]:
        """Load and validate tool registry from JSON file."""
        try:
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
            
            # Basic validation
            if "tools" not in data:
                raise ValueError("Registry must contain 'tools' key")
                
            if "registry_version" not in data:
                logger.warning("Registry missing version - consider adding for cache invalidation")
                
            return data
            
        except Exception as e:
            logger.error(f"Failed to load tool registry from {self.registry_path}: {e}")
            raise
    
    def get_tool_metadata(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get complete metadata for a tool."""
        return self.registry_data.get("tools", {}).get(tool_name)
    
    def get_tool_purity(self, tool_name: str) -> str:
        """Get tool purity level (pure, read_only, impure)."""
        metadata = self.get_tool_metadata(tool_name)
        return metadata.get("purity", "impure") if metadata else "impure"
    
    def is_tool_parallel_safe(self, tool_name: str) -> bool:
        """Check if tool can be executed in parallel."""
        metadata = self.get_tool_metadata(tool_name)
        return metadata.get("parallel_safe", False) if metadata else False
    
    def requires_idempotency_key(self, tool_name: str) -> bool:
        """Check if tool requires idempotency key for safe retries."""
        metadata = self.get_tool_metadata(tool_name)
        return metadata.get("requires_idempotency_key", False) if metadata else False
    
    def get_cache_ttl(self, tool_name: str) -> int:
        """Get cache TTL in seconds for tool results."""
        metadata = self.get_tool_metadata(tool_name)
        return metadata.get("cache_ttl_s", 0) if metadata else 0
    
    def validate_tool_input(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        """Validate tool input against its schema."""
        metadata = self.get_tool_metadata(tool_name)
        if not metadata or "input_schema" not in metadata:
            logger.warning(f"No input schema for tool {tool_name}")
            return True  # Allow if no schema defined
            
        try:
            import jsonschema
            jsonschema.validate(tool_input, metadata["input_schema"])
            return True
        except Exception as e:
            logger.error(f"Tool input validation failed for {tool_name}: {e}")
            return False
    
    def get_cached_result(self, tool_name: str, tool_input: Dict[str, Any]) -> Optional[str]:
        """Get cached result for pure/read_only tools."""
        purity = self.get_tool_purity(tool_name)
        cache_key = self._create_cache_key(tool_name, tool_input)
        
        if purity == "pure":
            return self._pure_cache.get(cache_key)
        elif purity == "read_only":
            cached_entry = self._read_cache.get(cache_key)
            if cached_entry and time.time() - cached_entry["timestamp"] < self.get_cache_ttl(tool_name):
                return cached_entry["result"]
        
        return None
    
    def cache_result(self, tool_name: str, tool_input: Dict[str, Any], result: str) -> None:
        """Cache result for future use."""
        purity = self.get_tool_purity(tool_name)
        cache_key = self._create_cache_key(tool_name, tool_input)
        
        if purity == "pure":
            self._pure_cache[cache_key] = result
        elif purity == "read_only":
            self._read_cache[cache_key] = {
                "result": result,
                "timestamp": time.time()
            }
    
    def generate_idempotency_key(self, user_request: str, step_number: int, 
                                tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Generate unique idempotency key for impure operations."""
        content = f"{user_request}:{step_number}:{tool_name}:{json.dumps(tool_input, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def is_duplicate_operation(self, idempotency_key: str) -> bool:
        """Check if operation has already been completed."""
        return idempotency_key in self._idempotency_keys
    
    def mark_operation_complete(self, idempotency_key: str) -> None:
        """Mark idempotent operation as completed."""
        self._idempotency_keys.add(idempotency_key)
    
    def get_parallel_execution_groups(self, plan: Dict[str, Any]) -> List[List[Dict[str, Any]]]:
        """Analyze plan for parallel execution opportunities."""
        # Simple grouping by dependencies - could be enhanced with DAG analysis
        groups = []
        remaining_steps = list(plan.get("plan", []))
        
        while remaining_steps:
            # Find steps with no dependencies or all dependencies satisfied
            current_group = []
            completed_ids = set()
            
            for step in remaining_steps[:]:
                dependencies = step.get("after", [])
                if not dependencies or all(dep in completed_ids for dep in dependencies):
                    if self.is_tool_parallel_safe(step["tool"]):
                        current_group.append(step)
                        remaining_steps.remove(step)
                        completed_ids.add(step["id"])
            
            if current_group:
                groups.append(current_group)
            elif remaining_steps:
                # Take first remaining step to avoid infinite loop
                step = remaining_steps.pop(0)
                groups.append([step])
                completed_ids.add(step["id"])
        
        return groups
    
    def normalize_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Apply quick-win normalization rules to plan."""
        # Implement ChatGPT's quick win rules here
        normalized = plan.copy()
        # For now, return as-is - this could be expanded with specific rules
        return normalized
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """Get cache and registry statistics."""
        return {
            "pure_cache_entries": len(self._pure_cache),
            "read_cache_entries": len(self._read_cache),
            "total_tools": len(self.available_tools),
            "idempotency_keys": len(self._idempotency_keys)
        }
    
    def _create_cache_key(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Create cache key for tool call."""
        content = f"{tool_name}:{json.dumps(tool_input, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
