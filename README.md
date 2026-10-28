# Google Workspace MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with Google Workspace services: Gmail, Calendar, Sheets, Slides, and Drive.

## Features

- **Gmail**: Search messages, read emails, list threads, manage labels, create drafts, send emails
- **Calendar**: List calendars, view events, create/update/delete events, check availability
- **Sheets**: Search spreadsheets, read/write cell ranges, append rows, create spreadsheets
- **Slides**: Search presentations, view slide content, create presentations, add/edit slides
- **Drive**: Search files, list files, read file content, upload files, manage folders

## Installation

```bash
pip install -e .
```

## Configuration

Create a `.env` file with your Google OAuth credentials:

```env
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_TOKEN_PATH=~/.config/google-workspace-mcp/token.json
MCP_READ_ONLY=true
MCP_REQUIRE_CONFIRMATION=true
```

## Running the Server

```bash
google-workspace-mcp
```

The server communicates via stdio using the MCP protocol.

## OpenCode Integration

Add to your OpenCode configuration (`~/.config/opencode/opencode.json`):

```json
{
  "mcp": {
    "servers": {
      "google-workspace": {
        "type": "local",
        "command": ["google-workspace-mcp"],
        "environment": {
          "GOOGLE_CLIENT_ID": "{env:GOOGLE_CLIENT_ID}",
          "GOOGLE_CLIENT_SECRET": "{env:GOOGLE_CLIENT_SECRET}"
        }
      }
    }
  }
}
```

## Available Tools

### Gmail
- `gmail_search_messages(query, max_results)` - Search emails
- `gmail_get_message(message_id, include_body)` - Get message details
- `gmail_list_threads(query, max_results)` - List conversation threads
- `gmail_list_labels()` - List all labels
- `gmail_create_draft(to, subject, body, cc)` - Create email draft
- `gmail_send_email(to, subject, body, cc, confirm)` - Send email

### Calendar
- `calendar_list_calendars()` - List accessible calendars
- `calendar_list_events(calendar_id, start_time, end_time, max_results, query)` - List events
- `calendar_get_event(calendar_id, event_id)` - Get event details
- `calendar_create_event(summary, start_time, end_time, ...)` - Create event
- `calendar_delete_event(calendar_id, event_id, confirm)` - Delete event

### Sheets
- `sheets_search_spreadsheets(query, max_results)` - Search spreadsheets
- `sheets_get_metadata(spreadsheet_id)` - Get spreadsheet info
- `sheets_read_range(spreadsheet_id, range_name)` - Read cell values
- `sheets_write_range(spreadsheet_id, range_name, values_json, confirm)` - Write values
- `sheets_append_rows(spreadsheet_id, range_name, values_json, confirm)` - Append rows
- `sheets_create_spreadsheet(title, confirm)` - Create spreadsheet

### Slides
- `slides_search_presentations(query, max_results)` - Search presentations
- `slides_get_presentation(presentation_id)` - Get presentation info
- `slides_get_slide_content(presentation_id, slide_id)` - Get slide content
- `slides_create_presentation(title, confirm)` - Create presentation
- `slides_add_slide(presentation_id, layout_id, confirm)` - Add slide
- `slides_insert_text(presentation_id, slide_id, element_id, text, confirm)` - Insert text

### Drive
- `drive_search_files(query, max_results)` - Search files
- `drive_list_files(folder_id, max_results)` - List files
- `drive_get_file_metadata(file_id)` - Get file info
- `drive_read_file(file_id)` - Read file content
- `drive_create_folder(name, parent_id, confirm)` - Create folder
- `drive_upload_file(file_path, name, folder_id, confirm)` - Upload file
- `drive_rename_file(file_id, new_name, confirm)` - Rename file
- `drive_trash_file(file_id, confirm)` - Trash file
- `drive_restore_file(file_id, confirm)` - Restore file

## Security

- OAuth 2.0 with least-privilege scopes
- Read-only mode by default (`MCP_READ_ONLY=true`)
- Confirmation required for write operations (`MCP_REQUIRE_CONFIRMATION=true`)
- Token stored with restrictive file permissions (600)

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check src/
```
