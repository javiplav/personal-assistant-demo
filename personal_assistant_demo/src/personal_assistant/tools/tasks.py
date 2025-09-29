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
import tempfile
import shutil
import uuid
import time
import functools
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from filelock import FileLock
from ._paths import data_path

logger = logging.getLogger(__name__)

# Path to the tasks file
TASKS_FILE = data_path("tasks.json")
_TASKS_LOCK = FileLock(str(TASKS_FILE) + ".lock")


class TaskError(Exception):
    """Custom exception for task-related errors."""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code or "TASK_ERROR"
        super().__init__(message)


def _validate_task_input(description: str, client_name: str = "", status: str = "") -> None:
    """Validate task input parameters."""
    if not description or not description.strip():
        raise TaskError("Task description cannot be empty", "INVALID_DESCRIPTION")
    
    if len(description.strip()) > 500:
        raise TaskError("Task description too long (max 500 characters)", "DESCRIPTION_TOO_LONG")
    
    if client_name and len(client_name.strip()) > 100:
        raise TaskError("Client name too long (max 100 characters)", "CLIENT_NAME_TOO_LONG")
    
    if status and status not in ['completed', 'pending']:
        raise TaskError("Status must be 'completed', 'pending', or empty", "INVALID_STATUS")


def _generate_task_id() -> str:
    """Generate a unique task ID using UUID."""
    return str(uuid.uuid4())[:8]  # Use first 8 chars for readability


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


# Performance monitoring and caching
_task_cache = {}
_cache_timestamps = {}
CACHE_TTL = 30  # seconds


def measure_performance(func: Callable) -> Callable:
    """Decorator to measure and log function performance."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = func.__name__
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log performance metrics
            if execution_time > 1.0:  # Log slow operations
                logger.warning(f"{function_name} took {execution_time:.2f}s (slow)")
            else:
                logger.info(f"{function_name} completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{function_name} failed after {execution_time:.2f}s: {e}")
            raise
    
    return wrapper


def _get_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate cache key from function name and arguments."""
    # Create a deterministic string from args and kwargs
    args_str = str(args) + str(sorted(kwargs.items()))
    return f"{func_name}:{hash(args_str)}"


def _is_cache_valid(cache_key: str) -> bool:
    """Check if cached data is still valid."""
    if cache_key not in _cache_timestamps:
        return False
    
    timestamp = _cache_timestamps[cache_key]
    return (time.time() - timestamp) < CACHE_TTL


def _get_from_cache(cache_key: str) -> Optional[str]:
    """Get data from cache if valid."""
    if _is_cache_valid(cache_key) and cache_key in _task_cache:
        logger.info(f"Cache hit for {cache_key[:20]}...")
        return _task_cache[cache_key]
    return None


def _set_cache(cache_key: str, data: str) -> None:
    """Set data in cache with timestamp."""
    _task_cache[cache_key] = data
    _cache_timestamps[cache_key] = time.time()
    
    # Simple cache size management - keep last 50 entries
    if len(_task_cache) > 50:
        oldest_key = min(_cache_timestamps.keys(), key=lambda k: _cache_timestamps[k])
        del _task_cache[oldest_key]
        del _cache_timestamps[oldest_key]


def _invalidate_task_cache() -> None:
    """Clear task-related cache when data changes."""
    keys_to_remove = [k for k in _task_cache.keys() if k.startswith('list_tasks')]
    for key in keys_to_remove:
        _task_cache.pop(key, None)
        _cache_timestamps.pop(key, None)
    logger.info(f"Invalidated {len(keys_to_remove)} cache entries")


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
    """Save tasks to the JSON file atomically."""
    try:
        # Ensure the data directory exists
        TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with _TASKS_LOCK:
            # Write to temp file first for atomic operation
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tmp', 
                                           dir=TASKS_FILE.parent, delete=False, 
                                           encoding='utf-8') as tmp_file:
                json.dump(tasks, tmp_file, indent=2)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())  # Force write to disk
                tmp_file_path = tmp_file.name
            
            # Atomic move
            shutil.move(tmp_file_path, TASKS_FILE)
            
    except Exception as e:
        logger.error(f"Error saving tasks: {e}")
        # Clean up temp file if it exists
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            try:
                os.remove(tmp_file_path)
            except:
                pass
        raise TaskError(f"Failed to save tasks: {str(e)}", "SAVE_FAILED")


@measure_performance
async def add_task(description: str, client_name: str = "", client_id: str = "") -> str:
    """
    Add a new task to the task list, optionally associated with a client.
    
    Args:
        description: Description of the task to add
        client_name: Name of the client this task is for (optional)
        client_id: ID of the client this task is for (optional)
        
    Returns:
        JSON string with standardized response format
    """
    try:
        # Input validation
        _validate_task_input(description, client_name)
        
        tasks = _load_tasks()
        
        # Generate unique ID
        task_id = _generate_task_id()
        
        # Ensure ID is unique (unlikely but possible with UUID truncation)
        existing_ids = {task.get("id") for task in tasks}
        while task_id in existing_ids:
            task_id = _generate_task_id()
        
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
        
        # Invalidate cache since data changed
        _invalidate_task_cache()
        
        # Create response data
        response_data = {
            "task_id": task_id,
            "description": description.strip(),
            "client_name": client_name.strip() if client_name else None,
            "created_at": new_task["created_at"]
        }
        
        if client_name:
            message = f"Added task {task_id} for {client_name}: '{description.strip()}'"
        else:
            message = f"Added task {task_id}: '{description.strip()}'"
        
        return _create_standard_response(
            success=True,
            data=response_data,
            message=message
        )
        
    except TaskError as e:
        return _create_standard_response(
            success=False,
            error=e.message,
            error_code=e.error_code
        )
    except Exception as e:
        logger.error(f"Unexpected error adding task: {e}")
        return _create_standard_response(
            success=False,
            error="Internal error occurred while adding task",
            error_code="INTERNAL_ERROR"
        )


@measure_performance
async def list_tasks(query: str = "", client_name: str = "", client_id: str = "", status: str = "") -> str:
    """
    List tasks with optional filtering by client, query, or completion status.
    
    Args:
        query: Optional search query to filter tasks
        client_name: Filter tasks for specific client by name
        client_id: Filter tasks for specific client by ID
        status: Filter by completion status ('completed', 'pending', or '' for all)
    
    Returns:
        A formatted string showing filtered or all tasks
    """
    try:
        # Check cache first for read-heavy operations
        cache_key = _get_cache_key("list_tasks", (query, client_name, client_id, status), {})
        cached_result = _get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Input validation
        if status:
            _validate_task_input("dummy", "", status)  # Only validate status
        
        tasks = _load_tasks()
        
        if not tasks:
            return _create_standard_response(
                success=True,
                data={"tasks": [], "total_count": 0, "pending_count": 0, "completed_count": 0},
                message="You have no tasks yet. Add one by saying 'Add a task to...' or 'Create a task to...'"
            )
        
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
        
        # Apply status filtering
        if status and status.lower() in ["completed", "pending"]:
            is_completed = status.lower() == "completed"
            filtered_tasks = [t for t in filtered_tasks if t["completed"] == is_completed]
            if filter_description:
                filter_description += f" ({status.lower()})"
            else:
                filter_description = f" ({status.lower()} only)"
        
        if not filtered_tasks:
            message = f"No tasks found{filter_description}." if filter_description else "You have no tasks yet."
            return _create_standard_response(
                success=True,
                data={"tasks": [], "total_count": 0, "pending_count": 0, "completed_count": 0, "filter": filter_description.strip() if filter_description else None},
                message=message
            )
        
        # Separate completed and pending tasks, sorted by creation date (most recent first)
        pending_tasks = sorted([task for task in filtered_tasks if not task["completed"]], 
                              key=lambda x: x.get("created_at", ""), reverse=True)
        completed_tasks = sorted([task for task in filtered_tasks if task["completed"]], 
                                key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Build result with client information
        if filter_description:
            result = [f"Here are your tasks{filter_description}:"]
        else:
            result = ["Here are all your tasks:"]
        
        # Show appropriate sections based on status filter
        show_completed_only = status and status.lower() == "completed"
        show_pending_only = status and status.lower() == "pending"
        
        if pending_tasks and not show_completed_only:
            result.append("\n📋 **Pending Tasks:**")
            for task in pending_tasks:
                client_info = f" (for {task['client_name']})" if task.get('client_name') else ""
                result.append(f"  • {task['id']}: {task['description']}{client_info}")
        
        if completed_tasks and not show_pending_only:
            result.append("\n✅ **Completed Tasks:**")
            for task in completed_tasks:
                client_info = f" (for {task['client_name']})" if task.get('client_name') else ""
                result.append(f"  • {task['id']}: {task['description']}{client_info}")
        
        if not pending_tasks and completed_tasks and not filter_description:
            result.insert(1, "\n🎉 All tasks completed!")
        
        # Create response data
        response_data = {
            "tasks": filtered_tasks,
            "pending_tasks": [{"id": t["id"], "description": t["description"], "client_name": t.get("client_name")} for t in pending_tasks],
            "completed_tasks": [{"id": t["id"], "description": t["description"], "client_name": t.get("client_name")} for t in completed_tasks],
            "total_count": len(filtered_tasks),
            "pending_count": len(pending_tasks),
            "completed_count": len(completed_tasks),
            "filter": filter_description.strip() if filter_description else None
        }
        
        result_json = _create_standard_response(
            success=True,
            data=response_data,
            message="\n".join(result)
        )
        
        # Cache the result for future requests
        _set_cache(cache_key, result_json)
        return result_json
        
    except TaskError as e:
        return _create_standard_response(
            success=False,
            error=e.message,
            error_code=e.error_code
        )
    except Exception as e:
        logger.error(f"Unexpected error listing tasks: {e}")
        return _create_standard_response(
            success=False,
            error="Internal error occurred while retrieving tasks",
            error_code="INTERNAL_ERROR"
        )


@measure_performance
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
        
        # Invalidate cache since task status changed
        _invalidate_task_cache()
        
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


