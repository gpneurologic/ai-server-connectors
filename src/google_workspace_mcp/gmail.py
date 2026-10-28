"""Gmail MCP tools."""

import base64
import email
import logging
import re
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GmailTools:
    """Gmail MCP tool implementations."""

    def __init__(self, credentials, config):
        self.credentials = credentials
        self.config = config
        self.service = build("gmail", "v1", credentials=credentials)

    def search_messages(self, query: str, max_results: Optional[int] = None) -> dict:
        """Search Gmail messages using Gmail query syntax.

        Args:
            query: Gmail search query (e.g., "from:alice@example.com subject:hello")
            max_results: Maximum number of results (default: config max)

        Returns:
            List of message metadata (id, threadId, snippet, date, from, to, subject)
        """
        limit = min(max_results or self.config.security.max_results, 100)

        try:
            response = self.service.users().messages().list(
                userId="me", q=query, maxResults=limit
            ).execute()

            messages = []
            for msg in response.get("messages", []):
                messages.append(self._get_message_metadata(msg["id"]))

            return {
                "success": True,
                "query": query,
                "total": len(messages),
                "messages": messages,
            }

        except HttpError as e:
            logger.error("Gmail search failed: %s", e)
            return {"success": False, "error": str(e)}

    def get_message(self, message_id: str, include_body: bool = False) -> dict:
        """Retrieve a Gmail message.

        Args:
            message_id: Gmail message ID
            include_body: Whether to include the message body (default: False)

        Returns:
            Message metadata and optionally body content
        """
        try:
            if include_body:
                msg = self.service.users().messages().get(
                    userId="me", id=message_id, format="full"
                ).execute()
            else:
                msg = self.service.users().messages().get(
                    userId="me", id=message_id, format="metadata",
                    metadataHeaders=["From", "To", "Subject", "Date"]
                ).execute()

            result = self._get_message_metadata(message_id)

            if include_body:
                body = self._extract_body(msg)
                result["body"] = body[: self.config.security.max_email_body_chars]

            return {"success": True, "message": result}

        except HttpError as e:
            logger.error("Failed to get message %s: %s", message_id, e)
            return {"success": False, "error": str(e)}

    def list_threads(self, query: Optional[str] = None, max_results: Optional[int] = None) -> dict:
        """List conversation threads.

        Args:
            query: Optional Gmail search query
            max_results: Maximum number of results

        Returns:
            List of thread metadata
        """
        limit = min(max_results or self.config.security.max_results, 100)

        try:
            request = self.service.users().threads().list(userId="me", maxResults=limit)
            if query:
                request = request.q(query)

            response = request.execute()
            threads = []

            for thread in response.get("threads", []):
                threads.append({
                    "id": thread["id"],
                    "snippet": thread.get("snippet", ""),
                    "messages": thread.get("messages", []),
                })

            return {
                "success": True,
                "total": len(threads),
                "threads": threads,
            }

        except HttpError as e:
            logger.error("Failed to list threads: %s", e)
            return {"success": False, "error": str(e)}

    def list_labels(self) -> dict:
        """List all Gmail labels.

        Returns:
            List of label objects
        """
        try:
            response = self.service.users().labels().list(userId="me").execute()
            labels = response.get("labels", [])
            return {"success": True, "labels": labels}
        except HttpError as e:
            logger.error("Failed to list labels: %s", e)
            return {"success": False, "error": str(e)}

    def create_draft(self, to: str, subject: str, body: str, cc: Optional[str] = None) -> dict:
        """Create an email draft.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            cc: Optional CC recipients

        Returns:
            Draft metadata
        """
        if self.config.security.read_only:
            return {"success": False, "error": "Gmail is in read-only mode"}

        try:
            message = f"To: {to}\r\nSubject: {subject}\r\n"
            if cc:
                message += f"CC: {cc}\r\n"
            message += f"\r\n{body}\r\n"

            draft = {
                "message": {
                    "raw": base64.urlsafe_b64encode(message.encode("utf-8")).decode("utf-8")
                }
            }

            response = self.service.users().drafts().create(
                userId="me", body=draft
            ).execute()

            return {
                "success": True,
                "draft_id": response["id"],
                "message_id": response["message"]["id"],
            }

        except HttpError as e:
            logger.error("Failed to create draft: %s", e)
            return {"success": False, "error": str(e)}

    def send_email(self, to: str, subject: str, body: str, cc: Optional[str] = None,
                  confirm: bool = False) -> dict:
        """Send an email.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            cc: Optional CC recipients
            confirm: Must be True to actually send (safety)

        Returns:
            Sent message metadata
        """
        if self.config.security.read_only:
            return {"success": False, "error": "Gmail is in read-only mode"}

        if self.config.security.require_confirmation and not confirm:
            return {
                "success": False,
                "error": "Set confirm=true to send email"
            }

        try:
            message = f"To: {to}\r\nSubject: {subject}\r\n"
            if cc:
                message += f"CC: {cc}\r\n"
            message += f"\r\n{body}\r\n"

            draft = {
                "message": {
                    "raw": base64.urlsafe_b64encode(message.encode("utf-8")).decode("utf-8")
                }
            }

            response = self.service.users().messages().send(
                userId="me", body=draft
            ).execute()

            return {
                "success": True,
                "message_id": response["id"],
                "thread_id": response["threadId"],
            }

        except HttpError as e:
            logger.error("Failed to send email: %s", e)
            return {"success": False, "error": str(e)}

    def _get_message_metadata(self, message_id: str) -> dict:
        """Get basic metadata for a message."""
        try:
            msg = self.service.users().messages().get(
                userId="me", id=message_id, format="metadata",
                metadataHeaders=["From", "To", "Cc", "Subject", "Date", "Snippet"]
            ).execute()

            headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}

            return {
                "id": message_id,
                "thread_id": msg.get("threadId", ""),
                "from": headers.get("from", ""),
                "to": headers.get("to", ""),
                "cc": headers.get("cc", ""),
                "subject": headers.get("subject", ""),
                "date": headers.get("date", ""),
                "snippet": msg.get("snippet", ""),
            }
        except HttpError as e:
            logger.error("Failed to get message metadata for %s: %s", message_id, e)
            return {"id": message_id, "error": str(e)}

    def _extract_body(self, message: dict) -> str:
        """Extract plain text body from a message."""
        payload = message.get("payload", {})

        # Check for direct body
        if payload.get("body", {}).get("data"):
            body_data = payload["body"]["data"]
            return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

        # Check parts for text/plain
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain":
                if part.get("body", {}).get("data"):
                    body_data = part["body"]["data"]
                    return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")

        # Fallback: return snippet
        return message.get("snippet", "")
