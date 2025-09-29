"""
Meeting Scheduler Tool for Personal Assistant Demo.

This tool demonstrates enterprise integration capabilities that solutions architects
need to showcase to clients - meeting scheduling, coordination, and
professional communication.
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
MEETINGS_FILE = data_path("meetings.json")
_MEETINGS_LOCK = FileLock(str(MEETINGS_FILE) + ".lock", timeout=5)

logger = logging.getLogger(__name__)


class MeetingError(Exception):
    """Custom exception for meeting-related errors."""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code or "MEETING_ERROR"
        super().__init__(message)


def _validate_meeting_input(title: str, participants: List[str], duration_minutes: int = 60, description: str = "") -> None:
    """Validate meeting input parameters."""
    if not title or not title.strip():
        raise MeetingError("Meeting title cannot be empty", "INVALID_TITLE")
    
    if len(title.strip()) > 200:
        raise MeetingError("Meeting title too long (max 200 characters)", "TITLE_TOO_LONG")
    
    if not participants or len(participants) == 0:
        raise MeetingError("Meeting must have at least one participant", "NO_PARTICIPANTS")
    
    if len(participants) > 50:
        raise MeetingError("Too many participants (max 50)", "TOO_MANY_PARTICIPANTS")
    
    for participant in participants:
        if not participant or not participant.strip():
            raise MeetingError("Participant name cannot be empty", "INVALID_PARTICIPANT")
        if len(participant.strip()) > 100:
            raise MeetingError("Participant name too long (max 100 characters)", "PARTICIPANT_NAME_TOO_LONG")
    
    if duration_minutes <= 0:
        raise MeetingError("Duration must be positive", "INVALID_DURATION")
    
    if duration_minutes > 1440:  # 24 hours
        raise MeetingError("Duration too long (max 24 hours)", "DURATION_TOO_LONG")
    
    if description and len(description) > 1000:
        raise MeetingError("Description too long (max 1000 characters)", "DESCRIPTION_TOO_LONG")


def _generate_meeting_id() -> str:
    """Generate a unique meeting ID using UUID."""
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


def measure_performance(func: Callable) -> Callable:
    """Decorator to measure and log function performance."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = func.__name__
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
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


# Performance monitoring and caching
_meeting_cache = {}
_cache_timestamps = {}
CACHE_TTL = 30  # seconds
MAX_CACHE_SIZE = 100


def _get_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate cache key from function name and arguments."""
    import hashlib
    key_parts = [func_name]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()[:16]


def _is_cache_valid(cache_key: str) -> bool:
    """Check if cache entry is still valid."""
    if cache_key not in _cache_timestamps:
        return False
    age = time.time() - _cache_timestamps[cache_key]
    return age < CACHE_TTL


def _get_from_cache(cache_key: str) -> Optional[str]:
    """Get value from cache if valid."""
    if _is_cache_valid(cache_key):
        return _meeting_cache.get(cache_key)
    return None


def _set_cache(cache_key: str, value: str) -> None:
    """Set cache value with timestamp and size management."""
    # Simple LRU: remove oldest entries if cache is full
    if len(_meeting_cache) >= MAX_CACHE_SIZE:
        oldest_key = min(_cache_timestamps.keys(), key=lambda k: _cache_timestamps[k])
        _meeting_cache.pop(oldest_key, None)
        _cache_timestamps.pop(oldest_key, None)
    
    _meeting_cache[cache_key] = value
    _cache_timestamps[cache_key] = time.time()


def _invalidate_meeting_cache() -> None:
    """Invalidate all meeting cache entries."""
    global _meeting_cache, _cache_timestamps
    invalidated_count = len(_meeting_cache)
    _meeting_cache.clear()
    _cache_timestamps.clear()
    logger.info(f"Invalidated {invalidated_count} cache entries")


def _load_meetings() -> List[Dict[str, Any]]:
    """Load meetings from the JSON file with proper locking."""
    try:
        with _MEETINGS_LOCK:
            if MEETINGS_FILE.exists():
                return json.loads(MEETINGS_FILE.read_text(encoding="utf-8"))
            return []
    except Exception as e:
        logger.error(f"Error loading meetings: {e}")
        return []


def _save_meetings(meetings: List[Dict[str, Any]]) -> None:
    """Save meetings to the JSON file atomically."""
    try:
        MEETINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with _MEETINGS_LOCK:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tmp', 
                                           dir=MEETINGS_FILE.parent, delete=False, 
                                           encoding='utf-8') as tmp_file:
                json.dump(meetings, tmp_file, indent=2)
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
                tmp_file_path = tmp_file.name
            
            shutil.move(tmp_file_path, MEETINGS_FILE)
            
    except Exception as e:
        logger.error(f"Error saving meetings: {e}")
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            try:
                os.remove(tmp_file_path)
            except:
                pass
        raise MeetingError(f"Failed to save meetings: {str(e)}", "SAVE_FAILED")




@measure_performance
async def schedule_meeting(
    title: str,
    participants: list,
    duration_minutes: int = 60,
    preferred_times: list = None,
    description: str = ""
) -> str:
    """
    Schedule a meeting with the specified details.
    
    This function demonstrates enterprise scheduling capabilities
    that solutions architects often need to showcase to clients.
    
    Returns:
        JSON string with standardized response format
    """
    try:
        # Input validation
        _validate_meeting_input(title, participants, duration_minutes, description)
        # Load existing meetings
        meetings = _load_meetings()

        # Helpers for robust duplicate detection
        def _normalize_title(s: str) -> str:
            """Lowercase, trim, and collapse internal whitespace for title comparison."""
            return " ".join((s or "").lower().strip().split())

        def _times_overlap(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
            """Return True if time intervals overlap."""
            return (a_start < b_end) and (b_start < a_end)

        # Parse preferred times and find best slot FIRST so we can compare against existing meetings
        best_time = None
        if preferred_times:
            # Enhanced logic to handle natural language time strings
            for time_str in preferred_times:
                try:
                    # Try ISO format first
                    parsed_time = datetime.fromisoformat(time_str)
                except ValueError:
                    # Try to parse natural language time strings
                    time_str_lower = time_str.lower().strip()
                    now = datetime.now()

                    if "tomorrow" in time_str_lower:
                        target_date = now + timedelta(days=1)
                    elif "today" in time_str_lower:
                        target_date = now
                    else:
                        # Default to tomorrow if no date specified
                        target_date = now + timedelta(days=1)

                    # Extract time from string
                    if "2 pm" in time_str_lower or "2:00 pm" in time_str_lower:
                        hour, minute = 14, 0
                    elif "3 pm" in time_str_lower or "3:00 pm" in time_str_lower:
                        hour, minute = 15, 0
                    elif "4 pm" in time_str_lower or "4:00 pm" in time_str_lower:
                        hour, minute = 16, 0
                    elif "10 am" in time_str_lower or "10:00 am" in time_str_lower:
                        hour, minute = 10, 0
                    elif "11 am" in time_str_lower or "11:00 am" in time_str_lower:
                        hour, minute = 11, 0
                    elif "12 pm" in time_str_lower or "12:00 pm" in time_str_lower:
                        hour, minute = 12, 0
                    elif "1 pm" in time_str_lower or "1:00 pm" in time_str_lower:
                        hour, minute = 13, 0
                    else:
                        # Default to 10 AM if time not recognized
                        hour, minute = 10, 0

                    parsed_time = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

                # Check if time is in the future
                if parsed_time > datetime.now():
                    best_time = parsed_time
                    break

        if not best_time:
            # Default to tomorrow at 10 AM
            best_time = datetime.now() + timedelta(days=1)
            best_time = best_time.replace(hour=10, minute=0, second=0, microsecond=0)

        # Calculate end time for target slot
        end_time = best_time + timedelta(minutes=duration_minutes)

        # Robust duplicate prevention: same normalized title AND same participants AND overlapping/same time
        new_title_norm = _normalize_title(title)
        new_participants_set = set(participants)
        for existing_meeting in meetings:
            try:
                existing_title_norm = _normalize_title(existing_meeting.get("title", ""))
                existing_participants_set = set(existing_meeting.get("participants", []))
                existing_start = datetime.fromisoformat(existing_meeting["start_time"])
                # Use stored end_time if present; otherwise compute from duration
                if existing_meeting.get("end_time"):
                    existing_end = datetime.fromisoformat(existing_meeting["end_time"])
                else:
                    existing_end = existing_start + timedelta(minutes=int(existing_meeting.get("duration_minutes", duration_minutes)))

                # Titles must be exactly equal after normalization, and participants must match exactly
                titles_match = (existing_title_norm == new_title_norm)
                participants_match = (existing_participants_set == new_participants_set)

                # Time overlap or near-identical start (<= 5 minutes)
                starts_close_seconds = abs((existing_start - best_time).total_seconds())
                time_conflict = _times_overlap(existing_start, existing_end, best_time, end_time) or (starts_close_seconds <= 300)

                if titles_match and participants_match and time_conflict:
                    response_data = {
                        "meeting_id": existing_meeting["id"],
                        "title": existing_meeting["title"],
                        "start_time": existing_start.strftime("%Y-%m-%d %H:%M"),
                        "participants": existing_meeting["participants"],
                        "duplicate_prevented": True
                    }
                    message = f"Meeting '{title}' with {', '.join(participants)} already exists (ID: {existing_meeting['id']}) around {existing_start.strftime('%Y-%m-%d %H:%M')}. No duplicate created."
                    return _create_standard_response(
                        success=True,
                        data=response_data,
                        message=message
                    )
            except (ValueError, KeyError, TypeError):
                continue

        # Generate meeting ID using UUID
        meeting_id = _generate_meeting_id()
        
        # Create meeting object
        meeting = {
            "id": meeting_id,
            "title": title,
            "participants": participants,
            "start_time": best_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_minutes": duration_minutes,
            "description": description,
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }
        
        meetings.append(meeting)
        
        # Save to file (atomic operation)
        _save_meetings(meetings)
        
        # Invalidate cache after modification
        _invalidate_meeting_cache()
        
        # Create response data
        response_data = {
            "meeting_id": meeting_id,
            "title": title,
            "start_time": best_time.strftime("%Y-%m-%d %H:%M"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M"),
            "participants": participants,
            "duration_minutes": duration_minutes,
            "status": "scheduled"
        }
        
        message = f"Meeting '{title}' scheduled successfully for {best_time.strftime('%Y-%m-%d at %H:%M')} with {len(participants)} participants."
        
        return _create_standard_response(
            success=True,
            data=response_data,
            message=message
        )
        
    except MeetingError as e:
        return _create_standard_response(
            success=False,
            error=e.message,
            error_code=e.error_code
        )
    except Exception as e:
        logger.error(f"Unexpected error scheduling meeting: {e}")
        return _create_standard_response(
            success=False,
            error="Internal error occurred during meeting scheduling",
            error_code="INTERNAL_ERROR"
        )


@measure_performance
async def list_meetings(filters: str = "") -> str:
    """List meetings with optional filtering (e.g., 'active', 'cancelled').
    
    Returns:
        JSON string with standardized response format
    """
    try:
        # Input validation
        if filters and len(filters.strip()) > 100:
            raise MeetingError("Filter string too long (max 100 characters)", "FILTER_TOO_LONG")
        
        # Check cache first
        cache_key = _get_cache_key("list_meetings", (), {"filters": filters})
        cached_result = _get_from_cache(cache_key)
        if cached_result:
            return cached_result
        meetings = _load_meetings()

        if not meetings:
            response_data = {
                "meetings": [],
                "count": 0,
                "filter": filters
            }
            result = _create_standard_response(
                success=True,
                data=response_data,
                message="No meetings found."
            )
            _set_cache(cache_key, result)
            return result

        # Apply simple status filters
        filtered_meetings = meetings
        if filters:
            f = filters.lower().strip()
            if "active" in f:
                filtered_meetings = [m for m in meetings if m.get("status", "scheduled").lower() != "cancelled"]
            elif "cancelled" in f or "canceled" in f:
                filtered_meetings = [m for m in meetings if m.get("status", "scheduled").lower() == "cancelled"]

        # Sort by start time (handle missing start_time gracefully)
        filtered_meetings.sort(key=lambda x: x.get("start_time", "1970-01-01T00:00:00"))

        # Project to compact representation
        def _project(m: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "id": m.get("id"),
                "title": m.get("title"),
                "start_time": m.get("start_time"),
                "end_time": m.get("end_time"),
                "status": m.get("status", "scheduled"),
                "participants": m.get("participants", [])
            }

        slim = [_project(m) for m in filtered_meetings]

        response_data = {
            "meetings": slim,
            "count": len(slim),
            "filter": filters
        }
        
        message = f"Found {len(slim)} meeting(s)"
        if filters:
            message += f" with filter '{filters}'"
        message += "."
        
        result = _create_standard_response(
            success=True,
            data=response_data,
            message=message
        )
        
        # Cache the result
        _set_cache(cache_key, result)
        return result

    except MeetingError as e:
        return _create_standard_response(
            success=False,
            error=e.message,
            error_code=e.error_code
        )
    except Exception as e:
        logger.error(f"Unexpected error listing meetings: {e}")
        return _create_standard_response(
            success=False,
            error="Internal error occurred while listing meetings",
            error_code="INTERNAL_ERROR"
        )


@measure_performance
async def cancel_meeting(meeting_id: str, reason: str = "") -> str:
    """
    Cancel a scheduled meeting by ID.
    
    Args:
        meeting_id: UUID-based meeting identifier
        reason: Optional cancellation reason
        
    Returns:
        JSON string with standardized response format
    """
    try:
        # Input validation
        if not meeting_id or not meeting_id.strip():
            raise MeetingError("Meeting ID cannot be empty", "INVALID_MEETING_ID")
        
        if len(meeting_id.strip()) > 50:
            raise MeetingError("Meeting ID too long", "MEETING_ID_TOO_LONG")
        
        if reason and len(reason.strip()) > 500:
            raise MeetingError("Cancellation reason too long (max 500 characters)", "REASON_TOO_LONG")
        
        meetings = _load_meetings()
        
        if not meetings:
            raise MeetingError("No meetings found", "NO_MEETINGS_FOUND")
        
        # Find and update meeting
        meeting_found = False
        cancelled_meeting = None
        for meeting in meetings:
            if meeting["id"] == meeting_id.strip():
                if meeting.get("status", "scheduled").lower() == "cancelled":
                    raise MeetingError(f"Meeting {meeting_id} is already cancelled", "ALREADY_CANCELLED")
                
                meeting["status"] = "cancelled"
                meeting["cancelled_at"] = datetime.now().isoformat()
                meeting["cancellation_reason"] = reason.strip() if reason.strip() else "No reason provided"
                meeting_found = True
                cancelled_meeting = meeting.copy()  # Copy for response
                break
        
        if not meeting_found:
            raise MeetingError(f"Meeting with ID {meeting_id} not found", "MEETING_NOT_FOUND")
        
        # Save updated meetings (atomic operation)
        _save_meetings(meetings)
        
        # Invalidate cache after modification
        _invalidate_meeting_cache()
        
        # Create response data
        response_data = {
            "meeting_id": meeting_id,
            "title": cancelled_meeting["title"],
            "participants": cancelled_meeting["participants"],
            "cancelled_at": cancelled_meeting["cancelled_at"],
            "cancellation_reason": cancelled_meeting["cancellation_reason"],
            "status": "cancelled"
        }
        
        message = f"Meeting '{cancelled_meeting['title']}' (ID: {meeting_id}) cancelled successfully. Participants would be notified automatically."
        
        return _create_standard_response(
            success=True,
            data=response_data,
            message=message
        )
        
    except MeetingError as e:
        return _create_standard_response(
            success=False,
            error=e.message,
            error_code=e.error_code
        )
    except Exception as e:
        logger.error(f"Unexpected error cancelling meeting: {e}")
        return _create_standard_response(
            success=False,
            error="Internal error occurred during meeting cancellation",
            error_code="INTERNAL_ERROR"
        )
