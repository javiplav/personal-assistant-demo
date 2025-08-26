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
import random
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from filelock import FileLock
from ._paths import data_path

logger = logging.getLogger(__name__)

# Path to the tasks file
TASKS_FILE = data_path("tasks.json")
_TASKS_LOCK = FileLock(str(TASKS_FILE) + ".lock")


def _load_tasks() -> List[Dict[str, Any]]:
    """Load tasks from the JSON file."""
    try:
        with _TASKS_LOCK:
            if TASKS_FILE.exists():
                return json.loads(TASKS_FILE.read_text(encoding="utf-8"))
            return []
    except Exception as e:
        logger.error(f"Error loading tasks: {e}")
        return []


def _save_tasks(tasks: List[Dict[str, Any]]) -> None:
    """Save tasks to the JSON file."""
    try:
        # Ensure the data directory exists
        TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with _TASKS_LOCK:
            TASKS_FILE.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
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
        
        # Return structured JSON response
        if client_name:
            response_data = {
                "success": True,
                "task_id": task_id,
                "description": description,
                "client_name": client_name,
                "message": f"Added task #{task_id} for {client_name}: '{description}'"
            }
        else:
            response_data = {
                "success": True,
                "task_id": task_id,
                "description": description,
                "message": f"Added task #{task_id}: '{description}'"
            }
        return json.dumps(response_data)
        
    except Exception as e:
        logger.error(f"Error adding task: {e}")
        return json.dumps({
            "success": False,
            "error": f"Couldn't add the task '{description}'. Please try again."
        })


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
            return json.dumps({
                "success": True,
                "tasks": [],
                "message": "You have no tasks yet. Add one by saying 'Add a task to...' or 'Create a task to...'"
            })
        
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
            message = f"No tasks found{filter_description}." if filter_description else "You have no tasks yet."
            return json.dumps({
                "success": True,
                "tasks": [],
                "filter": filter_description.strip() if filter_description else None,
                "message": message
            })
        
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
        
        return json.dumps({
            "success": True,
            "pending_tasks": [{"id": t["id"], "description": t["description"], "client_name": t.get("client_name")} for t in pending_tasks],
            "completed_tasks": [{"id": t["id"], "description": t["description"], "client_name": t.get("client_name")} for t in completed_tasks],
            "filter": filter_description.strip() if filter_description else None,
            "message": "\n".join(result)
        })
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return json.dumps({
            "success": False,
            "error": "Sorry, I couldn't retrieve your tasks. Please try again."
        })


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
            return json.dumps({
                "success": False,
                "error": "You have no tasks to complete."
            })
        
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
            return json.dumps({
                "success": False,
                "error": f"Couldn't find a task matching '{task_identifier}'. Use 'list tasks' to see all tasks."
            })
        
        if task_to_complete["completed"]:
            return json.dumps({
                "success": True,
                "task_id": task_to_complete['id'],
                "description": task_to_complete['description'],
                "already_completed": True,
                "message": f"Task #{task_to_complete['id']} is already completed: '{task_to_complete['description']}'"
            })
        
        # Mark as completed
        task_to_complete["completed"] = True
        task_to_complete["completed_at"] = datetime.now().isoformat()
        
        _save_tasks(tasks)
        
        return json.dumps({
            "success": True,
            "task_id": task_to_complete['id'],
            "description": task_to_complete['description'],
            "completed_at": task_to_complete['completed_at'],
            "message": f"Completed task #{task_to_complete['id']}: '{task_to_complete['description']}'"
        })
        
    except Exception as e:
        logger.error(f"Error completing task: {e}")
        return json.dumps({
            "success": False,
            "error": f"Couldn't complete the task '{task_identifier}'. Please try again."
        })


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
            return json.dumps({
                "success": False,
                "error": "You have no tasks to delete."
            })
        
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
            return json.dumps({
                "success": False,
                "error": f"Couldn't find a task matching '{task_identifier}'. Use 'list tasks' to see all tasks."
            })
        
        # Remove the task
        tasks.pop(task_index)
        _save_tasks(tasks)
        
        return json.dumps({
            "success": True,
            "task_id": task_to_delete['id'],
            "description": task_to_delete['description'],
            "message": f"Deleted task #{task_to_delete['id']}: '{task_to_delete['description']}'"
        })
        
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        return json.dumps({
            "success": False,
            "error": f"Couldn't delete the task '{task_identifier}'. Please try again."
        })


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
    import json
    
    try:
        clients_file = data_path("clients.json")
        clients_lock = FileLock(str(clients_file) + ".lock")
        if clients_file.exists():
            with clients_lock:
                clients = json.loads(clients_file.read_text(encoding="utf-8"))
            
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


def _load_clients() -> List[Dict[str, Any]]:
    """Load clients from the clients JSON file."""
    try:
        clients_file = data_path("clients.json")
        clients_lock = FileLock(str(clients_file) + ".lock")
        if clients_file.exists():
            with clients_lock:
                return json.loads(clients_file.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"Error loading clients: {e}")
    return []


async def assign_random_clients_to_unassigned_tasks(force_reassign: str = "false") -> str:
    """
    Assign random clients to tasks that don't have a specific client name assigned.
    This helps ensure all tasks are associated with a client for better organization.
    
    Args:
        force_reassign: Set to "true" to reassign clients even if tasks already have assignments (optional)
    
    Returns:
        A JSON string with the results of the assignment operation
    """
    try:
        # Load tasks and clients
        tasks = _load_tasks()
        clients = _load_clients()
        
        if not clients:
            return json.dumps({
                "success": False,
                "error": "No clients available for assignment. Please add some clients first."
            })
        
        # Find tasks without client assignments
        unassigned_tasks = []
        should_force_reassign = force_reassign.lower() == "true"
        
        for task in tasks:
            # A task is considered unassigned if it has no client_name or client_name is null/empty
            # OR if force_reassign is true
            if should_force_reassign or not task.get("client_name") or task.get("client_name") in [None, "", "null"]:
                unassigned_tasks.append(task)
        
        if not unassigned_tasks:
            return json.dumps({
                "success": True,
                "assignments_made": 0,
                "message": "All tasks already have client assignments."
            })
        
        # Assign random clients to unassigned tasks
        assignments_made = []
        
        for task in unassigned_tasks:
            # Pick a random client
            random_client = random.choice(clients)
            
            # Update task with client information
            task["client_name"] = random_client["name"]
            task["client_id"] = random_client["id"]
            
            assignments_made.append({
                "task_id": task["id"],
                "task_description": task["description"],
                "assigned_client": random_client["name"],
                "client_id": random_client["id"]
            })
            
            logger.info(f"Assigned task #{task['id']} ('{task['description']}') to client {random_client['name']} (ID: {random_client['id']})")
        
        # Save updated tasks
        _save_tasks(tasks)
        
        return json.dumps({
            "success": True,
            "assignments_made": len(assignments_made),
            "assignments": assignments_made,
            "message": f"Successfully assigned {len(assignments_made)} tasks to random clients."
        })
        
    except Exception as e:
        logger.error(f"Error assigning random clients to tasks: {e}")
        return json.dumps({
            "success": False,
            "error": f"Failed to assign clients to tasks: {str(e)}"
        })
