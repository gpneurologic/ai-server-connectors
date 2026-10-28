"""Tests for MCP server."""

import asyncio
import pytest
from google_workspace_mcp.server import app


def test_server_name():
    """Test server name."""
    assert app.name == "google-workspace"


@pytest.mark.anyio
async def test_tools_registered():
    """Test that tools are registered."""
    tools = await app.list_tools()
    tool_names = [t.name for t in tools]

    # Check Gmail tools
    assert "gmail_search_messages" in tool_names
    assert "gmail_get_message" in tool_names
    assert "gmail_list_threads" in tool_names
    assert "gmail_list_labels" in tool_names
    assert "gmail_create_draft" in tool_names
    assert "gmail_send_email" in tool_names

    # Check Calendar tools
    assert "calendar_list_calendars" in tool_names
    assert "calendar_list_events" in tool_names
    assert "calendar_get_event" in tool_names
    assert "calendar_create_event" in tool_names
    assert "calendar_delete_event" in tool_names

    # Check Sheets tools
    assert "sheets_search_spreadsheets" in tool_names
    assert "sheets_get_metadata" in tool_names
    assert "sheets_read_range" in tool_names
    assert "sheets_write_range" in tool_names
    assert "sheets_append_rows" in tool_names
    assert "sheets_create_spreadsheet" in tool_names

    # Check Slides tools
    assert "slides_search_presentations" in tool_names
    assert "slides_get_presentation" in tool_names
    assert "slides_get_slide_content" in tool_names
    assert "slides_create_presentation" in tool_names
    assert "slides_add_slide" in tool_names
    assert "slides_insert_text" in tool_names

    # Check Drive tools
    assert "drive_search_files" in tool_names
    assert "drive_list_files" in tool_names
    assert "drive_get_file_metadata" in tool_names
    assert "drive_read_file" in tool_names
    assert "drive_create_folder" in tool_names
    assert "drive_upload_file" in tool_names
    assert "drive_rename_file" in tool_names
    assert "drive_trash_file" in tool_names
    assert "drive_restore_file" in tool_names

    # Total: 6 + 5 + 6 + 6 + 9 = 32 tools
    assert len(tool_names) == 32
