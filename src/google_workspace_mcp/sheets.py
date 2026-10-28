"""Google Sheets MCP tools."""

import logging
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class SheetsTools:
    """Google Sheets MCP tool implementations."""

    def __init__(self, credentials, config):
        self.credentials = credentials
        self.config = config
        self.service = build("sheets", "v4", credentials=credentials)

    def search_spreadsheets(self, query: str, max_results: Optional[int] = None) -> dict:
        """Search for spreadsheets via Drive API."""
        from .drive import DriveTools
        drive = DriveTools(self.credentials, self.config)
        return drive.search_files(f"'{query}' and mimeType='application/vnd.google-apps.spreadsheet'", max_results)

    def get_spreadsheet_metadata(self, spreadsheet_id: str) -> dict:
        """Get spreadsheet metadata including sheet names and dimensions."""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                includeGridData=False,
            ).execute()

            sheets = []
            for sheet in spreadsheet.get("sheets", []):
                props = sheet.get("properties", {})
                grid = sheet.get("gridProperties", {})
                sheets.append({
                    "sheet_id": props.get("sheetId"),
                    "title": props.get("title"),
                    "index": props.get("index"),
                    "row_count": grid.get("rowCount"),
                    "column_count": grid.get("columnCount"),
                })

            return {
                "success": True,
                "spreadsheet_id": spreadsheet_id,
                "title": spreadsheet.get("properties", {}).get("title"),
                "sheets": sheets,
            }
        except HttpError as e:
            logger.error("Failed to get spreadsheet metadata: %s", e)
            return {"success": False, "error": str(e)}

    def read_range(self, spreadsheet_id: str, range_name: str) -> dict:
        """Read values from a spreadsheet range."""
        try:
            response = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name,
            ).execute()

            values = response.get("values", [])
            return {
                "success": True,
                "spreadsheet_id": spreadsheet_id,
                "range": range_name,
                "row_count": len(values),
                "column_count": len(values[0]) if values else 0,
                "values": values,
            }
        except HttpError as e:
            logger.error("Failed to read range %s: %s", range_name, e)
            return {"success": False, "error": str(e)}

    def write_range(self, spreadsheet_id: str, range_name: str, values: list,
                   confirm: bool = False) -> dict:
        """Write values to a spreadsheet range."""
        if self.config.security.read_only:
            return {"success": False, "error": "Sheets is in read-only mode"}
        if self.config.security.require_confirmation and not confirm:
            return {"success": False, "error": "Set confirm=true to write values"}

        try:
            body = {"values": values}
            response = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body,
            ).execute()

            return {
                "success": True,
                "spreadsheet_id": spreadsheet_id,
                "range": range_name,
                "updated_rows": response.get("updatedRows"),
                "updated_columns": response.get("updatedColumns"),
                "updated_cells": response.get("updatedCells"),
            }
        except HttpError as e:
            logger.error("Failed to write range %s: %s", range_name, e)
            return {"success": False, "error": str(e)}

    def append_rows(self, spreadsheet_id: str, range_name: str, values: list,
                   confirm: bool = False) -> dict:
        """Append rows to a spreadsheet."""
        if self.config.security.read_only:
            return {"success": False, "error": "Sheets is in read-only mode"}
        if self.config.security.require_confirmation and not confirm:
            return {"success": False, "error": "Set confirm=true to append rows"}

        try:
            body = {"values": values}
            response = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body,
            ).execute()

            return {
                "success": True,
                "spreadsheet_id": spreadsheet_id,
                "range": range_name,
                "updates": response.get("updates"),
            }
        except HttpError as e:
            logger.error("Failed to append rows: %s", e)
            return {"success": False, "error": str(e)}

    def create_spreadsheet(self, title: str, confirm: bool = False) -> dict:
        """Create a new spreadsheet."""
        if self.config.security.read_only:
            return {"success": False, "error": "Sheets is in read-only mode"}
        if self.config.security.require_confirmation and not confirm:
            return {"success": False, "error": "Set confirm=true to create spreadsheet"}

        try:
            body = {"properties": {"title": title}}
            spreadsheet = self.service.spreadsheets().create(body=body).execute()

            return {
                "success": True,
                "spreadsheet_id": spreadsheet["spreadsheetId"],
                "title": spreadsheet["properties"]["title"],
                "url": spreadsheet["spreadsheetUrl"],
            }
        except HttpError as e:
            logger.error("Failed to create spreadsheet: %s", e)
            return {"success": False, "error": str(e)}
