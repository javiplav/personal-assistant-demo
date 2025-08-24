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

import re
import logging
from typing import List

logger = logging.getLogger(__name__)


def _extract_numbers(text: str) -> List[float]:
    """Extract numbers from text, supporting both integers and floats."""
    # Pattern to match integers and floats (including negative numbers)
    pattern = r'-?\d+\.?\d*'
    matches = re.findall(pattern, text)
    return [float(match) for match in matches if match]


async def add_numbers(text: str) -> str:
    """
    Add two or more numbers together.
    
    Args:
        text: Text containing the numbers to add
        
    Returns:
        The sum of the numbers
    """
    try:
        numbers = _extract_numbers(text)
        
        if len(numbers) < 2:
            return "Please provide at least two numbers to add together."
        
        result = sum(numbers)
        
        if len(numbers) == 2:
            return f"The sum of {numbers[0]} + {numbers[1]} = {result}"
        else:
            numbers_str = " + ".join(str(n) for n in numbers)
            return f"The sum of {numbers_str} = {result}"
            
    except Exception as e:
        logger.error(f"Error adding numbers: {e}")
        return f"Sorry, I couldn't perform the addition. Please check your input and try again."


async def subtract_numbers(text: str) -> str:
    """
    Subtract the second number from the first number.
    
    Args:
        text: Text containing the numbers to subtract
        
    Returns:
        The difference of the numbers
    """
    try:
        numbers = _extract_numbers(text)
        
        if len(numbers) < 2:
            return "Please provide two numbers to subtract."
        
        if len(numbers) > 2:
            return "This tool only supports subtraction between two numbers."
        
        result = numbers[0] - numbers[1]
        return f"The result of {numbers[0]} - {numbers[1]} = {result}"
        
    except Exception as e:
        logger.error(f"Error subtracting numbers: {e}")
        return f"Sorry, I couldn't perform the subtraction. Please check your input and try again."


async def multiply_numbers(text: str) -> str:
    """
    Multiply two or more numbers together.
    
    Args:
        text: Text containing the numbers to multiply
        
    Returns:
        The product of the numbers
    """
    try:
        numbers = _extract_numbers(text)
        
        if len(numbers) < 2:
            return "Please provide at least two numbers to multiply together."
        
        result = 1
        for num in numbers:
            result *= num
        
        if len(numbers) == 2:
            return f"The product of {numbers[0]} × {numbers[1]} = {result}"
        else:
            numbers_str = " × ".join(str(n) for n in numbers)
            return f"The product of {numbers_str} = {result}"
            
    except Exception as e:
        logger.error(f"Error multiplying numbers: {e}")
        return f"Sorry, I couldn't perform the multiplication. Please check your input and try again."


async def divide_numbers(text: str) -> str:
    """
    Divide the first number by the second number.
    
    Args:
        text: Text containing the numbers to divide
        
    Returns:
        The quotient of the numbers
    """
    try:
        numbers = _extract_numbers(text)
        
        if len(numbers) < 2:
            return "Please provide two numbers to divide."
        
        if len(numbers) > 2:
            return "This tool only supports division between two numbers."
        
        if numbers[1] == 0:
            return "Cannot divide by zero!"
        
        result = numbers[0] / numbers[1]
        return f"The result of {numbers[0]} ÷ {numbers[1]} = {result}"
        
    except Exception as e:
        logger.error(f"Error dividing numbers: {e}")
        return f"Sorry, I couldn't perform the division. Please check your input and try again."


async def calculate_percentage(text: str) -> str:
    """
    Calculate a percentage of a number.
    
    Args:
        text: Text containing the percentage and number (e.g., "20% of 150")
        
    Returns:
        The calculated percentage value
    """
    try:
        # Look for percentage pattern like "20% of 150" or "20 percent of 150"
        percentage_pattern = r'(\d+\.?\d*)%?\s*(?:percent)?\s*of\s*(\d+\.?\d*)'
        match = re.search(percentage_pattern, text, re.IGNORECASE)
        
        if match:
            percentage = float(match.group(1))
            number = float(match.group(2))
            result = (percentage / 100) * number
            return f"{percentage}% of {number} = {result}"
        
        # Fallback: try to extract two numbers and assume first is percentage
        numbers = _extract_numbers(text)
        if len(numbers) >= 2:
            percentage = numbers[0]
            number = numbers[1]
            result = (percentage / 100) * number
            return f"{percentage}% of {number} = {result}"
        
        return "Please provide a percentage and a number (e.g., '20% of 150' or '20 percent of 150')."
        
    except Exception as e:
        logger.error(f"Error calculating percentage: {e}")
        return f"Sorry, I couldn't calculate the percentage. Please check your input and try again."
