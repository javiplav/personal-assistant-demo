# agent_validator.py
# Phase 3: Planner/Executor front-gate validator for NAT hardened agents.
# - Validates planner DAG JSON against schema, detects cycles, normalizes steps.
# - Validates executor step JSON against schema, checks readiness vs DAG, and per-tool input schemas.
# - No LLM/runtime dependencies; pure Python + jsonschema.

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple
import re

try:
    from jsonschema import Draft202012Validator, validate as _js_validate, exceptions as js_exceptions
except Exception as e:
    raise RuntimeError(
        "jsonschema is required. Install with: pip install 'jsonschema>=4.0'"
    ) from e


# ---------- Error codes ----------
E_SCHEMA       = "E_SCHEMA"        # JSON Schema violation
E_CYCLE        = "E_CYCLE"         # Graph contains cycles
E_STEP_ORDER   = "E_STEP_ORDER"    # Step numbering / topo inconsistencies
E_TOOL_UNKNOWN = "E_TOOL_UNKNOWN"  # Tool not found in registry
E_READINESS    = "E_READINESS"     # Executor proposed a node that isn't ready
E_DUP_ID       = "E_DUP_ID"        # Duplicate node IDs
E_REF_UNKNOWN  = "E_REF_UNKNOWN"   # 'after' references unknown node IDs


# ---------- Dataclasses ----------
@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]
    normalized_plan: Optional[Dict[str, Any]] = None
    topo_order_ids: Optional[List[str]] = None  # Stable topo order of node ids


# ---------- Utilities ----------
_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_\-]{1,31}$")

def _err(code: str, msg: str) -> str:
    return f"{code}: {msg}"

def _build_planner_schema(allowed_tools: List[str]) -> Dict[str, Any]:
    # Planner (DAG) schema – dynamic enum of tools from registry
    return {
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
                        "id":   {"type": "string", "pattern": "^[a-z][a-z0-9_\\-]{1,31}$"},
                        "step": {"type": "integer", "minimum": 1},
                        "tool": {"type": "string", "enum": allowed_tools},
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

def _build_executor_schema(allowed_tools: List[str]) -> Dict[str, Any]:
    # Executor output schema – dynamic enum of tools
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["next_step", "remaining_steps", "type"],
        "additionalProperties": False,
        "properties": {
            "next_step": {"type": "integer", "minimum": 1},
            "remaining_steps": {"type": "integer", "minimum": 0},
            "type": {"type": "string", "enum": ["tool_call", "final"]},
            "tool": {"type": "string", "enum": allowed_tools},
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

def _schema_validate(instance: Any, schema: Dict[str, Any]) -> List[str]:
    try:
        Draft202012Validator(schema).validate(instance)
        return []
    except js_exceptions.ValidationError as e:
        return [_err(E_SCHEMA, f"{e.message} at path {'/'.join(map(str, e.path))}")]

def _build_graph(plan_nodes: List[Dict[str, Any]]) -> Tuple[Dict[str, List[str]], Dict[str, Dict[str, Any]]]:
    graph: Dict[str, List[str]] = {}
    nodes_by_id: Dict[str, Dict[str, Any]] = {}
    for n in plan_nodes:
        nid = n["id"]
        graph.setdefault(nid, [])
        nodes_by_id[nid] = n
    for n in plan_nodes:
        nid = n["id"]
        for dep in n.get("after", []):
            graph.setdefault(dep, [])
            graph[dep].append(nid)
    return graph, nodes_by_id

def _detect_cycles(graph: Dict[str, List[str]]) -> Optional[List[str]]:
    WHITE, GRAY, BLACK = 0, 1, 2
    color: Dict[str, int] = {u: WHITE for u in graph}
    stack: List[str] = []

    def dfs(u: str) -> bool:
        color[u] = GRAY
        stack.append(u)
        for v in graph.get(u, []):
            if color[v] == WHITE:
                if dfs(v):
                    return True
            elif color[v] == GRAY:
                # Found a back edge; report the cycle path suffix
                cycle_start = stack.index(v)
                raise RuntimeError("->".join(stack[cycle_start:] + [v]))
        color[u] = BLACK
        stack.pop()
        return False

    try:
        for u in list(graph.keys()):
            if color[u] == WHITE:
                dfs(u)
        return None
    except RuntimeError as cyc:
        return str(cyc).split("->")

def _topo_sort(graph: Dict[str, List[str]]) -> List[str]:
    indeg: Dict[str, int] = {u: 0 for u in graph}
    for u in graph:
        for v in graph[u]:
            indeg[v] = indeg.get(v, 0) + 1
    # Deterministic tie-break
    zero = sorted([u for u, d in indeg.items() if d == 0])
    order: List[str] = []
    while zero:
        u = zero.pop(0)
        order.append(u)
        for v in sorted(graph.get(u, [])):
            indeg[v] -= 1
            if indeg[v] == 0:
                zero.append(v)
                zero.sort()
    if len(order) != len(indeg):
        # Not a DAG (shouldn't happen if cycle check passed)
        return []
    return order

def _normalize_steps(plan_nodes: List[Dict[str, Any]], topo_ids: List[str]) -> List[Dict[str, Any]]:
    # Re-assign step numbers in topo order (1..N), preserve id/tool/input/after
    id_to_node = {n["id"]: dict(n) for n in plan_nodes}
    normalized: List[Dict[str, Any]] = []
    for idx, nid in enumerate(topo_ids, start=1):
        node = id_to_node[nid]
        node["step"] = idx
        normalized.append(node)
    return normalized


# ---------- Public API ----------
def validate_plan(plan_json: Dict[str, Any], tool_registry: Dict[str, Any]) -> ValidationResult:
    """
    Validate planner output:
      - JSON Schema (structure, allowed tools, field types)
      - IDs: unique, pattern, all 'after' refer to existing IDs
      - Cycle detection
      - Topological sort
      - Normalization: step renumbering in topo order
    Returns ValidationResult(valid, errors, normalized_plan, topo_order_ids)
    """
    errors: List[str] = []
    tools = sorted(list(tool_registry.get("tools", {}).keys()))
    if not tools:
        return ValidationResult(False, [_err(E_SCHEMA, "Empty tool registry")])

    # 1) Schema
    schema = _build_planner_schema(allowed_tools=tools)
    errors += _schema_validate(plan_json, schema)
    if errors:
        return ValidationResult(False, errors)

    nodes = plan_json["plan"]

    # 2) ID checks, refs
    seen: Set[str] = set()
    for n in nodes:
        nid = n["id"]
        if nid in seen:
            errors.append(_err(E_DUP_ID, f"Duplicate id '{nid}'"))
        else:
            seen.add(nid)
        if not _ID_PATTERN.match(nid):
            errors.append(_err(E_SCHEMA, f"id '{nid}' violates pattern ^[a-z][a-z0-9_\\-]{{1,31}}$"))
        # tool must exist
        tool = n["tool"]
        if tool not in tool_registry["tools"]:
            errors.append(_err(E_TOOL_UNKNOWN, f"Unknown tool '{tool}'"))
        # after references must exist
        for dep in n.get("after", []):
            if dep not in [m["id"] for m in nodes]:
                errors.append(_err(E_REF_UNKNOWN, f"Node '{nid}' depends on unknown id '{dep}'"))

    if errors:
        return ValidationResult(False, errors)

    # 3) Graph build & cycle detection
    graph, _nodes_by_id = _build_graph(nodes)
    cycle = _detect_cycles(graph)
    if cycle:
        errors.append(_err(E_CYCLE, f"Cycle detected: {' -> '.join(cycle)}"))
        return ValidationResult(False, errors)

    # 4) Topo sort
    topo_ids = _topo_sort(graph)
    if not topo_ids or len(topo_ids) != len(nodes):
        errors.append(_err(E_STEP_ORDER, "Topological sort failed or incomplete"))
        return ValidationResult(False, errors)

    # 5) Normalization (renumber steps in topo order)
    normalized_nodes = _normalize_steps(nodes, topo_ids)
    normalized_plan = {"plan": normalized_nodes}

    return ValidationResult(True, [], normalized_plan, topo_ids)


def validate_executor_step(
    step_json: Dict[str, Any],
    current_plan: Dict[str, Any],
    tool_registry: Dict[str, Any],
) -> ValidationResult:
    """
    Validate executor output:
      - JSON Schema for executor message
      - If type="tool_call": tool exists, node is READY (deps satisfied, not already done)
      - Input validates against tool's input_schema
    current_plan should contain:
      {
        "plan": [ {id, step, tool, input, after}, ... ],
        "completed_ids": [ ... ],              # required for readiness checks
        "executing_ids": [ ... ] (optional)    # to avoid double-launch
      }
    Returns ValidationResult(valid, errors, normalized_plan=None, topo_order_ids=None)
    """
    errors: List[str] = []
    tools = sorted(list(tool_registry.get("tools", {}).keys()))
    if not tools:
        return ValidationResult(False, [_err(E_SCHEMA, "Empty tool registry")])

    schema = _build_executor_schema(allowed_tools=tools)
    errors += _schema_validate(step_json, schema)
    if errors:
        return ValidationResult(False, errors)

    plan_nodes: List[Dict[str, Any]] = current_plan.get("plan", [])
    completed: Set[str] = set(current_plan.get("completed_ids", []))
    executing: Set[str] = set(current_plan.get("executing_ids", []))

    # Quick index
    by_id = {n["id"]: n for n in plan_nodes}
    # Allow addressing by step or by tool+readiness. We check readiness by tool below.

    if step_json["type"] == "final":
        # All nodes must be completed
        if len(completed) != len(plan_nodes):
            errors.append(_err(E_STEP_ORDER, "Final requested but plan not fully completed"))
            return ValidationResult(False, errors)
        return ValidationResult(True, [], None, None)

    # type == "tool_call"
    tool = step_json["tool"]
    if tool not in tool_registry["tools"]:
        errors.append(_err(E_TOOL_UNKNOWN, f"Unknown tool '{tool}'"))
        return ValidationResult(False, errors)

    # Find READY node(s) in plan that match this tool and are not completed/executing.
    # A node is READY if all deps in 'after' are in completed.
    ready_candidates: List[Dict[str, Any]] = []
    for n in plan_nodes:
        if n["tool"] != tool:
            continue
        nid = n["id"]
        if nid in completed or nid in executing:
            continue
        deps_ok = all(dep in completed for dep in n.get("after", []))
        if deps_ok:
            ready_candidates.append(n)

    if not ready_candidates:
        errors.append(_err(E_READINESS, f"No READY node for tool '{tool}' given current dependencies"))
        return ValidationResult(False, errors)

    # Optional: if next_step is provided, prefer the ready node whose step equals next_step
    target_step = step_json.get("next_step", None)
    chosen = None
    if target_step is not None:
        for n in ready_candidates:
            if n.get("step") == target_step:
                chosen = n
                break
    if chosen is None:
        # Deterministic tie-break: lowest step, then id
        ready_candidates.sort(key=lambda n: (n.get("step", 1_000_000), n["id"]))
        chosen = ready_candidates[0]

    # Validate input against the tool's input_schema (from registry)
    tool_meta = tool_registry["tools"][tool]
    input_schema = tool_meta.get("input_schema", {"type": "object"})
    input_obj = step_json.get("input", {})
    errors += _schema_validate(input_obj, input_schema)
    if errors:
        return ValidationResult(False, errors)

    # All good
    return ValidationResult(True, [], None, None)


# ---------- Convenience helpers for controllers ----------
def is_node_ready(node: Dict[str, Any], completed_ids: Set[str]) -> bool:
    return all(dep in completed_ids for dep in node.get("after", []))

def ready_nodes(plan: List[Dict[str, Any]], completed_ids: Set[str], exclude_ids: Set[str] = None) -> List[Dict[str, Any]]:
    exclude_ids = exclude_ids or set()
    return [
        n for n in plan
        if n["id"] not in completed_ids
        and n["id"] not in exclude_ids
        and is_node_ready(n, completed_ids)
    ]
