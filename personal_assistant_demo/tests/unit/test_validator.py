"""
Test ChatGPT's Agent Validator Module

Tests all validation scenarios including:
- Valid DAG plans
- Invalid schemas  
- Cycle detection
- Readiness checking
- Tool input validation
"""

import json
import asyncio
from pathlib import Path
from personal_assistant.core.validator import validate_plan, validate_executor_step, ValidationResult

def load_tool_registry():
    """Load our tool registry for testing."""
    registry_path = Path(__file__).parent / "tool_registry.json"
    with open(registry_path, 'r') as f:
        return json.load(f)

def test_valid_dag_plan():
    """Test 1: Valid DAG plan with dependencies."""
    print("🧪 TEST 1: Valid DAG Plan")
    
    registry = load_tool_registry()
    
    valid_plan = {
        "plan": [
            {"id": "task_add", "step": 1, "tool": "add_task", "input": {"description": "Test"}, "after": []},
            {"id": "calc_pure", "step": 2, "tool": "calculate_percentage", "input": {"text": "25% of 100"}, "after": []},
            {"id": "task_list", "step": 3, "tool": "list_tasks", "input": {}, "after": ["task_add"]}
        ]
    }
    
    result = validate_plan(valid_plan, registry)
    
    print(f"   Valid: {result.valid}")
    print(f"   Errors: {result.errors}")
    print(f"   Topo Order: {result.topo_order_ids}")
    
    assert result.valid, f"Should be valid: {result.errors}"
    assert len(result.normalized_plan["plan"]) == 3
    print("   ✅ PASSED")

def test_cycle_detection():
    """Test 2: Cycle detection."""
    print("\n🧪 TEST 2: Cycle Detection")
    
    registry = load_tool_registry()
    
    cyclic_plan = {
        "plan": [
            {"id": "s1", "step": 1, "tool": "add_task", "input": {"description": "Test"}, "after": ["s2"]},
            {"id": "s2", "step": 2, "tool": "calculate_percentage", "input": {"text": "25% of 100"}, "after": ["s1"]}
        ]
    }
    
    result = validate_plan(cyclic_plan, registry)
    
    print(f"   Valid: {result.valid}")
    print(f"   Errors: {result.errors}")
    
    assert not result.valid, "Should detect cycle"
    assert any("E_CYCLE" in error for error in result.errors)
    print("   ✅ PASSED - Cycle detected correctly")

def test_schema_violations():
    """Test 3: Schema violations."""
    print("\n🧪 TEST 3: Schema Violations")
    
    registry = load_tool_registry()
    
    # Invalid tool name
    invalid_plan = {
        "plan": [
            {"id": "s1", "step": 1, "tool": "nonexistent_tool", "input": {}, "after": []}
        ]
    }
    
    result = validate_plan(invalid_plan, registry)
    
    print(f"   Valid: {result.valid}")
    print(f"   Errors: {result.errors}")
    
    assert not result.valid, "Should catch unknown tool"
    # Schema validation catches unknown tools at JSON schema level (E_SCHEMA) which is correct
    assert any("E_SCHEMA" in error for error in result.errors)
    print("   ✅ PASSED - Unknown tool detected at schema level")

def test_executor_validation():
    """Test 4: Executor step validation."""
    print("\n🧪 TEST 4: Executor Step Validation")
    
    registry = load_tool_registry()
    
    # Valid plan state
    current_plan = {
        "plan": [
            {"id": "s1", "step": 1, "tool": "add_task", "input": {"description": "Test"}, "after": []},
            {"id": "s2", "step": 2, "tool": "list_tasks", "input": {}, "after": ["s1"]}
        ],
        "completed_ids": [],
        "executing_ids": []
    }
    
    # Valid executor step (s1 is ready)
    executor_step = {
        "next_step": 1,
        "remaining_steps": 2,
        "type": "tool_call",
        "tool": "add_task",
        "input": {"description": "Test"}
    }
    
    result = validate_executor_step(executor_step, current_plan, registry)
    
    print(f"   Valid: {result.valid}")
    print(f"   Errors: {result.errors}")
    
    assert result.valid, f"Should be valid: {result.errors}"
    print("   ✅ PASSED")

def test_readiness_checking():
    """Test 5: Readiness checking."""
    print("\n🧪 TEST 5: Readiness Checking")
    
    registry = load_tool_registry()
    
    current_plan = {
        "plan": [
            {"id": "s1", "step": 1, "tool": "add_task", "input": {"description": "Test"}, "after": []},
            {"id": "s2", "step": 2, "tool": "list_tasks", "input": {}, "after": ["s1"]}
        ],
        "completed_ids": [],  # s1 not completed yet
        "executing_ids": []
    }
    
    # Try to execute s2 before s1 is done
    executor_step = {
        "next_step": 2,
        "remaining_steps": 1,
        "type": "tool_call", 
        "tool": "list_tasks",
        "input": {}
    }
    
    result = validate_executor_step(executor_step, current_plan, registry)
    
    print(f"   Valid: {result.valid}")
    print(f"   Errors: {result.errors}")
    
    assert not result.valid, "Should detect dependency not satisfied"
    assert any("E_READINESS" in error for error in result.errors)
    print("   ✅ PASSED - Dependency checking works")

def test_input_schema_validation():
    """Test 6: Tool input schema validation."""
    print("\n🧪 TEST 6: Tool Input Schema Validation")
    
    registry = load_tool_registry()
    
    current_plan = {
        "plan": [
            {"id": "s1", "step": 1, "tool": "add_task", "input": {"description": "Test"}, "after": []}
        ],
        "completed_ids": [],
        "executing_ids": []
    }
    
    # Invalid input (missing required description)
    executor_step = {
        "next_step": 1,
        "remaining_steps": 0,
        "type": "tool_call",
        "tool": "add_task",
        "input": {}  # Missing required "description"
    }
    
    result = validate_executor_step(executor_step, current_plan, registry)
    
    print(f"   Valid: {result.valid}")
    print(f"   Errors: {result.errors}")
    
    assert not result.valid, "Should catch missing required field"
    assert any("E_SCHEMA" in error for error in result.errors)
    print("   ✅ PASSED - Input validation works")

def run_all_tests():
    """Run comprehensive validator tests."""
    print("🔍 CHATGPT VALIDATOR MODULE TESTS")
    print("=" * 50)
    
    try:
        test_valid_dag_plan()
        test_cycle_detection()
        test_schema_violations()
        test_executor_validation()
        test_readiness_checking()
        test_input_schema_validation()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ ChatGPT's validator module is BULLETPROOF!")
        print("🔧 Ready for integration into DAG controller")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    run_all_tests()
