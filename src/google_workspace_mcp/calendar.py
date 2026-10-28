"""Google Calendar MCP tools."""

import logging
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class CalendarTools:
    """Google Calendar MCP tool implementations."""

    def __init__(self, credentials, config):
        self.credentials = credentials
        self.config = config
        self.service = build("calendar", "v3", credentials=credentials)

    def list_calendars(self) -> dict:
        """List accessible calendars."""
        try:
            response = self.service.calendarList().list().execute()
            calendars = []
            for cal in response.get("items", []):
                calendars.append({
                    "id": cal["id"],
                    "summary": cal.get("summary", ""),
                    "description": cal.get("description", ""),
                    "primary": cal.get("primary", False),
                })
            return {"success": True, "calendars": calendars}
        except HttpError as e:
            logger.error("Failed to list calendars: %s", e)
            return {"success": False, "error": str(e)}

    def list_events(self, calendar_id: Optional[str] = None, start_time: Optional[str] = None,
                   end_time: Optional[str] = None, max_results: Optional[int] = None,
                   query: Optional[str] = None) -> dict:
        """List calendar events."""
        limit = min(max_results or self.config.security.max_results, 100)
        calendar_id = calendar_id or "primary"

        try:
            request = self.service.events().list(
                calendarId=calendar_id,
                maxResults=limit,
                singleEvents=True,
                orderBy="startTime",
            )
            if start_time:
                request = request.timeMin(start_time)
            if end_time:
                request = request.timeMax(end_time)
            if query:
                request = request.q(query)

            response = request.execute()
            events = []
            for event in response.get("items", []):
                events.append(self._format_event(event))

            return {
                "success": True,
                "calendar_id": calendar_id,
                "total": len(events),
                "events": events,
            }
        except HttpError as e:
            logger.error("Failed to list events: %s", e)
            return {"success": False, "error": str(e)}

    def get_event(self, calendar_id: Optional[str], event_id: str) -> dict:
        """Get event details."""
        calendar_id = calendar_id or "primary"
        try:
            event = self.service.events().get(
                calendarId=calendar_id, eventId=event_id
            ).execute()
            return {"success": True, "event": self._format_event(event)}
        except HttpError as e:
            logger.error("Failed to get event %s: %s", event_id, e)
            return {"success": False, "error": str(e)}

    def create_event(self, summary: str, start_time: str, end_time: str,
                    description: Optional[str] = None, location: Optional[str] = None,
                    attendees: Optional[list] = None, calendar_id: Optional[str] = None,
                    confirm: bool = False) -> dict:
        """Create a calendar event."""
        if self.config.security.read_only:
            return {"success": False, "error": "Calendar is in read-only mode"}
        if self.config.security.require_confirmation and not confirm:
            return {"success": False, "error": "Set confirm=true to create event"}

        calendar_id = calendar_id or "primary"
        event = {
            "summary": summary,
            "start": {"dateTime": start_time, "timeZone": "UTC"},
            "end": {"dateTime": end_time, "timeZone": "UTC"},
        }
        if description:
            event["description"] = description
        if location:
            event["location"] = location
        if attendees:
            event["attendees"] = [{"email": a} for a in attendees]

        try:
            created = self.service.events().insert(
                calendarId=calendar_id, body=event
            ).execute()
            return {"success": True, "event": self._format_event(created)}
        except HttpError as e:
            logger.error("Failed to create event: %s", e)
            return {"success": False, "error": str(e)}

    def delete_event(self, calendar_id: Optional[str], event_id: str,
                    confirm: bool = False) -> dict:
        """Delete a calendar event."""
        if self.config.security.read_only:
            return {"success": False, "error": "Calendar is in read-only mode"}
        if self.config.security.require_confirmation and not confirm:
            return {"success": False, "error": "Set confirm=true to delete event"}

        calendar_id = calendar_id or "primary"
        try:
            self.service.events().delete(
                calendarId=calendar_id, eventId=event_id
            ).execute()
            return {"success": True, "event_id": event_id}
        except HttpError as e:
            logger.error("Failed to delete event %s: %s", event_id, e)
            return {"success": False, "error": str(e)}

    def _format_event(self, event: dict) -> dict:
        """Format event for output."""
        start = event.get("start", {})
        end = event.get("end", {})
        return {
            "id": event["id"],
            "summary": event.get("summary", ""),
            "description": event.get("description", ""),
            "location": event.get("location", ""),
            "start": start.get("dateTime") or start.get("date"),
            "end": end.get("dateTime") or end.get("date"),
            "status": event.get("status", ""),
            "attendees": [a.get("email", "") for a in event.get("attendees", [])],
            "html_link": event.get("htmlLink", ""),
        }
