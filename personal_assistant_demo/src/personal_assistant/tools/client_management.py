"""
Client Management Tool for Personal Assistant Demo.

This tool demonstrates CRM and project management capabilities that solutions architects
need for managing client relationships, tracking projects, and maintaining professional
communication records.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict
from pathlib import Path
from filelock import FileLock
from ._paths import data_path

# Standardized file path and lock
CLIENTS_FILE = data_path("clients.json")
_CLIENTS_LOCK = FileLock(str(CLIENTS_FILE) + ".lock")


def _load_clients():
    """Load clients from the JSON file with proper locking."""
    with _CLIENTS_LOCK:
        return json.loads(CLIENTS_FILE.read_text(encoding="utf-8")) if CLIENTS_FILE.exists() else []


def _save_clients(data):
    """Save clients to the JSON file with proper locking."""
    with _CLIENTS_LOCK:
        CLIENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        CLIENTS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")




async def add_client(
    name: str,
    company: str,
    email: str = "",
    phone: str = "",
    project_requirements: str = "",
    priority: str = "medium"
) -> Dict[str, Any]:
    """
    Add a new client to the CRM system.
    
    This function demonstrates enterprise CRM capabilities that solutions architects
    use to manage client relationships and track project opportunities.
    """
    try:
        # Validate priority value
        valid_priorities = ["high", "medium", "low"]
        if priority.lower() not in valid_priorities:
                    return json.dumps({
            "success": False,
            "error": f"Invalid priority value. Must be one of: {', '.join(valid_priorities)}"
        })
        
        # Load existing clients
        clients = _load_clients()
        
        # Check if client already exists by email (if provided) or (name and company)
        for client in clients:
            if email and client["email"] == email:
                return json.dumps({
                    "success": False,
                    "error": f"Client with email {email} already exists."
                })
            if client["name"].lower() == name.lower() and client["company"].lower() == company.lower():
                return json.dumps({
                    "success": False,
                    "error": f"Client '{name}' from company '{company}' already exists."
                })
        
        # Generate client ID - find max ID and increment
        client_id = max([c["id"] for c in clients], default=0) + 1
        
        # Create client object
        client = {
            "id": client_id,
            "name": name,
            "email": email,
            "company": company,
            "phone": phone,
            "project_requirements": project_requirements,
            "priority": priority,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "last_contact": datetime.now().isoformat(),
            "notes": []
        }
        
        clients.append(client)
        
        # Save to file
        _save_clients(clients)
        
        return json.dumps({
            "success": True,
            "client_id": client_id,
            "name": name,
            "company": company,
            "message": f"Client '{name}' from {company} added successfully with ID {client_id}."
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to add client: {str(e)}"
        })


async def list_clients(filters: str = "") -> Dict[str, Any]:
    """
    List all clients with optional filtering.
    Supports filtering by priority: 'high', 'medium', 'low', or 'high-priority'
    """
    try:
        clients = _load_clients()

        if not clients:
            return json.dumps({
                "success": True,
                "clients": [],
                "count": 0,
                "message": "No clients found."
            })

        # Apply filtering based on the filters parameter
        filtered_clients = clients
        filter_message = ""

        if filters:
            filters_lower = filters.lower()
            # Define valid priority values
            valid_priorities = ["high", "medium", "low"]

            # Extract priority from filters - use precise matching to avoid false positives
            priority_filter = None
            for priority in valid_priorities:
                if (
                    filters_lower == priority or
                    f"{priority} priority" in filters_lower or
                    f"{priority}-priority" in filters_lower or
                    filters_lower == f"{priority}priority"  # Handle "highpriority" etc.
                ):
                    priority_filter = priority
                    break

            if priority_filter:
                # Filter for specific priority clients
                filtered_clients = [c for c in clients if c.get("priority", "medium").lower() == priority_filter]
                filter_message = f" ({priority_filter} priority only)"
            elif "active" in filters_lower:
                # Filter for active clients only
                filtered_clients = [c for c in clients if c.get("status", "active").lower() == "active"]
                filter_message = " (active only)"

        # Sort by priority (high first) then by name
        priority_order = {"high": 1, "medium": 2, "low": 3}
        filtered_clients.sort(key=lambda x: (priority_order.get(x.get("priority", "medium"), 2), x["name"]))

        # Project to a compact representation to keep downstream LLM prompts small
        def _project_client(c: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "id": c.get("id"),
                "name": c.get("name"),
                "company": c.get("company"),
                "priority": c.get("priority", "medium"),
                "status": c.get("status", "active"),
                "email": c.get("email", "")
            }

        slim_clients = [_project_client(c) for c in filtered_clients]

        return json.dumps({
            "success": True,
            "clients": slim_clients,
            "count": len(slim_clients),
            "message": f"Found {len(slim_clients)} client(s){filter_message}."
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to list clients: {str(e)}"
        })


async def find_client_by_name(name: str) -> Dict[str, Any]:
    """
    Find a client by name and return their details.
    """
    try:
        clients = _load_clients()
        
        if not clients:
            return json.dumps({
                "success": False,
                "error": "No clients found."
            })
        
        # Search for client by name (case-insensitive partial match)
        matches = []
        name_lower = name.lower()
        
        for client in clients:
            if name_lower in client["name"].lower():
                matches.append(client)
        
        if len(matches) == 0:
            return json.dumps({
                "success": False,
                "error": f"No client found matching '{name}'."
            })
        elif len(matches) == 1:
            return json.dumps({
                "success": True,
                "client": matches[0],
                "message": f"Found client: {matches[0]['name']} (ID: {matches[0]['id']})"
            })
        else:
            return json.dumps({
                "success": True,
                "multiple_matches": True,
                "clients": matches,
                "message": f"Found {len(matches)} clients matching '{name}'"
            })
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to search for client: {str(e)}"
        })


async def add_client_note(
    client_identifier: str,
    note: str,
    note_type: str = "general"
) -> Dict[str, Any]:
    """
    Add a note to a client's profile. Can use client ID (as string) or client name.
    """
    try:
        clients = _load_clients()
        
        if not clients:
            return json.dumps({
                "success": False,
                "error": "No clients found."
            })
        
        # Determine if identifier is an ID or name
        target_client = None
        if client_identifier.isdigit():
            # It's a client ID
            client_id = int(client_identifier)
            for client in clients:
                if client["id"] == client_id:
                    target_client = client
                    break
        else:
            # It's a name, find the client
            identifier_lower = client_identifier.lower()
            matches = []
            for client in clients:
                if identifier_lower in client["name"].lower():
                    matches.append(client)
            
            if len(matches) == 1:
                target_client = matches[0]
            elif len(matches) > 1:
                return json.dumps({
                    "success": False,
                    "error": f"Multiple clients found matching '{client_identifier}'. Please be more specific or use client ID."
                })
            elif len(matches) == 0:
                return json.dumps({
                    "success": False,
                    "error": f"No client found matching '{client_identifier}'."
                })
        
        if not target_client:
            return json.dumps({
                "success": False,
                "error": f"Client '{client_identifier}' not found."
            })
        
        # Add note to the found client
        note_entry = {
            "id": len(target_client["notes"]) + 1,
            "content": note,
            "type": note_type,
            "created_at": datetime.now().isoformat()
        }
        target_client["notes"].append(note_entry)
        target_client["last_contact"] = datetime.now().isoformat()
        
        # Save updated clients
        _save_clients(clients)
        
        return json.dumps({
            "success": True,
            "client_id": target_client["id"],
            "client_name": target_client["name"],
            "note_id": note_entry["id"],
            "message": f"Note '{note}' added successfully to {target_client['name']} (ID: {target_client['id']})."
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to add note: {str(e)}"
        })


async def get_client_details(client_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific client by ID or name.

    Accepts either a numeric client ID (e.g., "1") or a client name
    (e.g., "Sarah Johnson"). If a name matches multiple clients, returns
    multiple candidates for disambiguation.
    """
    try:
        clients = _load_clients()

        if not clients:
            return json.dumps({
                "success": False,
                "error": "No clients found."
            })

        identifier = str(client_id) if client_id is not None else ""

        # Numeric ID path
        if identifier.isdigit():
            target_id = int(identifier)
            for client in clients:
                if client.get("id") == target_id:
                    return json.dumps({
                        "success": True,
                        "client": client,
                        "message": f"Retrieved details for client {target_id}."
                    })
            return json.dumps({
                "success": False,
                "error": f"Client with ID {target_id} not found."
            })

        # Name-based path (case-insensitive partial match)
        identifier_lower = identifier.lower().strip()
        matches = []
        for client in clients:
            if identifier_lower in str(client.get("name", "")).lower():
                matches.append(client)

        if len(matches) == 0:
            return json.dumps({
                "success": False,
                "error": f"No client found matching '{identifier}'."
            })
        elif len(matches) == 1:
            client = matches[0]
            return json.dumps({
                "success": True,
                "client": client,
                "message": f"Retrieved details for client {client.get('name')} (ID: {client.get('id')})."
            })
        else:
            return json.dumps({
                "success": True,
                "multiple_matches": True,
                "clients": matches,
                "message": f"Found {len(matches)} clients matching '{identifier}'. Please specify the ID."
            })

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to get client details: {str(e)}"
        })
