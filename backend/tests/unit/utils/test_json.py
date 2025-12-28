"""Unit tests for JSON utility functions."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from planned.domain.entities import User
from planned.domain.value_objects.user import UserSetting
from planned.infrastructure.utils.json import read_directory


@pytest.mark.asyncio
async def test_read_directory_single_file():
    """Test reading a single JSON file from directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test JSON file
        user_id = "test-user-123"
        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "password_hash": "hash",
            "settings": {},
        }
        
        file_path = Path(tmpdir) / f"{user_id}.json"
        with open(file_path, "w") as f:
            json.dump(user_data, f)
        
        result = await read_directory(tmpdir, User)
        
        assert len(result) == 1
        assert result[0].id == user_id
        assert result[0].email == "test@example.com"


@pytest.mark.asyncio
async def test_read_directory_multiple_files():
    """Test reading multiple JSON files from directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple test JSON files
        for i in range(3):
            user_id = f"test-user-{i}"
            user_data = {
                "id": user_id,
                "email": f"test{i}@example.com",
                "password_hash": "hash",
                "settings": {},
            }
            
            file_path = Path(tmpdir) / f"{user_id}.json"
            with open(file_path, "w") as f:
                json.dump(user_data, f)
        
        result = await read_directory(tmpdir, User)
        
        assert len(result) == 3
        assert all(user.id.startswith("test-user-") for user in result)


@pytest.mark.asyncio
async def test_read_directory_nonexistent():
    """Test reading from nonexistent directory returns empty list."""
    nonexistent_dir = "/nonexistent/directory/path"
    result = await read_directory(nonexistent_dir, User)
    
    assert result == []


@pytest.mark.asyncio
async def test_read_directory_ignores_non_json():
    """Test read_directory ignores non-JSON files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a JSON file
        user_id = "test-user"
        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "password_hash": "hash",
            "settings": {},
        }
        
        json_file = Path(tmpdir) / f"{user_id}.json"
        with open(json_file, "w") as f:
            json.dump(user_data, f)
        
        # Create a non-JSON file
        txt_file = Path(tmpdir) / "readme.txt"
        txt_file.write_text("This is not JSON")
        
        result = await read_directory(tmpdir, User)
        
        assert len(result) == 1
        assert result[0].id == user_id


@pytest.mark.asyncio
async def test_read_directory_ignores_directories():
    """Test read_directory ignores subdirectories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a JSON file
        user_id = "test-user"
        user_data = {
            "id": user_id,
            "email": "test@example.com",
            "password_hash": "hash",
            "settings": {},
        }
        
        json_file = Path(tmpdir) / f"{user_id}.json"
        with open(json_file, "w") as f:
            json.dump(user_data, f)
        
        # Create a subdirectory (which would appear in listdir but should be ignored)
        subdir = Path(tmpdir) / "subdir"
        subdir.mkdir()
        
        result = await read_directory(tmpdir, User)
        
        assert len(result) == 1
        assert result[0].id == user_id

