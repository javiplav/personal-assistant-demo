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
_CLIENTS_LOCK = FileLock(str(CLIENTS_FILE) + ".lock", timeout=5)


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
        
        # DEBUG: Log the actual filter parameter being passed
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"list_clients called with filters: '{filters}' (type: {type(filters)})")

        if filters and filters.strip():
            filters_lower = filters.lower().strip()
            logger.info(f"Normalized filters: '{filters_lower}'")
            
            # Define valid priority values
            valid_priorities = ["high", "medium", "low"]

            # FIXED: Much more restrictive filtering to avoid false positives
            priority_filter = None
            
            # Only filter if the filter string exactly matches expected patterns
            if filters_lower in valid_priorities:
                priority_filter = filters_lower
            elif filters_lower in [f"{p}-priority" for p in valid_priorities]:
                priority_filter = filters_lower.replace("-priority", "")
            elif filters_lower in [f"{p}priority" for p in valid_priorities]:
                priority_filter = filters_lower.replace("priority", "")
            elif filters_lower == "active":
                # Keep active filtering as-is
                filtered_clients = [c for c in clients if c.get("status", "active").lower() == "active"]
                filter_message = " (active only)"
                
            if priority_filter:
                logger.info(f"Applying priority filter: {priority_filter}")
                # Filter for specific priority clients
                filtered_clients = [c for c in clients if c.get("priority", "medium").lower() == priority_filter]
                filter_message = f" ({priority_filter} priority only)"
            elif filters_lower not in ["active"] and not priority_filter:
                # If filters provided but don't match any expected pattern, log warning but show all
                logger.warning(f"Unrecognized filter '{filters_lower}' - showing all clients")
                filter_message = " (filter not recognized, showing all)"

        # DEBUG: Log counts before processing
        logger.info(f"Total clients loaded: {len(clients)}")
        logger.info(f"Clients after filtering: {len(filtered_clients)}")
        
        # Sort by priority (high first) then by name
        priority_order = {"high": 1, "medium": 2, "low": 3}
        filtered_clients.sort(key=lambda x: (priority_order.get(x.get("priority", "medium"), 2), x["name"]))

        # Project to a compact representation to keep downstream LLM prompts small
        def _project_client(c: Dict[str, Any]) -> Dict[str, Any]:
            email = c.get("email", "").strip()
            # Provide clear indication when email is missing or placeholder
            if not email or email in ["no_email_provided", "PLEASE RESPOND WITH A VALID EMAIL ADDRESS FOR NETFLIX"]:
                email_display = "(no email set)"
            else:
                email_display = email
                
            return {
                "id": c.get("id"),
                "name": c.get("name"),
                "company": c.get("company"),
                "priority": c.get("priority", "medium"),
                "status": c.get("status", "active"),
                "email": email_display
            }

        slim_clients = [_project_client(c) for c in filtered_clients]
        
        # DEBUG: Log final count and client names
        logger.info(f"Final projected clients count: {len(slim_clients)}")
        logger.info(f"Client names: {[c['name'] for c in slim_clients]}")

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


async def update_client_email(client_identifier: str, email: str) -> Dict[str, Any]:
    """
    Update a client's email by ID or name.

    Accepts either a numeric client ID (e.g., "3") or a client name (partial match allowed).
    Validates basic email format and saves the change.
    """
    try:
        clients = _load_clients()

        if not clients:
            return json.dumps({
                "success": False,
                "error": "No clients found."
            })

        identifier = (client_identifier or "").strip()
        if not identifier:
            return json.dumps({
                "success": False,
                "error": "Client identifier is required."
            })

        # Basic email validation (very permissive)
        email_value = (email or "").strip()
        if not email_value or "@" not in email_value or "." not in email_value.split("@")[-1]:
            return json.dumps({
                "success": False,
                "error": "Please provide a valid email address."
            })

        target_client = None

        if identifier.isdigit():
            target_id = int(identifier)
            for c in clients:
                if c.get("id") == target_id:
                    target_client = c
                    break
        else:
            ident_lower = identifier.lower()
            matches = [c for c in clients if ident_lower in str(c.get("name", "")).lower()]
            if len(matches) == 1:
                target_client = matches[0]
            elif len(matches) > 1:
                return json.dumps({
                    "success": False,
                    "error": f"Multiple clients found matching '{client_identifier}'. Please use the client ID."
                })

        if not target_client:
            return json.dumps({
                "success": False,
                "error": f"Client '{client_identifier}' not found."
            })

        old_email = target_client.get("email", "")
        
        # Check if email is already set to the requested value
        if old_email == email_value:
            return json.dumps({
                "success": True,
                "client_id": target_client.get("id"),
                "client_name": target_client.get("name"),
                "old_email": old_email,
                "new_email": email_value,
                "no_change_needed": True,
                "message": f"Email for {target_client.get('name')} (ID: {target_client.get('id')}) is already set to {email_value}. No update needed."
            })
        
        target_client["email"] = email_value
        target_client["last_contact"] = datetime.now().isoformat()

        _save_clients(clients)

        return json.dumps({
            "success": True,
            "client_id": target_client.get("id"),
            "client_name": target_client.get("name"),
            "old_email": old_email,
            "new_email": email_value,
            "message": f"Updated email for {target_client.get('name')} (ID: {target_client.get('id')}) from '{old_email}' to '{email_value}'."
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to update client email: {str(e)}"
        })
