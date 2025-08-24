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

"""Function registration for the Personal Assistant Demo."""

import logging

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

# Weather tools commented out - uncomment and add OPENWEATHER_API_KEY to use
# from .tools.weather import get_weather_info, check_weather_condition
from .tools.tasks import add_task, list_tasks, complete_task, delete_task
from .tools.calculator import add_numbers, subtract_numbers, multiply_numbers, divide_numbers, calculate_percentage
from .tools.datetime_info import (
    get_current_time, get_current_date, get_current_datetime,
    get_timezone_info, calculate_time_difference, get_day_of_week, get_current_hour
)

logger = logging.getLogger(__name__)


# Weather Tools - Commented out (uncomment and add OPENWEATHER_API_KEY to use)
# class WeatherInfoConfig(FunctionBaseConfig, name="weather_info"):
#     pass


# @register_function(config_type=WeatherInfoConfig)
# async def weather_info(config: WeatherInfoConfig, builder: Builder):
#     """Get current weather information for a city."""
#     yield FunctionInfo.from_fn(
#         get_weather_info,
#         description=(
#             "Get current weather information for any city. "
#             "Provide the city name and get temperature, conditions, and humidity. "
#             "Example: 'What's the weather in New York?'"
#         )
#     )


# class WeatherConditionConfig(FunctionBaseConfig, name="weather_condition"):
#     pass


# @register_function(config_type=WeatherConditionConfig)
# async def weather_condition(config: WeatherConditionConfig, builder: Builder):
#     """Check for specific weather conditions in a city."""
#     yield FunctionInfo.from_fn(
#         check_weather_condition,
#         description=(
#             "Check if a specific weather condition exists in a city. "
#             "Useful for questions like 'Is it raining in London?' or 'Is it sunny in Miami?'"
#         )
#     )


# Task Management Tools
class AddTaskConfig(FunctionBaseConfig, name="add_task"):
    pass


@register_function(config_type=AddTaskConfig)
async def add_task_function(config: AddTaskConfig, builder: Builder):
    """Add a new task to the task list."""
    yield FunctionInfo.from_fn(
        add_task,
        description=(
            "Add a new task to your personal task list. "
            "Provide a description of what needs to be done. "
            "Example: 'Add a task to buy groceries'"
        )
    )


class ListTasksConfig(FunctionBaseConfig, name="list_tasks"):
    pass


@register_function(config_type=ListTasksConfig)
async def list_tasks_function(config: ListTasksConfig, builder: Builder):
    """List all tasks with their current status."""
    yield FunctionInfo.from_fn(
        list_tasks,
        description=(
            "Show all tasks in your personal task list, including both pending and completed tasks. "
            "Use this when asked to show, list, or display tasks."
        )
    )


class CompleteTaskConfig(FunctionBaseConfig, name="complete_task"):
    pass


@register_function(config_type=CompleteTaskConfig)
async def complete_task_function(config: CompleteTaskConfig, builder: Builder):
    """Mark a task as completed."""
    yield FunctionInfo.from_fn(
        complete_task,
        description=(
            "Mark a task as completed. You can specify the task by its ID number or by part of its description. "
            "Example: 'Complete task 1' or 'Mark the grocery task as done'"
        )
    )


class DeleteTaskConfig(FunctionBaseConfig, name="delete_task"):
    pass


@register_function(config_type=DeleteTaskConfig)
async def delete_task_function(config: DeleteTaskConfig, builder: Builder):
    """Delete a task from the task list."""
    yield FunctionInfo.from_fn(
        delete_task,
        description=(
            "Delete a task from your task list. You can specify the task by its ID number or by part of its description. "
            "Example: 'Delete task 1' or 'Remove the grocery task'"
        )
    )


# Calculator Tools
class AddNumbersConfig(FunctionBaseConfig, name="add_numbers"):
    pass


@register_function(config_type=AddNumbersConfig)
async def add_numbers_function(config: AddNumbersConfig, builder: Builder):
    """Add two or more numbers together."""
    yield FunctionInfo.from_fn(
        add_numbers,
        description=(
            "Add two or more numbers together. "
            "Example: 'Add 25 and 37' or 'What's 10 + 20 + 30?'"
        )
    )


class SubtractNumbersConfig(FunctionBaseConfig, name="subtract_numbers"):
    pass


@register_function(config_type=SubtractNumbersConfig)
async def subtract_numbers_function(config: SubtractNumbersConfig, builder: Builder):
    """Subtract one number from another."""
    yield FunctionInfo.from_fn(
        subtract_numbers,
        description=(
            "Subtract the second number from the first number. "
            "Example: 'Subtract 15 from 50' or 'What's 100 - 25?'"
        )
    )


class MultiplyNumbersConfig(FunctionBaseConfig, name="multiply_numbers"):
    pass


@register_function(config_type=MultiplyNumbersConfig)
async def multiply_numbers_function(config: MultiplyNumbersConfig, builder: Builder):
    """Multiply two or more numbers together."""
    yield FunctionInfo.from_fn(
        multiply_numbers,
        description=(
            "Multiply two or more numbers together. "
            "Example: 'Multiply 8 by 7' or 'What's 5 × 4 × 3?'"
        )
    )


class DivideNumbersConfig(FunctionBaseConfig, name="divide_numbers"):
    pass


@register_function(config_type=DivideNumbersConfig)
async def divide_numbers_function(config: DivideNumbersConfig, builder: Builder):
    """Divide one number by another."""
    yield FunctionInfo.from_fn(
        divide_numbers,
        description=(
            "Divide the first number by the second number. "
            "Example: 'Divide 100 by 4' or 'What's 50 ÷ 2?'"
        )
    )


# Additional calculator function - uncomment if needed
# class CalculatePercentageConfig(FunctionBaseConfig, name="calculate_percentage"):
#     pass


# @register_function(config_type=CalculatePercentageConfig)
# async def calculate_percentage_function(config: CalculatePercentageConfig, builder: Builder):
#     """Calculate a percentage of a number."""
#     yield FunctionInfo.from_fn(
#         calculate_percentage,
#         description=(
#             "Calculate what percentage of a number equals. "
#             "Example: 'What's 20% of 150?' or 'Calculate 15 percent of 200'"
#         )
#     )


# Date/Time Tools
class CurrentTimeConfig(FunctionBaseConfig, name="current_time"):
    pass


@register_function(config_type=CurrentTimeConfig)
async def current_time_function(config: CurrentTimeConfig, builder: Builder):
    """Get the current time."""
    yield FunctionInfo.from_fn(
        get_current_time,
        description=(
            "Get the current time in 12-hour format with AM/PM. "
            "Example: 'What time is it?' or 'Tell me the current time'"
        )
    )


class CurrentDateConfig(FunctionBaseConfig, name="current_date"):
    pass


@register_function(config_type=CurrentDateConfig)
async def current_date_function(config: CurrentDateConfig, builder: Builder):
    """Get the current date."""
    yield FunctionInfo.from_fn(
        get_current_date,
        description=(
            "Get the current date with day of week, month, day, and year. "
            "Example: 'What's today's date?' or 'What day is it?'"
        )
    )


class CurrentDatetimeConfig(FunctionBaseConfig, name="current_datetime"):
    pass


@register_function(config_type=CurrentDatetimeConfig)
async def current_datetime_function(config: CurrentDatetimeConfig, builder: Builder):
    """Get the current date and time together."""
    yield FunctionInfo.from_fn(
        get_current_datetime,
        description=(
            "Get both the current date and time together. "
            "Example: 'What's the current date and time?'"
        )
    )


# Additional datetime functions - uncomment if needed
# class TimezoneInfoConfig(FunctionBaseConfig, name="timezone_info"):
#     pass


# @register_function(config_type=TimezoneInfoConfig)
# async def timezone_info_function(config: TimezoneInfoConfig, builder: Builder):
#     """Get timezone information."""
#     yield FunctionInfo.from_fn(
#         get_timezone_info,
#         description=(
#             "Get information about the current timezone including name and UTC offset. "
#             "Example: 'What timezone am I in?' or 'What's my timezone?'"
#         )
#     )


# class TimeDifferenceConfig(FunctionBaseConfig, name="time_difference"):
#     pass


# @register_function(config_type=TimeDifferenceConfig)
# async def time_difference_function(config: TimeDifferenceConfig, builder: Builder):
#     """Calculate time after adding or subtracting hours."""
#     yield FunctionInfo.from_fn(
#         calculate_time_difference,
#         description=(
#             "Calculate what time it will be after adding or subtracting hours from now. "
#             "Example: 'What time will it be in 3 hours?' or 'What time was it 2 hours ago?'"
#         )
#     )


# class DayOfWeekConfig(FunctionBaseConfig, name="day_of_week"):
#     pass


# @register_function(config_type=DayOfWeekConfig)
# async def day_of_week_function(config: DayOfWeekConfig, builder: Builder):
#     """Get the current day of the week."""
#     yield FunctionInfo.from_fn(
#         get_day_of_week,
#         description=(
#             "Get the current day of the week. "
#             "Example: 'What day is today?' or 'What day of the week is it?'"
#         )
#     )


# class CurrentHourConfig(FunctionBaseConfig, name="current_hour"):
#     pass


# @register_function(config_type=CurrentHourConfig)
# async def current_hour_function(config: CurrentHourConfig, builder: Builder):
#     """Get the current hour in 24-hour format."""
#     yield FunctionInfo.from_fn(
#         get_current_hour,
#         description=(
#             "Get the current hour in 24-hour format (0-23). "
#             "Useful for time-based comparisons and calculations."
#         )
#     )
