"""
Client Management Tool for Personal Assistant Demo.

This tool demonstrates CRM and project management capabilities that solutions architects
need for managing client relationships, tracking projects, and maintaining professional
communication records.
"""

import json
import os
import logging
import tempfile
import shutil
import uuid
import time
import functools
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from filelock import FileLock
from ._paths import data_path

# Standardized file path and lock
CLIENTS_FILE = data_path("clients.json")
_CLIENTS_LOCK = FileLock(str(CLIENTS_FILE) + ".lock", timeout=5)

logger = logging.getLogger(__name__)


class ClientError(Exception):
    """Custom exception for client-related errors."""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code or "CLIENT_ERROR"
        super().__init__(message)


def _validate_client_input(name: str, company: str, email: str = "", priority: str = "medium") -> None:
    """Validate client input parameters."""
    if not name or not name.strip():
        raise ClientError("Client name cannot be empty", "INVALID_NAME")
    
    if not company or not company.strip():
        raise ClientError("Company name cannot be empty", "INVALID_COMPANY")
    
    if len(name.strip()) > 100:
        raise ClientError("Client name too long (max 100 characters)", "NAME_TOO_LONG")
        
    if len(company.strip()) > 100:
        raise ClientError("Company name too long (max 100 characters)", "COMPANY_TOO_LONG")
    
    if email and len(email) > 200:
        raise ClientError("Email too long (max 200 characters)", "EMAIL_TOO_LONG")
    
    valid_priorities = ["high", "medium", "low"]
    if priority and priority.lower() not in valid_priorities:
        raise ClientError(f"Priority must be one of: {', '.join(valid_priorities)}", "INVALID_PRIORITY")


def _generate_client_id() -> str:
    """Generate a unique client ID using UUID."""
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
_client_cache = {}
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
            
            if execution_time > 1.0:
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
    if _is_cache_valid(cache_key) and cache_key in _client_cache:
        logger.info(f"Cache hit for {cache_key[:20]}...")
        return _client_cache[cache_key]
    return None


def _set_cache(cache_key: str, data: str) -> None:
    """Set data in cache with timestamp."""
    _client_cache[cache_key] = data
    _cache_timestamps[cache_key] = time.time()
    
    if len(_client_cache) > 50:
        oldest_key = min(_cache_timestamps.keys(), key=lambda k: _cache_timestamps[k])
        del _client_cache[oldest_key]
        del _cache_timestamps[oldest_key]


def _invalidate_client_cache() -> None:
    """Clear client-related cache when data changes."""
    keys_to_remove = [k for k in _client_cache.keys() if k.startswith('list_clients')]
    for key in keys_to_remove:
        _client_cache.pop(key, None)
        _cache_timestamps.pop(key, None)
    logger.info(f"Invalidated {len(keys_to_remove)} client cache entries")


def _load_clients() -> List[Dict[str, Any]]:
    """Load clients from the JSON file with proper error handling."""
    try:
        with _CLIENTS_LOCK:
            if CLIENTS_FILE.exists():
                return json.loads(CLIENTS_FILE.read_text(encoding="utf-8"))
            return []
    except Exception as e:
        logger.error(f"Error loading clients: {e}")
        return []


def _save_clients(data: List[Dict[str, Any]]) -> None:
    """Save clients to the JSON file atomically."""
    try:
        CLIENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with _CLIENTS_LOCK:
            # Write to temp file first for atomic operation
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tmp', 
                                           dir=CLIENTS_FILE.parent, delete=False,
                                           encoding='utf-8') as tmp_file:
                json.dump(data, tmp_file, indent=2)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                tmp_file_path = tmp_file.name
            
            # Atomic move
            shutil.move(tmp_file_path, CLIENTS_FILE)
            
    except Exception as e:
        logger.error(f"Error saving clients: {e}")
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            try:
                os.remove(tmp_file_path)
            except:
                pass
        raise ClientError(f"Failed to save clients: {str(e)}", "SAVE_FAILED")




@measure_performance
async def add_client(
    name: str,
    company: str,
    email: str = "",
    phone: str = "",
    project_requirements: str = "",
    priority: str = "medium"
) -> str:
    """
    Add a new client to the CRM system.
    
    This function demonstrates enterprise CRM capabilities that solutions architects
    use to manage client relationships and track project opportunities.
    """
    try:
        # Input validation
        _validate_client_input(name, company, email, priority)
        
        # Load existing clients
        clients = _load_clients()
        
        # Check for duplicates
        for client in clients:
            if email and client.get("email") == email:
                raise ClientError(f"Client with email {email} already exists", "DUPLICATE_EMAIL")
            if (client.get("name", "").lower() == name.lower() and 
                client.get("company", "").lower() == company.lower()):
                raise ClientError(f"Client '{name}' from company '{company}' already exists", "DUPLICATE_CLIENT")
        
        # Generate unique client ID
        client_id = _generate_client_id()
        
        # Ensure ID is unique
        existing_ids = {str(client.get("id")) for client in clients}
        while client_id in existing_ids:
            client_id = _generate_client_id()
        
        # Create client object
        client = {
            "id": client_id,
            "name": name.strip(),
            "email": email.strip() if email else "",
            "company": company.strip(),
            "phone": phone.strip() if phone else "",
            "project_requirements": project_requirements.strip() if project_requirements else "",
            "priority": priority.lower(),
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "last_contact": datetime.now().isoformat(),
            "notes": []
        }
        
        clients.append(client)
        _save_clients(clients)
        
        # Invalidate cache
        _invalidate_client_cache()
        
        # Create response data
        response_data = {
            "client_id": client_id,
            "name": name.strip(),
            "company": company.strip(),
            "email": email.strip() if email else "",
            "priority": priority.lower(),
            "created_at": client["created_at"]
        }
        
        return _create_standard_response(
            success=True,
            data=response_data,
            message=f"Client '{name}' from {company} added successfully with ID {client_id}"
        )
        
    except ClientError as e:
        return _create_standard_response(
            success=False,
            error=e.message,
            error_code=e.error_code
        )
    except Exception as e:
        logger.error(f"Unexpected error adding client: {e}")
        return _create_standard_response(
            success=False,
            error="Internal error occurred while adding client",
            error_code="INTERNAL_ERROR"
        )


@measure_performance
async def list_clients(filters: str = "") -> str:
    """
    List all clients with optional filtering.
    Supports filtering by priority: 'high', 'medium', 'low', or 'high-priority'
    """
    try:
        # Check cache first
        cache_key = _get_cache_key("list_clients", (filters,), {})
        cached_result = _get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        clients = _load_clients()

        if not clients:
            result = _create_standard_response(
                success=True,
                data={"clients": [], "count": 0, "filter": filters.strip() if filters else None},
                message="No clients found."
            )
            _set_cache(cache_key, result)
            return result

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

        response_data = {
            "clients": slim_clients,
            "count": len(slim_clients),
            "filter": filters.strip() if filters else None
        }
        
        result = _create_standard_response(
            success=True,
            data=response_data,
            message=f"Found {len(slim_clients)} client(s){filter_message}."
        )
        
        # Cache the result
        _set_cache(cache_key, result)
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error listing clients: {e}")
        return _create_standard_response(
            success=False,
            error="Internal error occurred while listing clients",
            error_code="INTERNAL_ERROR"
        )


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
