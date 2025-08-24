"""
Meeting Scheduler Tool for Personal Assistant Demo.

This tool demonstrates enterprise integration capabilities that solutions architects
need to showcase to clients - calendar management, meeting scheduling, and
professional communication.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path




async def schedule_meeting(
    title: str,
    participants: List[str],
    duration_minutes: int = 60,
    preferred_times: Optional[List[str]] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Schedule a meeting with the specified details.
    
    This function demonstrates enterprise calendar integration capabilities
    that solutions architects often need to showcase to clients.
    """
    try:
        # Load existing meetings
        meetings_file = Path("data/meetings.json")
        meetings_file.parent.mkdir(exist_ok=True)
        
        if meetings_file.exists():
            with open(meetings_file, "r") as f:
                meetings = json.load(f)
        else:
            meetings = []
        
        # Generate meeting ID
        meeting_id = len(meetings) + 1
        
        # Parse preferred times and find best slot
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
        
        # Calculate end time
        end_time = best_time + timedelta(minutes=duration_minutes)
        
        # Create meeting object
        meeting = {
            "id": meeting_id,
            "title": title,
            "participants": participants,
            "start_time": best_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_minutes": duration_minutes,
            "description": description or "",
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }
        
        meetings.append(meeting)
        
        # Save to file
        with open(meetings_file, "w") as f:
            json.dump(meetings, f, indent=2)
        
        return {
            "success": True,
            "meeting_id": meeting_id,
            "title": title,
            "start_time": best_time.strftime("%Y-%m-%d %H:%M"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M"),
            "participants": participants,
            "message": f"Meeting '{title}' scheduled successfully for {best_time.strftime('%Y-%m-%d at %H:%M')} with {len(participants)} participants."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to schedule meeting: {str(e)}"
        }


async def list_meetings(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    List all scheduled meetings with optional filtering.
    """
    try:
        meetings_file = Path("data/meetings.json")
        
        if not meetings_file.exists():
            return {
                "success": True,
                "meetings": [],
                "message": "No meetings found."
            }
        
        with open(meetings_file, "r") as f:
            meetings = json.load(f)
        
        # Apply filters
        filtered_meetings = []
        for meeting in meetings:
            # Date filter
            if start_date or end_date:
                meeting_date = datetime.fromisoformat(meeting["start_time"]).date()
                
                if start_date:
                    start_dt = datetime.fromisoformat(start_date).date()
                    if meeting_date < start_dt:
                        continue
                
                if end_date:
                    end_dt = datetime.fromisoformat(end_date).date()
                    if meeting_date > end_dt:
                        continue
            
            # Status filter
            if status and meeting.get("status") != status:
                continue
            
            filtered_meetings.append(meeting)
        
        # Sort by start time
        filtered_meetings.sort(key=lambda x: x["start_time"])
        
        return {
            "success": True,
            "meetings": filtered_meetings,
            "count": len(filtered_meetings),
            "message": f"Found {len(filtered_meetings)} meeting(s)."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list meetings: {str(e)}"
        }


async def cancel_meeting(meeting_id: int, reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Cancel a scheduled meeting by ID.
    """
    try:
        meetings_file = Path("data/meetings.json")
        
        if not meetings_file.exists():
            return {
                "success": False,
                "error": "No meetings found."
            }
        
        with open(meetings_file, "r") as f:
            meetings = json.load(f)
        
        # Find and update meeting
        meeting_found = False
        for meeting in meetings:
            if meeting["id"] == meeting_id:
                meeting["status"] = "cancelled"
                meeting["cancelled_at"] = datetime.now().isoformat()
                meeting["cancellation_reason"] = reason or "No reason provided"
                meeting_found = True
                break
        
        if not meeting_found:
            return {
                "success": False,
                "error": f"Meeting with ID {meeting_id} not found."
            }
        
        # Save updated meetings
        with open(meetings_file, "w") as f:
            json.dump(meetings, f, indent=2)
        
        return {
            "success": True,
            "meeting_id": meeting_id,
            "message": f"Meeting {meeting_id} cancelled successfully. Participants would be notified automatically."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to cancel meeting: {str(e)}"
        }
