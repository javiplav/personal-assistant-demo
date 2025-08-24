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

"""Date and time information tools for the Personal Assistant Demo."""

import logging
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


async def get_current_time(query: str = "") -> str:
    """
    Get the current time.
    
    Returns:
        A formatted string with the current time
    """
    try:
        now = datetime.now()
        formatted_time = now.strftime("%I:%M %p")  # 12-hour format with AM/PM
        return f"The current time is {formatted_time}"
        
    except Exception as e:
        logger.error(f"Error getting current time: {e}")
        return "Sorry, I couldn't get the current time."


async def get_current_date(query: str = "") -> str:
    """
    Get the current date.
    
    Returns:
        A formatted string with the current date
    """
    try:
        now = datetime.now()
        formatted_date = now.strftime("%A, %B %d, %Y")  # e.g., "Monday, January 15, 2024"
        return f"Today is {formatted_date}"
        
    except Exception as e:
        logger.error(f"Error getting current date: {e}")
        return "Sorry, I couldn't get the current date."


async def get_current_datetime(query: str = "") -> str:
    """
    Get the current date and time together.
    
    Returns:
        A formatted string with the current date and time
    """
    try:
        now = datetime.now()
        formatted_datetime = now.strftime("%A, %B %d, %Y at %I:%M %p")
        return f"It is currently {formatted_datetime}"
        
    except Exception as e:
        logger.error(f"Error getting current datetime: {e}")
        return "Sorry, I couldn't get the current date and time."


async def get_timezone_info() -> str:
    """
    Get timezone information.
    
    Returns:
        A string with timezone information
    """
    try:
        # Get the local timezone name
        timezone_name = time.tzname[0] if not time.daylight else time.tzname[1]
        
        # Get UTC offset
        now = datetime.now()
        utc_offset = now.astimezone().strftime('%z')
        
        # Format the offset nicely (e.g., +0500 -> +05:00)
        if len(utc_offset) == 5:
            formatted_offset = f"{utc_offset[:3]}:{utc_offset[3:]}"
        else:
            formatted_offset = utc_offset
        
        return f"Your timezone is {timezone_name} (UTC{formatted_offset})"
        
    except Exception as e:
        logger.error(f"Error getting timezone info: {e}")
        return "Sorry, I couldn't get timezone information."


async def calculate_time_difference(hours: str) -> str:
    """
    Calculate what time it will be after adding or subtracting hours.
    
    Args:
        hours: Number of hours to add (positive) or subtract (negative)
        
    Returns:
        The calculated time
    """
    try:
        # Extract the number from the text
        import re
        numbers = re.findall(r'-?\d+\.?\d*', hours)
        
        if not numbers:
            return "Please provide the number of hours to add or subtract."
        
        hours_to_add = float(numbers[0])
        
        now = datetime.now()
        future_time = now + timedelta(hours=hours_to_add)
        
        current_time_str = now.strftime("%I:%M %p")
        future_time_str = future_time.strftime("%I:%M %p")
        
        if hours_to_add > 0:
            return f"It is currently {current_time_str}. In {hours_to_add} hours, it will be {future_time_str}."
        elif hours_to_add < 0:
            return f"It is currently {current_time_str}. {abs(hours_to_add)} hours ago, it was {future_time_str}."
        else:
            return f"It is currently {current_time_str}."
            
    except Exception as e:
        logger.error(f"Error calculating time difference: {e}")
        return "Sorry, I couldn't calculate the time difference."


async def get_day_of_week(query: str = "") -> str:
    """
    Get the current day of the week.
    
    Returns:
        The current day of the week
    """
    try:
        now = datetime.now()
        day_name = now.strftime("%A")
        return f"Today is {day_name}"
        
    except Exception as e:
        logger.error(f"Error getting day of week: {e}")
        return "Sorry, I couldn't get the current day of the week."


async def get_current_hour(query: str = "") -> str:
    """
    Get the current hour (24-hour format).
    
    Returns:
        The current hour
    """
    try:
        now = datetime.now()
        current_hour = now.hour
        return f"The current hour is {current_hour} (24-hour format)"
        
    except Exception as e:
        logger.error(f"Error getting current hour: {e}")
        return "Sorry, I couldn't get the current hour."
