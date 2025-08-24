"""
Client Management Tool for Personal Assistant Demo.

This tool demonstrates CRM and project management capabilities that solutions architects
need for managing client relationships, tracking projects, and maintaining professional
communication records.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path




async def add_client(
    name: str,
    email: str,
    company: str,
    phone: Optional[str] = None,
    project_requirements: Optional[str] = None,
    priority: str = "medium"
) -> Dict[str, Any]:
    """
    Add a new client to the CRM system.
    
    This function demonstrates enterprise CRM capabilities that solutions architects
    use to manage client relationships and track project opportunities.
    """
    try:
        # Load existing clients
        clients_file = Path("data/clients.json")
        clients_file.parent.mkdir(exist_ok=True)
        
        if clients_file.exists():
            with open(clients_file, "r") as f:
                clients = json.load(f)
        else:
            clients = []
        
        # Check if client already exists
        for client in clients:
            if client["email"] == email:
                return {
                    "success": False,
                    "error": f"Client with email {email} already exists."
                }
        
        # Generate client ID
        client_id = len(clients) + 1
        
        # Create client object
        client = {
            "id": client_id,
            "name": name,
            "email": email,
            "company": company,
            "phone": phone or "",
            "project_requirements": project_requirements or "",
            "priority": priority,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "last_contact": datetime.now().isoformat(),
            "notes": []
        }
        
        clients.append(client)
        
        # Save to file
        with open(clients_file, "w") as f:
            json.dump(clients, f, indent=2)
        
        return {
            "success": True,
            "client_id": client_id,
            "name": name,
            "company": company,
            "message": f"Client '{name}' from {company} added successfully with ID {client_id}."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to add client: {str(e)}"
        }


async def list_clients(
    company: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all clients with optional filtering.
    """
    try:
        clients_file = Path("data/clients.json")
        
        if not clients_file.exists():
            return {
                "success": True,
                "clients": [],
                "message": "No clients found."
            }
        
        with open(clients_file, "r") as f:
            clients = json.load(f)
        
        # Apply filters
        filtered_clients = []
        for client in clients:
            # Company filter
            if company and company.lower() not in client["company"].lower():
                continue
            
            # Priority filter
            if priority and client.get("priority") != priority:
                continue
            
            # Status filter
            if status and client.get("status") != status:
                continue
            
            filtered_clients.append(client)
        
        # Sort by priority (high first) then by name
        priority_order = {"high": 1, "medium": 2, "low": 3}
        filtered_clients.sort(key=lambda x: (priority_order.get(x.get("priority", "medium"), 2), x["name"]))
        
        return {
            "success": True,
            "clients": filtered_clients,
            "count": len(filtered_clients),
            "message": f"Found {len(filtered_clients)} client(s)."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list clients: {str(e)}"
        }


async def add_client_note(
    client_id: int,
    note: str,
    note_type: str = "general"
) -> Dict[str, Any]:
    """
    Add a note to a client's profile.
    """
    try:
        clients_file = Path("data/clients.json")
        
        if not clients_file.exists():
            return {
                "success": False,
                "error": "No clients found."
            }
        
        with open(clients_file, "r") as f:
            clients = json.load(f)
        
        # Find client and add note
        client_found = False
        for client in clients:
            if client["id"] == client_id:
                note_entry = {
                    "id": len(client["notes"]) + 1,
                    "content": note,
                    "type": note_type,
                    "created_at": datetime.now().isoformat()
                }
                client["notes"].append(note_entry)
                client["last_contact"] = datetime.now().isoformat()
                client_found = True
                break
        
        if not client_found:
            return {
                "success": False,
                "error": f"Client with ID {client_id} not found."
            }
        
        # Save updated clients
        with open(clients_file, "w") as f:
            json.dump(clients, f, indent=2)
        
        return {
            "success": True,
            "client_id": client_id,
            "note_id": len(clients[client_id - 1]["notes"]),
            "message": f"Note added successfully to client {client_id}."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to add note: {str(e)}"
        }


async def get_client_details(client_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a specific client.
    """
    try:
        clients_file = Path("data/clients.json")
        
        if not clients_file.exists():
            return {
                "success": False,
                "error": "No clients found."
            }
        
        with open(clients_file, "r") as f:
            clients = json.load(f)
        
        # Find client
        for client in clients:
            if client["id"] == client_id:
                return {
                    "success": True,
                    "client": client,
                    "message": f"Retrieved details for client {client_id}."
                }
        
        return {
            "success": False,
            "error": f"Client with ID {client_id} not found."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get client details: {str(e)}"
        }
