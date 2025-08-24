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

"""Task management tools for the Personal Assistant Demo."""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to the tasks file
TASKS_FILE = Path(__file__).parent.parent.parent.parent / "data" / "tasks.json"


def _load_tasks() -> List[Dict[str, Any]]:
    """Load tasks from the JSON file."""
    try:
        if TASKS_FILE.exists():
            with open(TASKS_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading tasks: {e}")
        return []


def _save_tasks(tasks: List[Dict[str, Any]]) -> None:
    """Save tasks to the JSON file."""
    try:
        # Ensure the data directory exists
        TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving tasks: {e}")


async def add_task(description: str) -> str:
    """
    Add a new task to the task list.
    
    Args:
        description: Description of the task to add
        
    Returns:
        Confirmation message about the added task
    """
    try:
        tasks = _load_tasks()
        
        # Generate a simple ID based on the current number of tasks
        task_id = len(tasks) + 1
        
        new_task = {
            "id": task_id,
            "description": description.strip(),
            "completed": False,
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        }
        
        tasks.append(new_task)
        _save_tasks(tasks)
        
        return f"✅ Added task #{task_id}: '{description}'"
        
    except Exception as e:
        logger.error(f"Error adding task: {e}")
        return f"Sorry, I couldn't add the task '{description}'. Please try again."


async def list_tasks(query: str = "") -> str:
    """
    List all tasks with their status.
    
    Returns:
        A formatted string showing all tasks
    """
    try:
        tasks = _load_tasks()
        
        if not tasks:
            return "📝 You have no tasks yet. Add one by saying 'Add a task to...' or 'Create a task to...'"
        
        # Separate completed and pending tasks
        pending_tasks = [task for task in tasks if not task["completed"]]
        completed_tasks = [task for task in tasks if task["completed"]]
        
        result = []
        
        if pending_tasks:
            result.append("📋 **Pending Tasks:**")
            for task in pending_tasks:
                result.append(f"  • #{task['id']}: {task['description']}")
        
        if completed_tasks:
            result.append("\n✅ **Completed Tasks:**")
            for task in completed_tasks:
                result.append(f"  • #{task['id']}: {task['description']}")
        
        if not pending_tasks and completed_tasks:
            result.insert(0, "🎉 All tasks completed!")
        
        return "\n".join(result)
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return "Sorry, I couldn't retrieve your tasks. Please try again."


async def complete_task(task_identifier: str) -> str:
    """
    Mark a task as completed.
    
    Args:
        task_identifier: Task ID or description to complete
        
    Returns:
        Confirmation message about the completed task
    """
    try:
        tasks = _load_tasks()
        
        if not tasks:
            return "You have no tasks to complete."
        
        # Try to find the task by ID first, then by description
        task_to_complete = None
        
        # Check if identifier is a number (task ID)
        try:
            task_id = int(task_identifier)
            task_to_complete = next((task for task in tasks if task["id"] == task_id), None)
        except ValueError:
            # Not a number, search by description
            identifier_lower = task_identifier.lower()
            for task in tasks:
                if identifier_lower in task["description"].lower():
                    task_to_complete = task
                    break
        
        if not task_to_complete:
            return f"❌ I couldn't find a task matching '{task_identifier}'. Use 'list tasks' to see all tasks."
        
        if task_to_complete["completed"]:
            return f"✅ Task #{task_to_complete['id']} is already completed: '{task_to_complete['description']}'"
        
        # Mark as completed
        task_to_complete["completed"] = True
        task_to_complete["completed_at"] = datetime.now().isoformat()
        
        _save_tasks(tasks)
        
        return f"🎉 Completed task #{task_to_complete['id']}: '{task_to_complete['description']}'"
        
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        return f"Sorry, I couldn't complete the task '{task_identifier}'. Please try again."


async def delete_task(task_identifier: str) -> str:
    """
    Delete a task from the task list.
    
    Args:
        task_identifier: Task ID or description to delete
        
    Returns:
        Confirmation message about the deleted task
    """
    try:
        tasks = _load_tasks()
        
        if not tasks:
            return "You have no tasks to delete."
        
        # Try to find the task by ID first, then by description
        task_to_delete = None
        task_index = -1
        
        # Check if identifier is a number (task ID)
        try:
            task_id = int(task_identifier)
            for i, task in enumerate(tasks):
                if task["id"] == task_id:
                    task_to_delete = task
                    task_index = i
                    break
        except ValueError:
            # Not a number, search by description
            identifier_lower = task_identifier.lower()
            for i, task in enumerate(tasks):
                if identifier_lower in task["description"].lower():
                    task_to_delete = task
                    task_index = i
                    break
        
        if not task_to_delete:
            return f"❌ I couldn't find a task matching '{task_identifier}'. Use 'list tasks' to see all tasks."
        
        # Remove the task
        tasks.pop(task_index)
        _save_tasks(tasks)
        
        return f"🗑️ Deleted task #{task_to_delete['id']}: '{task_to_delete['description']}'"
        
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        return f"Sorry, I couldn't delete the task '{task_identifier}'. Please try again."
