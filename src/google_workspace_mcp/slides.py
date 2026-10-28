"""Google Slides MCP tools."""

import logging
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class SlidesTools:
    """Google Slides MCP tool implementations."""

    def __init__(self, credentials, config):
        self.credentials = credentials
        self.config = config
        self.service = build("slides", "v1", credentials=credentials)

    def search_presentations(self, query: str, max_results: Optional[int] = None) -> dict:
        """Search for presentations via Drive API."""
        from .drive import DriveTools
        drive = DriveTools(self.credentials, self.config)
        return drive.search_files(f"'{query}' and mimeType='application/vnd.google-apps.presentation'", max_results)

    def get_presentation(self, presentation_id: str) -> dict:
        """Get presentation metadata and slide list."""
        try:
            presentation = self.service.presentations().get(
                presentationId=presentation_id
            ).execute()

            slides = []
            for slide in presentation.get("slides", []):
                slide_info = {
                    "slide_id": slide["objectId"],
                    "page_type": slide.get("pageType", ""),
                    "layout_id": slide.get("layoutId", ""),
                }
                slides.append(slide_info)

            return {
                "success": True,
                "presentation_id": presentation_id,
                "title": presentation.get("title", ""),
                "slide_count": len(slides),
                "slides": slides,
            }
        except HttpError as e:
            logger.error("Failed to get presentation %s: %s", presentation_id, e)
            return {"success": False, "error": str(e)}

    def get_slide_content(self, presentation_id: str, slide_id: str) -> dict:
        """Get text content of a specific slide."""
        try:
            presentation = self.service.presentations().get(
                presentationId=presentation_id
            ).execute()

            for slide in presentation.get("slides", []):
                if slide["objectId"] == slide_id:
                    elements = []
                    for shape in slide.get("pageElements", []):
                        text = self._extract_text_from_element(shape)
                        if text:
                            elements.append({
                                "element_id": shape.get("objectId"),
                                "type": shape.get("shape", {}).get("type", ""),
                                "text": text,
                            })
                    return {"success": True, "slide_id": slide_id, "elements": elements}

            return {"success": False, "error": f"Slide {slide_id} not found"}
        except HttpError as e:
            logger.error("Failed to get slide content: %s", e)
            return {"success": False, "error": str(e)}

    def create_presentation(self, title: str, confirm: bool = False) -> dict:
        """Create a new presentation."""
        if self.config.security.read_only:
            return {"success": False, "error": "Slides is in read-only mode"}
        if self.config.security.require_confirmation and not confirm:
            return {"success": False, "error": "Set confirm=true to create presentation"}

        try:
            body = {"title": title}
            presentation = self.service.presentations().create(body=body).execute()

            return {
                "success": True,
                "presentation_id": presentation["presentationId"],
                "title": presentation["title"],
                "url": presentation["documentProperties"]["revisionId"],
            }
        except HttpError as e:
            logger.error("Failed to create presentation: %s", e)
            return {"success": False, "error": str(e)}

    def add_slide(self, presentation_id: str, layout_id: Optional[str] = None,
                 confirm: bool = False) -> dict:
        """Add a new slide to a presentation."""
        if self.config.security.read_only:
            return {"success": False, "error": "Slides is in read-only mode"}
        if self.config.security.require_confirmation and not confirm:
            return {"success": False, "error": "Set confirm=true to add slide"}

        try:
            requests = [{"createSlide": {"layoutId": layout_id or ""}}]
            response = self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": requests},
            ).execute()

            slide_id = response["replies"][0]["createSlide"]["objectId"]
            return {"success": True, "slide_id": slide_id}
        except HttpError as e:
            logger.error("Failed to add slide: %s", e)
            return {"success": False, "error": str(e)}

    def insert_text(self, presentation_id: str, slide_id: str, element_id: str,
                   text: str, confirm: bool = False) -> dict:
        """Insert text into a slide element."""
        if self.config.security.read_only:
            return {"success": False, "error": "Slides is in read-only mode"}
        if self.config.security.require_confirmation and not confirm:
            return {"success": False, "error": "Set confirm=true to insert text"}

        try:
            requests = [{
                "insertText": {
                    "objectId": element_id,
                    "text": text,
                }
            }]
            self.service.presentations().batchUpdate(
                presentationId=presentation_id,
                body={"requests": requests},
            ).execute()

            return {"success": True, "element_id": element_id}
        except HttpError as e:
            logger.error("Failed to insert text: %s", e)
            return {"success": False, "error": str(e)}

    def _extract_text_from_element(self, element: dict) -> str:
        """Extract text content from a slide element."""
        shape = element.get("shape", {})
        text = ""

        for text_run in shape.get("text", {}).get("textRuns", []):
            text += text_run.get("text", "")

        return text
