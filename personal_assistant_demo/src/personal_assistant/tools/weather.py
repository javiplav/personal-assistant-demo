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

"""Weather tools for the Personal Assistant Demo."""

import logging
import requests
from ..env_loader import get_optional_env_var

logger = logging.getLogger(__name__)


def get_weather_info(city: str) -> str:
    """
    Get current weather information for a specified city.
    
    Args:
        city: The name of the city to get weather for
        
    Returns:
        String containing weather information or error message
    """
    try:
        api_key = get_optional_env_var("OPENWEATHERMAP_API_KEY")
        if not api_key:
            return "Weather service unavailable: API key not configured. Please set OPENWEATHERMAP_API_KEY environment variable."
        
        # OpenWeatherMap API endpoint
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric"  # Use Celsius
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant information
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            description = data["weather"][0]["description"].title()
            
            return f"Weather in {city}: {description}, {temp}°C (feels like {feels_like}°C), Humidity: {humidity}%"
        elif response.status_code == 404:
            return f"City '{city}' not found. Please check the spelling and try again."
        else:
            return f"Unable to fetch weather data for {city}. Service may be temporarily unavailable."
            
    except requests.exceptions.Timeout:
        return "Weather service request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        logger.error(f"Weather API request failed: {e}")
        return "Weather service is currently unavailable."
    except Exception as e:
        logger.error(f"Unexpected error in get_weather_info: {e}")
        return "An unexpected error occurred while fetching weather data."


def check_weather_condition(city: str, condition: str) -> str:
    """
    Check if a specific weather condition exists in a city.
    
    Args:
        city: The name of the city to check
        condition: The weather condition to check for (e.g., "rain", "snow", "clear")
        
    Returns:
        String indicating whether the condition exists
    """
    try:
        api_key = get_optional_env_var("OPENWEATHERMAP_API_KEY")
        if not api_key:
            return "Weather service unavailable: API key not configured."
        
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            current_condition = data["weather"][0]["main"].lower()
            description = data["weather"][0]["description"].lower()
            
            condition_lower = condition.lower()
            
            # Check if the condition matches
            if condition_lower in current_condition or condition_lower in description:
                return f"Yes, there is {condition} in {city} right now. Current weather: {data['weather'][0]['description'].title()}"
            else:
                return f"No, there is no {condition} in {city} right now. Current weather: {data['weather'][0]['description'].title()}"
        elif response.status_code == 404:
            return f"City '{city}' not found. Please check the spelling and try again."
        else:
            return f"Unable to check weather condition for {city}."
            
    except Exception as e:
        logger.error(f"Error in check_weather_condition: {e}")
        return "An error occurred while checking the weather condition."
