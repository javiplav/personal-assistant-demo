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


async def add_task(description: str, client_name: str = "", client_id: str = "") -> str:
    """
    Add a new task to the task list, optionally associated with a client.
    
    Args:
        description: Description of the task to add
        client_name: Name of the client this task is for (optional)
        client_id: ID of the client this task is for (optional)
        
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
            "client_name": client_name.strip() if client_name else None,
            "client_id": int(client_id) if client_id and client_id.isdigit() else None,
            "completed": False,
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        }
        
        tasks.append(new_task)
        _save_tasks(tasks)
        
        # Format response based on client association
        if client_name:
            return f"✅ Added task #{task_id} for {client_name}: '{description}'"
        else:
            return f"✅ Added task #{task_id}: '{description}'"
        
    except Exception as e:
        logger.error(f"Error adding task: {e}")
        return f"Sorry, I couldn't add the task '{description}'. Please try again."


async def list_tasks(query: str = "", client_name: str = "", client_id: str = "") -> str:
    """
    List tasks with optional filtering by client or query.
    
    Args:
        query: Optional search query to filter tasks
        client_name: Filter tasks for specific client by name
        client_id: Filter tasks for specific client by ID
    
    Returns:
        A formatted string showing filtered or all tasks
    """
    try:
        tasks = _load_tasks()
        
        if not tasks:
            return "📝 You have no tasks yet. Add one by saying 'Add a task to...' or 'Create a task to...'"
        
        # Apply filtering
        filtered_tasks = tasks
        filter_description = ""
        
        if client_name:
            client_lower = client_name.lower()
            filtered_tasks = [t for t in filtered_tasks if t.get("client_name") and client_lower in t["client_name"].lower()]
            filter_description = f" for client '{client_name}'"
        elif client_id and client_id.isdigit():
            filtered_tasks = [t for t in filtered_tasks if t.get("client_id") == int(client_id)]
            filter_description = f" for client ID {client_id}"
        elif query:
            query_lower = query.lower()
            filtered_tasks = [t for t in filtered_tasks if query_lower in t["description"].lower()]
            filter_description = f" matching '{query}'"
        
        if not filtered_tasks:
            if filter_description:
                return f"📝 No tasks found{filter_description}."
            else:
                return "📝 You have no tasks yet."
        
        # Separate completed and pending tasks, sorted by ID
        pending_tasks = sorted([task for task in filtered_tasks if not task["completed"]], key=lambda x: x["id"])
        completed_tasks = sorted([task for task in filtered_tasks if task["completed"]], key=lambda x: x["id"])
        
        # Build result with client information
        if filter_description:
            result = [f"Here are your tasks{filter_description}:"]
        else:
            result = ["Here are all your tasks:"]
        
        if pending_tasks:
            result.append("\n📋 **Pending Tasks:**")
            for task in pending_tasks:
                client_info = f" (for {task['client_name']})" if task.get('client_name') else ""
                result.append(f"  • #{task['id']}: {task['description']}{client_info}")
        
        if completed_tasks:
            result.append("\n✅ **Completed Tasks:**")
            for task in completed_tasks:
                client_info = f" (for {task['client_name']})" if task.get('client_name') else ""
                result.append(f"  • #{task['id']}: {task['description']}{client_info}")
        
        if not pending_tasks and completed_tasks and not filter_description:
            result.insert(1, "\n🎉 All tasks completed!")
        
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


async def list_tasks_for_client(client_name: str) -> str:
    """
    List all tasks for a specific client.
    
    Args:
        client_name: Name of the client to filter tasks for
        
    Returns:
        A formatted string showing tasks for the specified client
    """
    return await list_tasks(client_name=client_name)


async def add_client_task(client_name: str, task_description: str) -> str:
    """
    Add a task for a specific client.
    
    Args:
        client_name: Name of the client this task is for
        task_description: Description of the task
        
    Returns:
        Confirmation message about the added task
    """
    # Find client ID by name
    from pathlib import Path
    import json
    
    try:
        clients_file = Path("data/clients.json")
        if clients_file.exists():
            with open(clients_file, "r") as f:
                clients = json.load(f)
            
            # Find matching client
            client_id = None
            for client in clients:
                if client["name"].lower() == client_name.lower():
                    client_id = str(client["id"])
                    break
            
            return await add_task(task_description, client_name, client_id)
        else:
            return await add_task(task_description, client_name)
    except Exception as e:
        logger.error(f"Error adding client task: {e}")
        return await add_task(task_description, client_name)
