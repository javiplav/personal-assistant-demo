# Legacy Code Directory

This directory contains deprecated code that has been superseded by the production-grade implementation.

## ⚠️ Deprecation Notice

**Status**: DEPRECATED  
**Removal Date**: January 2026 (90 days from migration)  
**Migration Path**: Use `core/` modules instead

## Files in This Directory

### `enhanced_react_handler.py`
- **Status**: Deprecated
- **Reason**: ReAct agents suffer from "drift" in multi-step scenarios
- **Replacement**: Planner-Executor architecture in `core/agent.py`
- **Last Known Working Config**: `configs/config-ollama-react.yml`

### `planner_executor_agent.py`  
- **Status**: Deprecated
- **Reason**: Basic implementation superseded by production-hardened version
- **Replacement**: Full implementation in `core/` modules
- **Migration**: All features moved to core architecture

## Why These Were Deprecated

1. **ReAct Drift**: The ReAct handler would lose context in multi-step requests and enter analysis loops
2. **Limited Production Features**: Basic planner-executor lacked circuit breakers, PII sanitization, validation
3. **Monolithic Design**: Single large files instead of modular, testable components

## Migration Guide

### From ReAct Agent
```python
# OLD - Don't use
from personal_assistant.legacy.enhanced_react_handler import ReactAgent

# NEW - Use this instead
from personal_assistant.core.agent import PersonalAssistantAgent
```

### From Basic Planner-Executor
```python  
# OLD - Don't use
from personal_assistant.legacy.planner_executor_agent import PlannerExecutorAgent

# NEW - Use this instead  
from personal_assistant.core.agent import PersonalAssistantAgent
```

## Production Advantages of New Architecture

- ✅ **No ReAct Drift** - Deterministic planner-executor flow
- ✅ **Circuit Breakers** - Tool-level failure isolation  
- ✅ **PII Sanitization** - Safe for production data
- ✅ **Comprehensive Validation** - Bulletproof plan checking
- ✅ **Performance Monitoring** - OpenTelemetry integration
- ✅ **Result Caching** - Intelligent memoization
- ✅ **Golden Test Coverage** - 7 parametrized regression tests

## Support

If you need to reference legacy behavior:
1. Check git history for implementation details
2. Review `configs/config-ollama-react.yml` for ReAct configuration
3. Consult `docs/architecture.md` for migration patterns

**Do not use legacy code in new development.**
