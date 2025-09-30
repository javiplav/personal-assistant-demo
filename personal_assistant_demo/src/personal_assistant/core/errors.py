"""
Centralized error handling for the personal assistant agent.

Provides:
- Typed exceptions for different error categories
- Standardized error codes
- Error response formatting
"""

from typing import Optional, Dict, Any


class PersonalAssistantError(Exception):
    """Base exception for personal assistant errors."""
    
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(PersonalAssistantError):
    """Errors related to input validation and schema checking."""
    pass


class PlanningError(PersonalAssistantError):
    """Errors during plan creation and validation."""
    pass


class ExecutionError(PersonalAssistantError):
    """Errors during step execution."""
    pass


class ToolError(PersonalAssistantError):
    """Errors from tool execution."""
    pass


class CircuitBreakerError(PersonalAssistantError):
    """Errors when circuit breaker is open."""
    pass


# Standard error codes
class ErrorCodes:
    """Centralized error codes for consistent error handling."""
    
    # Validation errors
    E_SCHEMA = "E_SCHEMA"
    E_CYCLE = "E_CYCLE"
    E_STEP_ORDER = "E_STEP_ORDER"
    E_TOOL_UNKNOWN = "E_TOOL_UNKNOWN"
    E_READINESS = "E_READINESS"
    E_DUP_ID = "E_DUP_ID"
    E_REF_UNKNOWN = "E_REF_UNKNOWN"
    
    # Execution errors
    E_TIMEOUT = "E_TIMEOUT"
    E_RATE_LIMIT = "E_RATE_LIMIT"
    E_TOOL_FAILED = "E_TOOL_FAILED"
    E_DEADLINE = "E_DEADLINE"
    
    # Circuit breaker errors
    E_CIRCUIT_OPEN = "E_CIRCUIT_OPEN"
    
    # Generic errors
    E_UNKNOWN = "E_UNKNOWN"


def create_error_response(
    success: bool = False,
    message: str = "",
    error_code: Optional[str] = None,
    error_details: Optional[Dict[str, Any]] = None,
    data: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Create standardized error response format.
    
    Args:
        success: Whether the operation was successful
        message: Human-readable message
        error_code: Machine-readable error code
        error_details: Additional error details
        data: Any relevant data
        
    Returns:
        Standardized error response dictionary
    """
    response = {
        "success": success,
        "message": message
    }
    
    if success and data is not None:
        response["data"] = data
    elif not success:
        response["error"] = message
        if error_code:
            response["error_code"] = error_code
        if error_details:
            response["error_details"] = error_details
    
    return response
