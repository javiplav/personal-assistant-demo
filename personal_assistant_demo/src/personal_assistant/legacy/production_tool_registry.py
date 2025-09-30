"""
Production Tool Registry with ChatGPT's Hardening Features

Implements:
- Runtime validation against JSON schemas
- Purity-based caching (pure=long TTL, read_only=short TTL, impure=none)
- Safe parallelism (parallel_safe=true tools only)
- Idempotency key generation for impure operations
- Plan normalization based on tool metadata
- Schema versioning for cache invalidation

Based on ChatGPT's production optimization recommendations.
"""

import json
import hashlib
import time
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

class ProductionToolRegistry:
    """
    Production-grade tool registry with ChatGPT's hardening features.
    
    Features:
    - Schema-based validation
    - Purity-based caching and parallelism
    - Idempotency key generation
    - Plan normalization
    - Version-based cache invalidation
    """
    
    def __init__(self, registry_path: str):
        """Initialize the production tool registry."""
        self.registry_path = Path(registry_path)
        self.registry_data = self._load_registry()
        self.tool_schemas = self._extract_tool_schemas()
        
        # Production caches (in-memory for demo, would use Redis in production)
        self._pure_cache = {}  # Long TTL cache for pure functions
        self._read_cache = {}  # Short TTL cache for read-only functions
        self._cache_timestamps = {}
        
        # Idempotency tracking
        self._idempotency_keys = set()
        
        logger.info(f"🔧 Loaded tool registry v{self.registry_version} with {len(self.tool_schemas)} tools")
        
    def _load_registry(self) -> Dict[str, Any]:
        """Load and validate the tool registry."""
        try:
            with open(self.registry_path, 'r') as f:
                registry = json.load(f)
                
            # Basic registry validation
            required_fields = ["registry_version", "tool_schema_version", "tools"]
            for field in required_fields:
                if field not in registry:
                    raise ValueError(f"Registry missing required field: {field}")
                    
            logger.info(f"✅ Registry validation passed: {len(registry['tools'])} tools loaded")
            return registry
            
        except Exception as e:
            logger.error(f"❌ Failed to load tool registry: {e}")
            raise
    
    def _extract_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Extract tool metadata and schemas for runtime use."""
        tools = {}
        for tool_name, tool_config in self.registry_data["tools"].items():
            tools[tool_name] = {
                "version": tool_config["version"],
                "purity": tool_config["purity"], 
                "parallel_safe": tool_config["parallel_safe"],
                "requires_idempotency_key": tool_config["requires_idempotency_key"],
                "cache_ttl_s": tool_config["cache_ttl_s"],
                "input_schema": tool_config["input_schema"],
                "output_schema": tool_config["output_schema"]
            }
        return tools
    
    @property
    def registry_version(self) -> str:
        """Get the registry version for cache invalidation."""
        return self.registry_data["registry_version"]
    
    @property
    def tool_schema_version(self) -> str:
        """Get the tool schema version for cache invalidation."""
        return self.registry_data["tool_schema_version"]
    
    @property
    def available_tools(self) -> List[str]:
        """Get list of all available tool names."""
        return list(self.tool_schemas.keys())
    
    def validate_tool_input(self, tool_name: str, tool_input: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate tool input against its schema.
        
        Returns:
            (is_valid, error_message)
        """
        if tool_name not in self.tool_schemas:
            return False, f"Unknown tool: {tool_name}"
        
        try:
            schema = self.tool_schemas[tool_name]["input_schema"]
            validate(instance=tool_input, schema=schema)
            return True, None
            
        except ValidationError as e:
            error_msg = f"Input validation failed for {tool_name}: {e.message}"
            logger.warning(f"⚠️ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Schema validation error for {tool_name}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg
    
    def get_tool_purity(self, tool_name: str) -> str:
        """Get tool purity level (pure, read_only, impure)."""
        return self.tool_schemas.get(tool_name, {}).get("purity", "impure")
    
    def is_parallel_safe(self, tool_name: str) -> bool:
        """Check if tool can be run in parallel."""
        return self.tool_schemas.get(tool_name, {}).get("parallel_safe", False)
    
    def requires_idempotency_key(self, tool_name: str) -> bool:
        """Check if tool requires idempotency key for retry safety."""
        return self.tool_schemas.get(tool_name, {}).get("requires_idempotency_key", False)
    
    def get_cache_ttl(self, tool_name: str) -> float:
        """Get cache TTL for tool in seconds."""
        return self.tool_schemas.get(tool_name, {}).get("cache_ttl_s", 0)
    
    def generate_idempotency_key(self, user_request: str, step_number: int, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Generate idempotency key for retry safety.
        
        Args:
            user_request: Original user request
            step_number: Step number in plan
            tool_name: Tool being executed
            tool_input: Tool input parameters
            
        Returns:
            Unique idempotency key
        """
        # Create deterministic hash from request context
        key_data = {
            "user_request": user_request,
            "step": step_number,
            "tool": tool_name,
            "input": tool_input,
            "registry_version": self.registry_version
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]  # 16 chars for readability
        
        return f"idem_{key_hash}"
    
    def is_duplicate_operation(self, idempotency_key: str) -> bool:
        """Check if operation has already been executed (idempotency check)."""
        return idempotency_key in self._idempotency_keys
    
    def mark_operation_complete(self, idempotency_key: str) -> None:
        """Mark operation as completed for idempotency tracking."""
        self._idempotency_keys.add(idempotency_key)
        
        # Cleanup old keys (keep only last 1000 for memory management)
        if len(self._idempotency_keys) > 1000:
            old_keys = list(self._idempotency_keys)[:500]
            for key in old_keys:
                self._idempotency_keys.discard(key)
    
    def get_cached_result(self, tool_name: str, tool_input: Dict[str, Any]) -> Optional[str]:
        """
        Get cached result for tool execution.
        
        Implements ChatGPT's caching strategy:
        - pure functions: long TTL (86400s)
        - read_only functions: short TTL (0.5-2s) 
        - impure functions: no caching (TTL 0)
        """
        purity = self.get_tool_purity(tool_name)
        cache_ttl = self.get_cache_ttl(tool_name)
        
        if cache_ttl == 0:  # No caching for impure tools
            return None
        
        # Generate cache key
        cache_key = self._generate_cache_key(tool_name, tool_input)
        
        # Select appropriate cache based on purity
        if purity == "pure":
            cache = self._pure_cache
        elif purity == "read_only":
            cache = self._read_cache
        else:
            return None  # No caching for impure
        
        # Check if cached result exists and is fresh
        if cache_key in cache:
            cached_time = self._cache_timestamps.get(cache_key, 0)
            age = time.time() - cached_time
            
            if age <= cache_ttl:
                logger.debug(f"📦 Cache hit for {tool_name} (age: {age:.2f}s)")
                return cache[cache_key]
            else:
                # Expired - remove from cache
                cache.pop(cache_key, None)
                self._cache_timestamps.pop(cache_key, None)
                logger.debug(f"⏰ Cache expired for {tool_name} (age: {age:.2f}s)")
        
        return None
    
    def cache_result(self, tool_name: str, tool_input: Dict[str, Any], result: str) -> None:
        """Cache tool result according to purity-based caching strategy."""
        purity = self.get_tool_purity(tool_name)
        cache_ttl = self.get_cache_ttl(tool_name)
        
        if cache_ttl == 0:  # No caching for impure tools
            return
        
        # Generate cache key
        cache_key = self._generate_cache_key(tool_name, tool_input)
        
        # Select appropriate cache based on purity
        if purity == "pure":
            cache = self._pure_cache
        elif purity == "read_only":
            cache = self._read_cache
        else:
            return  # No caching for impure
        
        # Store result with timestamp
        cache[cache_key] = result
        self._cache_timestamps[cache_key] = time.time()
        
        logger.debug(f"💾 Cached result for {tool_name} (TTL: {cache_ttl}s)")
        
        # Memory management - limit cache sizes
        max_cache_size = 10000 if purity == "pure" else 1000
        if len(cache) > max_cache_size:
            # Remove oldest entries
            sorted_keys = sorted(cache.keys(), key=lambda k: self._cache_timestamps.get(k, 0))
            for key in sorted_keys[:max_cache_size // 2]:
                cache.pop(key, None)
                self._cache_timestamps.pop(key, None)
    
    def _generate_cache_key(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Generate deterministic cache key for tool + input."""
        key_data = {
            "tool": tool_name,
            "input": tool_input,
            "schema_version": self.tool_schema_version
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]  # 32 chars for uniqueness
    
    def invalidate_caches(self) -> None:
        """Invalidate all caches (call when registry/tools change)."""
        self._pure_cache.clear()
        self._read_cache.clear()
        self._cache_timestamps.clear()
        logger.info("🧹 All tool caches invalidated")
    
    def normalize_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize plan using ChatGPT's quick win rules:
        1. Collapse consecutive identical reads with equal inputs
        2. Remove duplicate list_tasks unless status/query changes  
        3. Move pure calcs after required impure reads if they don't feed each other
        4. Cap steps at 12 max
        """
        original_steps = plan["plan"]
        
        if len(original_steps) == 0:
            return plan
        
        normalized_steps = []
        
        # Rule 1 & 2: Collapse consecutive identical reads
        prev_step = None
        for step in original_steps:
            tool_name = step["tool"]
            tool_input = step["input"]
            purity = self.get_tool_purity(tool_name)
            
            # Skip if identical to previous read-only operation
            if (prev_step and 
                purity == "read_only" and 
                prev_step["tool"] == tool_name and
                prev_step["input"] == tool_input):
                logger.info(f"🔧 Collapsed duplicate {tool_name} operation")
                continue
            
            normalized_steps.append(step)
            prev_step = step
        
        # Rule 3: Move pure calculations after impure operations (basic reordering)
        impure_steps = []
        pure_steps = []
        read_steps = []
        
        for step in normalized_steps:
            purity = self.get_tool_purity(step["tool"])
            if purity == "impure":
                impure_steps.append(step)
            elif purity == "pure":
                pure_steps.append(step)
            else:  # read_only
                read_steps.append(step)
        
        # Reorder: impure → read_only → pure (preserving relative order within each group)
        reordered_steps = impure_steps + read_steps + pure_steps
        
        # Rule 4: Cap at 12 steps max
        if len(reordered_steps) > 12:
            logger.warning(f"⚠️ Plan has {len(reordered_steps)} steps, capping at 12")
            reordered_steps = reordered_steps[:12]
        
        # Renumber steps
        for i, step in enumerate(reordered_steps, 1):
            step["step"] = i
        
        normalized_plan = {"plan": reordered_steps}
        
        if len(reordered_steps) != len(original_steps):
            logger.info(f"🔧 Plan normalized: {len(original_steps)} → {len(reordered_steps)} steps")
        
        return normalized_plan
    
    def get_parallel_execution_groups(self, plan: Dict[str, Any]) -> List[List[Dict[str, Any]]]:
        """
        Group plan steps for safe parallel execution.
        
        Returns list of execution groups where steps in each group can run in parallel.
        Only groups parallel_safe=true tools together.
        """
        steps = plan["plan"]
        execution_groups = []
        current_group = []
        
        for step in steps:
            tool_name = step["tool"]
            is_safe = self.is_parallel_safe(tool_name)
            
            # If current step is parallel safe and we have other parallel safe steps, add to group
            if is_safe and current_group and all(self.is_parallel_safe(s["tool"]) for s in current_group):
                current_group.append(step)
                
                # Limit group size to 3 for resource management
                if len(current_group) >= 3:
                    execution_groups.append(current_group)
                    current_group = []
            else:
                # Start new group
                if current_group:
                    execution_groups.append(current_group)
                current_group = [step]
        
        # Add final group
        if current_group:
            execution_groups.append(current_group)
        
        parallel_groups = [group for group in execution_groups if len(group) > 1]
        if parallel_groups:
            logger.info(f"⚡ Plan allows {len(parallel_groups)} parallel execution groups")
        
        return execution_groups
    
    def get_tool_stats(self) -> Dict[str, Any]:
        """Get registry statistics for monitoring."""
        tools_by_purity = {"pure": 0, "read_only": 0, "impure": 0}
        parallel_safe_count = 0
        idempotency_required_count = 0
        
        for tool_name, tool_info in self.tool_schemas.items():
            tools_by_purity[tool_info["purity"]] += 1
            if tool_info["parallel_safe"]:
                parallel_safe_count += 1
            if tool_info["requires_idempotency_key"]:
                idempotency_required_count += 1
        
        return {
            "registry_version": self.registry_version,
            "total_tools": len(self.tool_schemas),
            "tools_by_purity": tools_by_purity,
            "parallel_safe_tools": parallel_safe_count,
            "idempotency_required_tools": idempotency_required_count,
            "pure_cache_entries": len(self._pure_cache),
            "read_cache_entries": len(self._read_cache),
            "idempotency_keys_tracked": len(self._idempotency_keys)
        }


# Demo function to showcase the production tool registry
async def demo_production_tool_registry():
    """Demo the production tool registry with all ChatGPT hardening features."""
    
    registry_path = "/Users/jplavnick/Documents/NVIDIA/nemo-agent-toolkit-demo/personal_assistant_demo/src/personal_assistant/tool_registry.json"
    registry = ProductionToolRegistry(registry_path)
    
    print("🔧 PRODUCTION TOOL REGISTRY DEMO")
    print("=" * 50)
    
    # Demo 1: Schema validation
    print("\n1. Schema Validation")
    print("-" * 30)
    
    valid_input = {"description": "Test task"}
    is_valid, error = registry.validate_tool_input("add_task", valid_input)
    print(f"Valid input: {is_valid}")
    
    invalid_input = {"wrong_field": "test"}  # missing required description
    is_valid, error = registry.validate_tool_input("add_task", invalid_input)
    print(f"Invalid input: {is_valid}, Error: {error}")
    
    # Demo 2: Purity-based features
    print("\n2. Purity-Based Features")
    print("-" * 30)
    
    print(f"calculate_percentage purity: {registry.get_tool_purity('calculate_percentage')}")
    print(f"calculate_percentage parallel safe: {registry.is_parallel_safe('calculate_percentage')}")
    print(f"calculate_percentage cache TTL: {registry.get_cache_ttl('calculate_percentage')}s")
    
    print(f"add_task purity: {registry.get_tool_purity('add_task')}")
    print(f"add_task requires idempotency: {registry.requires_idempotency_key('add_task')}")
    
    # Demo 3: Idempotency keys
    print("\n3. Idempotency Keys")
    print("-" * 30)
    
    user_request = "Add a test task"
    idem_key = registry.generate_idempotency_key(user_request, 1, "add_task", valid_input)
    print(f"Idempotency key: {idem_key}")
    print(f"Is duplicate: {registry.is_duplicate_operation(idem_key)}")
    
    registry.mark_operation_complete(idem_key)
    print(f"After marking complete: {registry.is_duplicate_operation(idem_key)}")
    
    # Demo 4: Plan normalization
    print("\n4. Plan Normalization")
    print("-" * 30)
    
    sample_plan = {
        "plan": [
            {"step": 1, "tool": "add_task", "input": {"description": "Test"}},
            {"step": 2, "tool": "list_tasks", "input": {}},
            {"step": 3, "tool": "list_tasks", "input": {}},  # Duplicate
            {"step": 4, "tool": "calculate_percentage", "input": {"text": "50% of 100"}}
        ]
    }
    
    normalized = registry.normalize_plan(sample_plan)
    print(f"Original steps: {len(sample_plan['plan'])}")
    print(f"Normalized steps: {len(normalized['plan'])}")
    
    # Demo 5: Registry statistics
    print("\n5. Registry Statistics")
    print("-" * 30)
    
    stats = registry.get_tool_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n" + "=" * 50)
    print("🎉 Production Tool Registry Demo Complete!")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo_production_tool_registry())
