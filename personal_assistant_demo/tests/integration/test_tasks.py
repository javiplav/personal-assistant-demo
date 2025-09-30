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

"""Tests for task management tools."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

from personal_assistant.tools.tasks import add_task, list_tasks, complete_task, delete_task


@pytest.fixture
def temp_tasks_file():
    """Create a temporary tasks file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump([], f)
        temp_file = Path(f.name)
    
    # Patch the TASKS_FILE constant
    with patch('personal_assistant.tools.tasks.TASKS_FILE', temp_file):
        yield temp_file
    
    # Clean up
    if temp_file.exists():
        temp_file.unlink()


@pytest.mark.asyncio
async def test_add_task(temp_tasks_file):
    """Test adding a task."""
    result = await add_task("Buy groceries")
    assert "Added task" in result
    assert "Buy groceries" in result
    
    # Verify task was saved
    with open(temp_tasks_file, 'r') as f:
        tasks = json.load(f)
    assert len(tasks) == 1
    assert tasks[0]["description"] == "Buy groceries"
    assert tasks[0]["completed"] is False


@pytest.mark.asyncio
async def test_list_tasks_empty(temp_tasks_file):
    """Test listing tasks when none exist."""
    result = await list_tasks()
    assert "no tasks yet" in result.lower()


@pytest.mark.asyncio
async def test_list_tasks_with_tasks(temp_tasks_file):
    """Test listing tasks when tasks exist."""
    # Add some tasks first
    await add_task("Task 1")
    await add_task("Task 2")
    
    result = await list_tasks()
    assert "Task 1" in result
    assert "Task 2" in result
    assert "Pending Tasks" in result


@pytest.mark.asyncio
async def test_complete_task(temp_tasks_file):
    """Test completing a task."""
    # Add a task first
    await add_task("Test task")
    
    # Complete it by ID
    result = await complete_task("1")
    assert "Completed task" in result
    assert "Test task" in result
    
    # Verify task is marked as completed
    with open(temp_tasks_file, 'r') as f:
        tasks = json.load(f)
    assert tasks[0]["completed"] is True


@pytest.mark.asyncio
async def test_complete_task_by_description(temp_tasks_file):
    """Test completing a task by description."""
    await add_task("Buy milk")
    
    result = await complete_task("milk")
    assert "Completed task" in result
    assert "Buy milk" in result


@pytest.mark.asyncio
async def test_delete_task(temp_tasks_file):
    """Test deleting a task."""
    await add_task("Task to delete")
    
    result = await delete_task("1")
    assert "Deleted task" in result
    assert "Task to delete" in result
    
    # Verify task was deleted
    with open(temp_tasks_file, 'r') as f:
        tasks = json.load(f)
    assert len(tasks) == 0


@pytest.mark.asyncio
async def test_complete_nonexistent_task(temp_tasks_file):
    """Test completing a task that doesn't exist."""
    result = await complete_task("999")
    assert "couldn't find" in result.lower()


@pytest.mark.asyncio
async def test_complete_already_completed_task(temp_tasks_file):
    """Test completing an already completed task."""
    await add_task("Already done")
    await complete_task("1")  # Complete it
    
    result = await complete_task("1")  # Try to complete again
    assert "already completed" in result.lower()
