# tests/test_agent_pipeline.py
import time
import pytest
from collections import defaultdict
import sys
import os

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from personal_assistant.core.validator import validate_plan, validate_executor_step

# --------- Fixtures ---------
@pytest.fixture
def tool_registry():
    # Minimal subset to keep test small; replace with your full registry
    return {
        "tools": {
            "add_task": {"input_schema":{"type":"object","required":["description"],"additionalProperties":False,"properties":{"description":{"type":"string"}}},"purity":"impure","parallel_safe":False},
            "list_tasks": {"input_schema":{"type":"object","additionalProperties":False,"properties":{}},"purity":"read_only","parallel_safe":True},
            "calculate_percentage": {"input_schema":{"type":"object","required":["text"],"additionalProperties":False,"properties":{"text":{"type":"string"}}},"purity":"pure","parallel_safe":True},
        }
    }

@pytest.fixture
def make_plan(tool_registry):
    def _mk(nodes):
        raw = {"plan": nodes}
        res = validate_plan(raw, tool_registry)
        assert res.valid, res.errors
        return res.normalized_plan
    return _mk

@pytest.fixture
def controller_state():
    return {"completed_ids": set(), "executing_ids": set()}

# Fake tool runner to simulate latency/failure/cache
class FakeRunner:
    def __init__(self):
        self.cache = {}
        self.fail_once = set()
        self.logs = []

    def run(self, tool, inp):
        key = (tool, str(inp))
        if tool in ("calculate_percentage", "list_tasks") and key in self.cache:
            self.logs.append(("cache_hit", tool))
            return {"ok": True, "data": f"CACHED({tool})"}

        # Simulate transient failure once
        tag = (tool, "fail_once")
        if tag in self.fail_once:
            self.fail_once.remove(tag)
            self.logs.append(("fail_once", tool))
            return {"ok": False, "error": {"code":"TRANSIENT","message":"boom"}}

        # Latency profiles
        if tool == "add_task":
            time.sleep(0.01)
            out = {"ok": True, "data": "uuid-123"}
        elif tool == "list_tasks":
            time.sleep(0.005)
            out = {"ok": True, "data": ["a","b","c"]}
        elif tool == "calculate_percentage":
            time.sleep(0.002)
            out = {"ok": True, "data": "50"}
        else:
            out = {"ok": False, "error": {"code":"UNKNOWN","message":"tool"}}

        # Memoize pure/read_only for test purposes
        if tool in ("calculate_percentage", "list_tasks") and out["ok"]:
            self.cache[key] = out
        return out

# Helper: execute respecting readiness; super-compact for tests
def execute_plan(normalized_plan, tool_registry, runner: FakeRunner, controller_state, deadline_ms=None, retry=False):
    start = time.time()
    plan = list(normalized_plan["plan"])
    completed = controller_state["completed_ids"]
    while len(completed) < len(plan):
        if deadline_ms and (time.time() - start) * 1000 > deadline_ms:
            return {"ok": False, "error":"DEADLINE", "completed": len(completed)}
        # pick all ready nodes (simple linear pick for tests; your prod controller is DAG-parallel)
        ready = [n for n in plan if n["id"] not in completed and all(d in completed for d in n.get("after", []))]
        assert ready, "No ready nodes but plan not complete"
        n = sorted(ready, key=lambda x:(x["step"], x["id"]))[0]
        step_msg = {"next_step": n["step"], "remaining_steps": len(plan)-len(completed)-1, "type":"tool_call", "tool": n["tool"], "input": n["input"]}
        val = validate_executor_step(step_msg, {"plan": plan, **controller_state}, tool_registry)
        assert val.valid, val.errors
        res = runner.run(n["tool"], n["input"])
        if not res["ok"] and retry:
            # simple one-retry with small backoff
            time.sleep(0.01)
            res = runner.run(n["tool"], n["input"])
        if not res["ok"]:
            return {"ok": False, "error": res["error"], "completed": len(completed)}
        completed.add(n["id"])
    return {"ok": True, "completed": len(completed)}

# --------- Tests ---------

def test_happy_path_linear(make_plan, tool_registry):
    """Golden Test 1: Happy path 3-step baseline execution"""
    plan = make_plan([
        {"id":"s1","step":1,"tool":"add_task","input":{"description":"Demo"},"after":[]},
        {"id":"s2","step":2,"tool":"list_tasks","input":{},"after":["s1"]},
        {"id":"s3","step":3,"tool":"calculate_percentage","input":{"text":"25% of 200"},"after":["s1"]},
    ])
    res = execute_plan(plan, tool_registry, FakeRunner(), {"completed_ids": set(), "executing_ids": set()})
    assert res["ok"]

def test_large_observation_truncation(make_plan, tool_registry):
    """Golden Test 2: Large observation truncation handling"""
    # Simulate by repeating list results in FakeRunner; here we just validate plan passes and executes
    plan = make_plan([
        {"id":"s1","step":1,"tool":"add_task","input":{"description":"BigList"},"after":[]},
        {"id":"s2","step":2,"tool":"list_tasks","input":{},"after":["s1"]},
    ])
    res = execute_plan(plan, tool_registry, FakeRunner(), {"completed_ids": set(), "executing_ids": set()})
    assert res["ok"]

def test_transient_failure_with_retry(make_plan, tool_registry):
    """Golden Test 3: Transient failure with retry success"""
    plan = make_plan([
        {"id":"s1","step":1,"tool":"add_task","input":{"description":"Retry"},"after":[]},
        {"id":"s2","step":2,"tool":"list_tasks","input":{},"after":["s1"]},
    ])
    r = FakeRunner()
    r.fail_once.add(("list_tasks","fail_once"))
    res = execute_plan(plan, tool_registry, r, {"completed_ids": set(), "executing_ids": set()}, retry=True)
    assert res["ok"]
    assert ("fail_once","list_tasks") in r.logs

def test_duplicate_reads_collapsed_by_normalizer(tool_registry):
    """Golden Test 4: Duplicate reads collapsed by normalizer"""
    # Normalizer behavior is in your controller; here we validate the validator accepts the cleaned plan
    raw = {"plan":[
        {"id":"s1","step":1,"tool":"add_task","input":{"description":"X"},"after":[]},
        {"id":"s2","step":2,"tool":"list_tasks","input":{},"after":["s1"]},
        {"id":"s3","step":3,"tool":"list_tasks","input":{},"after":["s1"]},
    ]}
    # Emulate controller normalizer collapsing s2/s3 into one (left as comment); we simply accept a valid plan for test focus
    res = validate_plan(raw, tool_registry)
    assert res.valid

def test_parallel_safe_dag_ready_nodes(make_plan, tool_registry):
    """Golden Test 5: Parallel safe DAG (two pure calcs + dependent read)"""
    # Two pure calcs + one dependent read (would be parallel in prod)
    plan = make_plan([
        {"id":"s1","step":1,"tool":"add_task","input":{"description":"P"},"after":[]},
        {"id":"s2","step":2,"tool":"calculate_percentage","input":{"text":"25% of 200"},"after":["s1"]},
        {"id":"s3","step":3,"tool":"calculate_percentage","input":{"text":"15% of 300"},"after":["s1"]},
        {"id":"s4","step":4,"tool":"list_tasks","input":{},"after":["s1"]},
    ])
    # We won't assert true parallelism here (that's your controller integration test), but plan executes
    res = execute_plan(plan, tool_registry, FakeRunner(), {"completed_ids": set(), "executing_ids": set()})
    assert res["ok"]

def test_deadline_enforcement(make_plan, tool_registry):
    """Golden Test 6: Deadline enforcement with partial completion"""
    plan = make_plan([
        {"id":"s1","step":1,"tool":"add_task","input":{"description":"Slow"},"after":[]},
        {"id":"s2","step":2,"tool":"list_tasks","input":{},"after":["s1"]},
        {"id":"s3","step":3,"tool":"calculate_percentage","input":{"text":"25% of 200"},"after":["s1"]},
    ])
    res = execute_plan(plan, tool_registry, FakeRunner(), {"completed_ids": set(), "executing_ids": set()}, deadline_ms=5)
    assert not res["ok"] and res["error"] == "DEADLINE"

def test_cycle_injection_rejected(tool_registry):
    """Golden Test 7: Cycle injection test (validator rejects s1→s2→s1)"""
    bad = {"plan":[
        {"id":"s1","step":1,"tool":"add_task","input":{"description":"C"},"after":["s2"]},
        {"id":"s2","step":2,"tool":"list_tasks","input":{},"after":["s1"]},
    ]}
    res = validate_plan(bad, tool_registry)
    assert not res.valid
    assert any("E_CYCLE" in e for e in res.errors)
