"""
Meeting Scheduler Tool for Personal Assistant Demo.

This tool demonstrates enterprise integration capabilities that solutions architects
need to showcase to clients - meeting scheduling, coordination, and
professional communication.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict
from pathlib import Path
from filelock import FileLock
from ._paths import data_path

# Standardized file path and lock
MEETINGS_FILE = data_path("meetings.json")
_MEETINGS_LOCK = FileLock(str(MEETINGS_FILE) + ".lock")


def _load_meetings():
    """Load meetings from the JSON file with proper locking."""
    with _MEETINGS_LOCK:
        return json.loads(MEETINGS_FILE.read_text(encoding="utf-8")) if MEETINGS_FILE.exists() else []


def _save_meetings(data):
    """Save meetings to the JSON file with proper locking."""
    with _MEETINGS_LOCK:
        MEETINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        MEETINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")




async def schedule_meeting(
    title: str,
    participants: list,
    duration_minutes: int = 60,
    preferred_times: list = None,
    description: str = ""
) -> Dict[str, Any]:
    """
    Schedule a meeting with the specified details.
    
    This function demonstrates enterprise scheduling capabilities
    that solutions architects often need to showcase to clients.
    """
    try:
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
                    return json.dumps({
                        "success": True,
                        "meeting_id": existing_meeting["id"],
                        "title": existing_meeting["title"],
                        "start_time": existing_start.strftime("%Y-%m-%d %H:%M"),
                        "participants": existing_meeting["participants"],
                        "message": f"Meeting '{title}' with {', '.join(participants)} already exists (ID: {existing_meeting['id']}) around {existing_start.strftime('%Y-%m-%d %H:%M')}. No duplicate created.",
                        "duplicate_prevented": True
                    })
            except (ValueError, KeyError, TypeError):
                continue

        # Generate meeting ID
        meeting_id = len(meetings) + 1
        
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
        
        # Save to file
        _save_meetings(meetings)
        
        return json.dumps({
            "success": True,
            "meeting_id": meeting_id,
            "title": title,
            "start_time": best_time.strftime("%Y-%m-%d %H:%M"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M"),
            "participants": participants,
            "message": f"Meeting '{title}' scheduled successfully for {best_time.strftime('%Y-%m-%d at %H:%M')} with {len(participants)} participants."
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to schedule meeting: {str(e)}"
        })


async def list_meetings(filters: str = "") -> Dict[str, Any]:
    """List meetings with optional filtering (e.g., 'active', 'cancelled')."""
    try:
        meetings = _load_meetings()

        if not meetings:
            return json.dumps({
                "success": True,
                "meetings": [],
                "count": 0,
                "message": "No meetings found."
            })

        # Apply simple status filters
        filtered_meetings = meetings
        if filters:
            f = filters.lower()
            if "active" in f:
                filtered_meetings = [m for m in meetings if m.get("status", "scheduled").lower() != "cancelled"]
            elif "cancelled" in f or "canceled" in f:
                filtered_meetings = [m for m in meetings if m.get("status", "scheduled").lower() == "cancelled"]

        # Sort by start time
        filtered_meetings.sort(key=lambda x: x.get("start_time", ""))

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

        return json.dumps({
            "success": True,
            "meetings": slim,
            "count": len(slim),
            "message": f"Found {len(slim)} meeting(s)."
        })

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to list meetings: {str(e)}"
        })


async def cancel_meeting(meeting_id: int, reason: str = "") -> Dict[str, Any]:
    """
    Cancel a scheduled meeting by ID.
    """
    try:
        meetings = _load_meetings()
        
        if not meetings:
            return json.dumps({
                "success": False,
                "error": "No meetings found."
            })
        
        # Find and update meeting
        meeting_found = False
        for meeting in meetings:
            if meeting["id"] == meeting_id:
                meeting["status"] = "cancelled"
                meeting["cancelled_at"] = datetime.now().isoformat()
                meeting["cancellation_reason"] = reason if reason else "No reason provided"
                meeting_found = True
                break
        
        if not meeting_found:
            return json.dumps({
                "success": False,
                "error": f"Meeting with ID {meeting_id} not found."
            })
        
        # Save updated meetings
        _save_meetings(meetings)
        
        return json.dumps({
            "success": True,
            "meeting_id": meeting_id,
            "message": f"Meeting {meeting_id} cancelled successfully. Participants would be notified automatically."
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to cancel meeting: {str(e)}"
        })
