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
        meetings_file = Path("data/meetings.json")
        meetings_file.parent.mkdir(exist_ok=True)
        
        if meetings_file.exists():
            with open(meetings_file, "r") as f:
                meetings = json.load(f)
        else:
            meetings = []
        
        # Check for duplicate meetings (same title, participants, and similar time)
        for existing_meeting in meetings:
            if (existing_meeting.get("title", "").lower().strip() == title.lower().strip() and
                set(existing_meeting.get("participants", [])) == set(participants)):
                
                # Check if it's for a similar time (within 24 hours)
                try:
                    existing_time = datetime.fromisoformat(existing_meeting["start_time"])
                    # If we have preferred times, check against those
                    if preferred_times:
                        for time_str in preferred_times:
                            # More general duplicate detection based on time proximity
                            # Parse the preferred time to compare with existing
                            target_time = None
                            time_str_lower = time_str.lower().strip()
                            now = datetime.now()
                            
                            if "tomorrow" in time_str_lower:
                                target_date = now + timedelta(days=1)
                            elif "today" in time_str_lower:
                                target_date = now
                            else:
                                target_date = now + timedelta(days=1)  # Default to tomorrow
                            
                            # Extract hour from string
                            if "3 pm" in time_str_lower:
                                target_time = target_date.replace(hour=15, minute=0, second=0, microsecond=0)
                            elif "2 pm" in time_str_lower:
                                target_time = target_date.replace(hour=14, minute=0, second=0, microsecond=0)
                            elif "4 pm" in time_str_lower:
                                target_time = target_date.replace(hour=16, minute=0, second=0, microsecond=0)
                            # Add more time patterns as needed
                            
                            if target_time:
                                # If existing meeting is within 2 hours of target time, consider it duplicate
                                time_diff = abs((existing_time - target_time).total_seconds())
                                if time_diff < 7200:  # 2 hours in seconds
                                    return {
                                        "success": True,
                                        "meeting_id": existing_meeting["id"],
                                        "title": existing_meeting["title"],
                                        "start_time": existing_time.strftime("%Y-%m-%d %H:%M"),
                                        "participants": existing_meeting["participants"],
                                        "message": f"Meeting '{title}' with {', '.join(participants)} already exists (ID: {existing_meeting['id']}) at {existing_time.strftime('%Y-%m-%d %H:%M')}. No duplicate created.",
                                        "duplicate_prevented": True
                                    }
                except (ValueError, KeyError):
                    continue
        
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
            "description": description,
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


async def list_meetings(filters: str = "") -> Dict[str, Any]:
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
        
        # Return all meetings (no filtering for simplicity)
        filtered_meetings = meetings
        
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


async def cancel_meeting(meeting_id: int, reason: str = "") -> Dict[str, Any]:
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
                meeting["cancellation_reason"] = reason if reason else "No reason provided"
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
