"""Google Workspace MCP Server."""

import asyncio
import json
import logging
import sys
from typing import Any

from mcp.server import MCPServer
from mcp.server.stdio import stdio_server

from .auth import authenticate
from .config import get_config
from .gmail import GmailTools
from .calendar import CalendarTools
from .sheets import SheetsTools
from .slides import SlidesTools
from .drive import DriveTools

logger = logging.getLogger(__name__)

# MCP server instance
app = MCPServer("google-workspace")

# Tool implementations (initialized after auth)
tools = {}


def init_tools(credentials, config):
    """Initialize all tool implementations."""
    tools["gmail"] = GmailTools(credentials, config)
    tools["calendar"] = CalendarTools(credentials, config)
    tools["sheets"] = SheetsTools(credentials, config)
    tools["slides"] = SlidesTools(credentials, config)
    tools["drive"] = DriveTools(credentials, config)


# Gmail tools
@app.tool()
def gmail_search_messages(query: str, max_results: int = 10) -> Any:
    """Search Gmail messages. Use Gmail query syntax (e.g., 'from:alice@example.com subject:hello')."""
    return tools["gmail"].search_messages(query, max_results)


@app.tool()
def gmail_get_message(message_id: str, include_body: bool = False) -> Any:
    """Get a Gmail message. Set include_body=true to retrieve the full message body."""
    return tools["gmail"].get_message(message_id, include_body)


@app.tool()
def gmail_list_threads(query: str = "", max_results: int = 10) -> Any:
    """List conversation threads. Optional Gmail query syntax for filtering."""
    return tools["gmail"].list_threads(query if query else None, max_results)


@app.tool()
def gmail_list_labels() -> Any:
    """List all Gmail labels."""
    return tools["gmail"].list_labels()


@app.tool()
def gmail_create_draft(to: str, subject: str, body: str, cc: str = "") -> Any:
    """Create an email draft."""
    return tools["gmail"].create_draft(to, subject, body, cc if cc else None)


@app.tool()
def gmail_send_email(to: str, subject: str, body: str, cc: str = "", confirm: bool = False) -> Any:
    """Send an email. Set confirm=true to actually send."""
    return tools["gmail"].send_email(to, subject, body, cc if cc else None, confirm)


# Calendar tools
@app.tool()
def calendar_list_calendars() -> Any:
    """List accessible calendars."""
    return tools["calendar"].list_calendars()


@app.tool()
def calendar_list_events(calendar_id: str = "", start_time: str = "", end_time: str = "",
                        max_results: int = 10, query: str = "") -> Any:
    """List calendar events. Times in ISO 8601 format."""
    return tools["calendar"].list_events(
        calendar_id if calendar_id else None,
        start_time if start_time else None,
        end_time if end_time else None,
        max_results,
        query if query else None
    )


@app.tool()
def calendar_get_event(calendar_id: str = "", event_id: str = "") -> Any:
    """Get event details."""
    return tools["calendar"].get_event(calendar_id if calendar_id else None, event_id)


@app.tool()
def calendar_create_event(summary: str, start_time: str, end_time: str,
                         description: str = "", location: str = "",
                         attendees: str = "", calendar_id: str = "",
                         confirm: bool = False) -> Any:
    """Create a calendar event. Attendees as comma-separated emails."""
    attendee_list = [a.strip() for a in attendees.split(",")] if attendees else None
    return tools["calendar"].create_event(
        summary, start_time, end_time,
        description if description else None,
        location if location else None,
        attendee_list,
        calendar_id if calendar_id else None,
        confirm
    )


@app.tool()
def calendar_delete_event(calendar_id: str = "", event_id: str = "", confirm: bool = False) -> Any:
    """Delete a calendar event."""
    return tools["calendar"].delete_event(
        calendar_id if calendar_id else None, event_id, confirm
    )


# Sheets tools
@app.tool()
def sheets_search_spreadsheets(query: str, max_results: int = 10) -> Any:
    """Search for spreadsheets by name."""
    return tools["sheets"].search_spreadsheets(query, max_results)


@app.tool()
def sheets_get_metadata(spreadsheet_id: str) -> Any:
    """Get spreadsheet metadata including sheet names and dimensions."""
    return tools["sheets"].get_spreadsheet_metadata(spreadsheet_id)


@app.tool()
def sheets_read_range(spreadsheet_id: str, range_name: str) -> Any:
    """Read values from a spreadsheet range (e.g., 'Sheet1!A1:C10')."""
    return tools["sheets"].read_range(spreadsheet_id, range_name)


@app.tool()
def sheets_write_range(spreadsheet_id: str, range_name: str, values_json: str,
                      confirm: bool = False) -> Any:
    """Write values to a spreadsheet range. values_json is a JSON array of arrays."""
    try:
        values = json.loads(values_json)
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON: {e}"}
    return tools["sheets"].write_range(spreadsheet_id, range_name, values, confirm)


@app.tool()
def sheets_append_rows(spreadsheet_id: str, range_name: str, values_json: str,
                      confirm: bool = False) -> Any:
    """Append rows to a spreadsheet. values_json is a JSON array of arrays."""
    try:
        values = json.loads(values_json)
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON: {e}"}
    return tools["sheets"].append_rows(spreadsheet_id, range_name, values, confirm)


@app.tool()
def sheets_create_spreadsheet(title: str, confirm: bool = False) -> Any:
    """Create a new spreadsheet."""
    return tools["sheets"].create_spreadsheet(title, confirm)


# Slides tools
@app.tool()
def slides_search_presentations(query: str, max_results: int = 10) -> Any:
    """Search for presentations by name."""
    return tools["slides"].search_presentations(query, max_results)


@app.tool()
def slides_get_presentation(presentation_id: str) -> Any:
    """Get presentation metadata and slide list."""
    return tools["slides"].get_presentation(presentation_id)


@app.tool()
def slides_get_slide_content(presentation_id: str, slide_id: str) -> Any:
    """Get text content of a specific slide."""
    return tools["slides"].get_slide_content(presentation_id, slide_id)


@app.tool()
def slides_create_presentation(title: str, confirm: bool = False) -> Any:
    """Create a new presentation."""
    return tools["slides"].create_presentation(title, confirm)


@app.tool()
def slides_add_slide(presentation_id: str, layout_id: str = "", confirm: bool = False) -> Any:
    """Add a new slide to a presentation."""
    return tools["slides"].add_slide(presentation_id, layout_id if layout_id else None, confirm)


@app.tool()
def slides_insert_text(presentation_id: str, slide_id: str, element_id: str,
                      text: str, confirm: bool = False) -> Any:
    """Insert text into a slide element."""
    return tools["slides"].insert_text(presentation_id, slide_id, element_id, text, confirm)


# Drive tools
@app.tool()
def drive_search_files(query: str, max_results: int = 10) -> Any:
    """Search files using Drive query syntax."""
    return tools["drive"].search_files(query, max_results)


@app.tool()
def drive_list_files(folder_id: str = "", max_results: int = 10) -> Any:
    """List files, optionally within a folder."""
    return tools["drive"].list_files(folder_id if folder_id else None, max_results)


@app.tool()
def drive_get_file_metadata(file_id: str) -> Any:
    """Get file metadata."""
    return tools["drive"].get_file_metadata(file_id)


@app.tool()
def drive_read_file(file_id: str) -> Any:
    """Read file content (text files only)."""
    return tools["drive"].read_file(file_id)


@app.tool()
def drive_create_folder(name: str, parent_id: str = "", confirm: bool = False) -> Any:
    """Create a new folder."""
    return tools["drive"].create_folder(name, parent_id if parent_id else None, confirm)


@app.tool()
def drive_upload_file(file_path: str, name: str = "", folder_id: str = "",
                     confirm: bool = False) -> Any:
    """Upload a file to Drive."""
    return tools["drive"].upload_file(
        file_path, name if name else None,
        folder_id if folder_id else None, confirm
    )


@app.tool()
def drive_rename_file(file_id: str, new_name: str, confirm: bool = False) -> Any:
    """Rename a file."""
    return tools["drive"].rename_file(file_id, new_name, confirm)


@app.tool()
def drive_trash_file(file_id: str, confirm: bool = False) -> Any:
    """Move a file to trash."""
    return tools["drive"].trash_file(file_id, confirm)


@app.tool()
def drive_restore_file(file_id: str, confirm: bool = False) -> Any:
    """Restore a trashed file."""
    return tools["drive"].restore_file(file_id, confirm)


async def run_server():
    """Run the MCP server."""
    logging.basicConfig(level=logging.INFO)

    config = get_config()

    # Validate configuration
    errors = config.validate()
    if errors:
        for error in errors:
            logger.error(error)
        sys.exit(1)

    # Authenticate
    logger.info("Authenticating with Google...")
    credentials = authenticate(config)
    logger.info("Authentication successful")

    # Initialize tools
    init_tools(credentials, config)
    logger.info("Tools initialized")

    # Run server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream)


def main():
    """Entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
