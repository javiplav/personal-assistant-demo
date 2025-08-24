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

"""Tests for date/time information tools."""

import pytest
from datetime import datetime
from personal_assistant.tools.datetime_info import (
    get_current_time, get_current_date, get_current_datetime,
    get_timezone_info, calculate_time_difference, get_day_of_week, get_current_hour
)


@pytest.mark.asyncio
async def test_get_current_time():
    """Test getting current time."""
    result = await get_current_time()
    assert "current time is" in result.lower()
    # Should contain AM or PM
    assert "AM" in result or "PM" in result


@pytest.mark.asyncio
async def test_get_current_date():
    """Test getting current date."""
    result = await get_current_date()
    assert "today is" in result.lower()
    # Should contain current year
    current_year = str(datetime.now().year)
    assert current_year in result


@pytest.mark.asyncio
async def test_get_current_datetime():
    """Test getting current date and time."""
    result = await get_current_datetime()
    assert "currently" in result.lower()
    assert "at" in result.lower()


@pytest.mark.asyncio
async def test_get_timezone_info():
    """Test getting timezone information."""
    result = await get_timezone_info()
    assert "timezone" in result.lower()
    assert "UTC" in result


@pytest.mark.asyncio
async def test_calculate_time_difference():
    """Test calculating time differences."""
    result = await calculate_time_difference("3")
    assert "3" in result
    assert "hours" in result.lower()
    assert "currently" in result.lower()
    
    # Test negative hours
    result = await calculate_time_difference("-2")
    assert "2" in result
    assert "ago" in result.lower()


@pytest.mark.asyncio
async def test_get_day_of_week():
    """Test getting day of the week."""
    result = await get_day_of_week()
    assert "today is" in result.lower()
    # Should contain one of the days of the week
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    assert any(day in result.lower() for day in days)


@pytest.mark.asyncio
async def test_get_current_hour():
    """Test getting current hour."""
    result = await get_current_hour()
    assert "current hour is" in result.lower()
    assert "24-hour format" in result.lower()
    
    # Should contain a number between 0-23
    current_hour = datetime.now().hour
    assert str(current_hour) in result


@pytest.mark.asyncio
async def test_calculate_time_difference_invalid():
    """Test time difference calculation with invalid input."""
    result = await calculate_time_difference("not a number")
    assert "provide the number" in result.lower()
