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

"""Tests to verify path centralization works correctly across different working directories."""

import asyncio
import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from personal_assistant.tools.client_management import list_clients
from personal_assistant.tools.meeting_scheduler import list_meetings
from personal_assistant.tools._paths import data_path


@pytest.fixture
def sample_clients_data():
    """Sample client data for testing."""
    return [
        {
            "id": 1,
            "name": "John Doe",
            "company": "Tech Corp",
            "email": "john@techcorp.com",
            "phone": "+1-555-0123",
            "project_requirements": "Cloud migration project",
            "priority": "high",
            "status": "active",
            "created_at": "2024-01-15T10:30:00",
            "last_contact": "2024-01-15T10:30:00",
            "notes": []
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "company": "Data Solutions",
            "email": "jane@datasolutions.com",
            "phone": "+1-555-0456",
            "project_requirements": "AI analytics platform",
            "priority": "medium",
            "status": "active",
            "created_at": "2024-01-16T14:20:00",
            "last_contact": "2024-01-16T14:20:00",
            "notes": []
        }
    ]


@pytest.fixture
def sample_meetings_data():
    """Sample meeting data for testing."""
    return [
        {
            "id": 1,
            "title": "Project Kickoff",
            "participants": ["john@techcorp.com", "jane@datasolutions.com"],
            "start_time": "2024-01-20T10:00:00",
            "end_time": "2024-01-20T11:00:00",
            "duration_minutes": 60,
            "description": "Initial project planning meeting",
            "status": "scheduled",
            "created_at": "2024-01-15T16:45:00"
        },
        {
            "id": 2,
            "title": "Weekly Sync",
            "participants": ["team@company.com"],
            "start_time": "2024-01-22T15:00:00",
            "end_time": "2024-01-22T16:00:00",
            "duration_minutes": 60,
            "description": "Regular team synchronization",
            "status": "scheduled",
            "created_at": "2024-01-16T09:15:00"
        }
    ]


def setup_test_data(clients_data, meetings_data):
    """Setup test data files in the proper data directory."""
    # Ensure the data directory exists
    data_path("clients.json").parent.mkdir(parents=True, exist_ok=True)
    
    # Write test data
    data_path("clients.json").write_text(
        json.dumps(clients_data, indent=2), 
        encoding="utf-8"
    )
    data_path("meetings.json").write_text(
        json.dumps(meetings_data, indent=2), 
        encoding="utf-8"
    )


def cleanup_test_data():
    """Clean up test data files."""
    for filename in ["clients.json", "meetings.json"]:
        test_file = data_path(filename)
        if test_file.exists():
            test_file.unlink()


@pytest.mark.asyncio
async def test_path_centralization_with_chdir(sample_clients_data, sample_meetings_data):
    """
    Test that list_clients and list_meetings work correctly even after changing
    the working directory, ensuring all paths use the centralized _paths module.
    """
    # Store original working directory
    original_cwd = os.getcwd()
    
    try:
        # Setup test data in the proper data directory
        setup_test_data(sample_clients_data, sample_meetings_data)
        
        # Create a temporary directory and change to it
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change working directory to temporary location
            os.chdir(temp_dir)
            
            # Verify we're in a different directory
            assert os.getcwd() == temp_dir
            assert os.getcwd() != original_cwd
            
            # Test list_clients - should still work despite directory change
            clients_result = await list_clients()
            clients_data = json.loads(clients_result)
            
            # Verify the client list function worked correctly
            assert clients_data["success"] is True
            assert clients_data["count"] == 2
            assert len(clients_data["clients"]) == 2
            
            # Verify client data is correct
            client_names = [client["name"] for client in clients_data["clients"]]
            assert "John Doe" in client_names
            assert "Jane Smith" in client_names
            
            # Test list_meetings - should still work despite directory change
            meetings_result = await list_meetings()
            meetings_data = json.loads(meetings_result)
            
            # Verify the meetings list function worked correctly
            assert meetings_data["success"] is True
            assert meetings_data["count"] == 2
            assert len(meetings_data["meetings"]) == 2
            
            # Verify meeting data is correct
            meeting_titles = [meeting["title"] for meeting in meetings_data["meetings"]]
            assert "Project Kickoff" in meeting_titles
            assert "Weekly Sync" in meeting_titles
            
    finally:
        # Always restore original working directory
        os.chdir(original_cwd)
        # Clean up test data
        cleanup_test_data()


@pytest.mark.asyncio
async def test_multiple_directory_changes(sample_clients_data, sample_meetings_data):
    """
    Test that functions work correctly across multiple directory changes,
    ensuring robust path resolution.
    """
    original_cwd = os.getcwd()
    
    try:
        # Setup test data
        setup_test_data(sample_clients_data, sample_meetings_data)
        
        # Test across multiple temporary directories
        for i in range(3):
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                
                # Create some nested directories to make it more challenging
                nested_dir = Path(temp_dir) / "nested" / "deep" / f"level_{i}"
                nested_dir.mkdir(parents=True)
                os.chdir(nested_dir)
                
                # Test that both functions still work
                clients_result = await list_clients()
                clients_data = json.loads(clients_result)
                assert clients_data["success"] is True
                assert clients_data["count"] == 2
                
                meetings_result = await list_meetings()
                meetings_data = json.loads(meetings_result)
                assert meetings_data["success"] is True
                assert meetings_data["count"] == 2
                
    finally:
        os.chdir(original_cwd)
        cleanup_test_data()


@pytest.mark.asyncio
async def test_path_centralization_no_data_files():
    """
    Test that functions handle missing data files correctly regardless of working directory.
    """
    original_cwd = os.getcwd()
    
    try:
        # Ensure no test data files exist
        cleanup_test_data()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Test list_clients with no data file
            clients_result = await list_clients()
            clients_data = json.loads(clients_result)
            assert clients_data["success"] is True
            assert clients_data["count"] == 0
            assert len(clients_data["clients"]) == 0
            assert "No clients found" in clients_data["message"]
            
            # Test list_meetings with no data file
            meetings_result = await list_meetings()
            meetings_data = json.loads(meetings_result)
            assert meetings_data["success"] is True
            assert meetings_data["count"] == 0
            assert len(meetings_data["meetings"]) == 0
            assert "No meetings found" in meetings_data["message"]
            
    finally:
        os.chdir(original_cwd)


def test_data_path_resolution():
    """
    Test that the data_path function correctly resolves absolute paths
    regardless of the current working directory.
    """
    original_cwd = os.getcwd()
    
    try:
        # Get the absolute path from current directory
        original_path = data_path("test.json")
        assert original_path.is_absolute()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            
            # Path should still be the same absolute path
            new_path = data_path("test.json")
            assert new_path.is_absolute()
            assert original_path == new_path
            
            # Verify it's not relative to the temp directory
            assert not str(new_path).startswith(temp_dir)
            
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    # Run the tests directly if this file is executed
    pytest.main([__file__, "-v"])
