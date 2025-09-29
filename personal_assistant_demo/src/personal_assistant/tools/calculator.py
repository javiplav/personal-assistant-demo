# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Calculator tools for the Personal Assistant Demo."""

import json
import re
import logging
import time
import functools
from typing import List, Any, Callable

logger = logging.getLogger(__name__)


class CalculatorError(Exception):
    """Custom exception for calculator-related errors."""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code or "CALCULATOR_ERROR"
        super().__init__(message)


def _validate_calculation_input(text: str, min_numbers: int = 2) -> None:
    """Validate calculator input parameters."""
    if not text or not text.strip():
        raise CalculatorError("Input text cannot be empty", "INVALID_INPUT")
    
    if len(text.strip()) > 1000:
        raise CalculatorError("Input text too long (max 1000 characters)", "INPUT_TOO_LONG")
    
    numbers = _extract_numbers(text)
    if len(numbers) < min_numbers:
        raise CalculatorError(f"Please provide at least {min_numbers} number{'s' if min_numbers > 1 else ''}", "INSUFFICIENT_NUMBERS")


def _create_standard_response(success: bool, data: Any = None, message: str = "", 
                             error: str = None, error_code: str = None) -> str:
    """Create standardized JSON response."""
    response = {
        "success": success,
        "message": message
    }
    
    if success:
        if data is not None:
            response["data"] = data
    else:
        response["error"] = error or "Unknown error"
        if error_code:
            response["error_code"] = error_code
    
    return json.dumps(response)


def measure_performance(func: Callable) -> Callable:
    """Decorator to measure and log function performance."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = func.__name__
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > 0.5:  # Log slow operations (lower threshold for calculations)
                logger.warning(f"{function_name} took {execution_time:.3f}s (slow)")
            else:
                logger.info(f"{function_name} completed in {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{function_name} failed after {execution_time:.3f}s: {e}")
            raise
    
    return wrapper


def _extract_numbers(text: str) -> List[float]:
    """Extract numbers from text, supporting both integers and floats."""
    # Pattern to match integers and floats (including negative numbers)
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    return [float(match) for match in matches if match]


@measure_performance
async def add_numbers(text: str) -> str:
    """
    Add two or more numbers together.
    
    Args:
        text: Text containing the numbers to add
        
    Returns:
        JSON string with standardized response format
    """
    try:
        # Input validation
        _validate_calculation_input(text, min_numbers=2)
        
        numbers = _extract_numbers(text)
        result = sum(numbers)
        
        # Create human-readable message
        if len(numbers) == 2:
            operation_str = f"{numbers[0]} + {numbers[1]}"
        else:
            operation_str = " + ".join(str(n) for n in numbers)
        
        message = f"The sum of {operation_str} = {result}"
        
        # Create response data
        response_data = {
            "operation": "addition",
            "operands": numbers,
            "result": result,
            "expression": operation_str
        }
            
        return _create_standard_response(
            success=True,
            data=response_data,
            message=message
        )
            
    except CalculatorError as e:
        return _create_standard_response(
            success=False,
            error=e.message,
            error_code=e.error_code
        )
    except Exception as e:
        logger.error(f"Unexpected error adding numbers: {e}")
        return _create_standard_response(
            success=False,
            error="Internal error occurred during addition",
            error_code="INTERNAL_ERROR"
        )


@measure_performance
async def subtract_numbers(text: str) -> str:
    """
    Subtract the second number from the first number.
    
    Args:
        text: Text containing the numbers to subtract
        
    Returns:
        JSON string with standardized response format
    """
    try:
        # Input validation
        _validate_calculation_input(text, min_numbers=2)
        
        numbers = _extract_numbers(text)
        
        # Check for too many numbers (keeping original behavior)
        if len(numbers) > 2:
            raise CalculatorError("This tool only supports subtraction between two numbers", "TOO_MANY_NUMBERS")
        
        result = numbers[0] - numbers[1]
        operation_str = f"{numbers[0]} - {numbers[1]}"
        message = f"The result of {operation_str} = {result}"
        
        # Create response data
        response_data = {
            "operation": "subtraction",
            "operands": numbers,
            "result": result,
            "expression": operation_str
        }
        
        return _create_standard_response(
            success=True,
            data=response_data,
            message=message
        )
        
    except CalculatorError as e:
        return _create_standard_response(
            success=False,
            error=e.message,
            error_code=e.error_code
        )
    except Exception as e:
        logger.error(f"Unexpected error subtracting numbers: {e}")
        return _create_standard_response(
            success=False,
            error="Internal error occurred during subtraction",
            error_code="INTERNAL_ERROR"
        )


@measure_performance
async def multiply_numbers(text: str) -> str:
    """
    Multiply two or more numbers together.
    
    Args:
        text: Text containing the numbers to multiply
        
    Returns:
        JSON string with standardized response format
    """
    try:
        # Input validation
        _validate_calculation_input(text, min_numbers=2)
        
        numbers = _extract_numbers(text)
        
        result = 1
        for num in numbers:
            result *= num
        
        # Create human-readable message
        if len(numbers) == 2:
            operation_str = f"{numbers[0]} × {numbers[1]}"
        else:
            operation_str = " × ".join(str(n) for n in numbers)
        
        message = f"The product of {operation_str} = {result}"
        
        # Create response data
        response_data = {
            "operation": "multiplication",
            "operands": numbers,
            "result": result,
            "expression": operation_str
        }
            
        return _create_standard_response(
            success=True,
            data=response_data,
            message=message
        )
            
    except CalculatorError as e:
        return _create_standard_response(
            success=False,
            error=e.message,
            error_code=e.error_code
        )
    except Exception as e:
        logger.error(f"Unexpected error multiplying numbers: {e}")
        return _create_standard_response(
            success=False,
            error="Internal error occurred during multiplication",
            error_code="INTERNAL_ERROR"
        )


@measure_performance
async def divide_numbers(text: str) -> str:
    """
    Divide the first number by the second number.
    
    Args:
        text: Text containing the numbers to divide
        
    Returns:
        JSON string with standardized response format
    """
    try:
        # Input validation
        _validate_calculation_input(text, min_numbers=2)
        
        numbers = _extract_numbers(text)
        
        # Check for too many numbers (keeping original behavior)
        if len(numbers) > 2:
            raise CalculatorError("This tool only supports division between two numbers", "TOO_MANY_NUMBERS")
        
        # Check for division by zero
        if numbers[1] == 0:
            raise CalculatorError("Cannot divide by zero", "DIVISION_BY_ZERO")
        
        result = numbers[0] / numbers[1]
        operation_str = f"{numbers[0]} ÷ {numbers[1]}"
        message = f"The result of {operation_str} = {result}"
        
        # Create response data
        response_data = {
            "operation": "division",
            "operands": numbers,
            "result": result,
            "expression": operation_str
        }
        
        return _create_standard_response(
            success=True,
            data=response_data,
            message=message
        )
        
    except CalculatorError as e:
        return _create_standard_response(
            success=False,
            error=e.message,
            error_code=e.error_code
        )
    except Exception as e:
        logger.error(f"Unexpected error dividing numbers: {e}")
        return _create_standard_response(
            success=False,
            error="Internal error occurred during division",
            error_code="INTERNAL_ERROR"
        )


@measure_performance
async def calculate_percentage(text: str) -> str:
    """
    Calculate a percentage of a number.
    
    Args:
        text: Text containing the percentage and number (e.g., "20% of 150")
        
    Returns:
        JSON string with standardized response format
    """
    try:
        # Input validation
        if not text or not text.strip():
            raise CalculatorError("Input text cannot be empty", "INVALID_INPUT")
        
        if len(text.strip()) > 1000:
            raise CalculatorError("Input text too long (max 1000 characters)", "INPUT_TOO_LONG")
        
        # Look for percentage pattern like "20% of 150" or "20 percent of 150"
        percentage_pattern = r'(\d+\.?\d*)%?\s*(?:percent)?\s*of\s*(\d+\.?\d*)'
        match = re.search(percentage_pattern, text, re.IGNORECASE)
        
        if match:
            percentage = float(match.group(1))
            number = float(match.group(2))
            result = (percentage / 100) * number
            
            operation_str = f"{percentage}% of {number}"
            message = f"{operation_str} = {result}"
            
            # Create response data
            response_data = {
                "operation": "percentage",
                "percentage": percentage,
                "base_number": number,
                "result": result,
                "expression": operation_str
            }
            
            return _create_standard_response(
                success=True,
                data=response_data,
                message=message
            )
        
        # Fallback: try to extract two numbers and assume first is percentage
        numbers = _extract_numbers(text)
        if len(numbers) >= 2:
            percentage = numbers[0]
            number = numbers[1]
            result = (percentage / 100) * number
            
            operation_str = f"{percentage}% of {number}"
            message = f"{operation_str} = {result}"
            
            # Create response data
            response_data = {
                "operation": "percentage",
                "percentage": percentage,
                "base_number": number,
                "result": result,
                "expression": operation_str
            }
            
            return _create_standard_response(
                success=True,
                data=response_data,
                message=message
            )
        
        raise CalculatorError("Please provide a percentage and a number (e.g., '20% of 150' or '20 percent of 150')", "INVALID_PERCENTAGE_FORMAT")
        
    except CalculatorError as e:
        return _create_standard_response(
            success=False,
            error=e.message,
            error_code=e.error_code
        )
    except Exception as e:
        logger.error(f"Unexpected error calculating percentage: {e}")
        return _create_standard_response(
            success=False,
            error="Internal error occurred during percentage calculation",
            error_code="INTERNAL_ERROR"
        )
