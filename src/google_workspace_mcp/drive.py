"""Google Drive MCP tools."""

import logging
import mimetypes
from pathlib import Path
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)


class DriveTools:
    """Google Drive MCP tool implementations."""

    def __init__(self, credentials, config):
        self.credentials = credentials
        self.config = config
        self.service = build("drive", "v3", credentials=credentials)

    def search_files(self, query: str, max_results: Optional[int] = None) -> dict:
        """Search files using Drive query syntax."""
        limit = min(max_results or self.config.security.max_results, 100)

        try:
            response = self.service.files().list(
                q=query,
                pageSize=limit,
                fields="files(id,name,mimeType,size,modifiedTime,createdTime,owners,webViewLink)",
                orderBy="modifiedTime desc",
            ).execute()

            files = []
            for f in response.get("files", []):
                files.append({
                    "id": f["id"],
                    "name": f["name"],
                    "mime_type": f["mimeType"],
                    "size": f.get("size"),
                    "modified_time": f.get("modifiedTime"),
                    "created_time": f.get("createdTime"),
                    "owners": [o.get("emailAddress", "") for o in f.get("owners", [])],
                    "web_view_link": f.get("webViewLink"),
                })

            return {
                "success": True,
                "query": query,
                "total": len(files),
                "files": files,
            }
        except HttpError as e:
            logger.error("Drive search failed: %s", e)
            return {"success": False, "error": str(e)}

    def list_files(self, folder_id: Optional[str] = None, max_results: Optional[int] = None) -> dict:
        """List files, optionally within a folder."""
        if folder_id:
            query = f"'{folder_id}' in parents and trashed=false"
        else:
            query = "trashed=false"

        return self.search_files(query, max_results)

    def get_file_metadata(self, file_id: str) -> dict:
        """Get file metadata."""
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields="id,name,mimeType,size,modifiedTime,createdTime,owners,webViewLink,description",
            ).execute()

            return {
                "success": True,
                "file": {
                    "id": file["id"],
                    "name": file["name"],
                    "mime_type": file["mimeType"],
                    "size": file.get("size"),
                    "modified_time": file.get("modifiedTime"),
                    "created_time": file.get("createdTime"),
                    "owners": [o.get("emailAddress", "") for o in file.get("owners", [])],
                    "web_view_link": file.get("webViewLink"),
                    "description": file.get("description"),
                }
            }
        except HttpError as e:
            logger.error("Failed to get file metadata: %s", e)
            return {"success": False, "error": str(e)}

    def read_file(self, file_id: str) -> dict:
        """Read file content (text files only)."""
        try:
            metadata = self.service.files().get(
                fileId=file_id,
                fields="mimeType,name,size",
            ).execute()

            mime_type = metadata["mimeType"]
            if not mime_type.startswith("text/") and mime_type not in [
                "application/json", "application/xml", "application/csv"
            ]:
                return {
                    "success": False,
                    "error": f"Cannot read {mime_type} as text"
                }

            request = self.service.files().get_media(fileId=file_id)
            import io
            fh = io.BytesIO()
            from googleapiclient.http import MediaIoBaseDownload
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

            fh.seek(0)
            content = fh.read().decode("utf-8", errors="replace")
            return {
                "success": True,
                "file_id": file_id,
                "name": metadata["name"],
                "mime_type": mime_type,
                "content": content,
            }
        except HttpError as e:
            logger.error("Failed to read file: %s", e)
            return {"success": False, "error": str(e)}

    def create_folder(self, name: str, parent_id: Optional[str] = None,
                     confirm: bool = False) -> dict:
        """Create a new folder."""
        if self.config.security.read_only:
            return {"success": False, "error": "Drive is in read-only mode"}
        if self.config.security.require_confirmation and not confirm:
            return {"success": False, "error": "Set confirm=true to create folder"}

        try:
            body = {
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            if parent_id:
                body["parents"] = [parent_id]

            folder = self.service.files().create(
                body=body,
                fields="id,name,webViewLink",
            ).execute()

            return {
                "success": True,
                "folder_id": folder["id"],
                "name": folder["name"],
                "web_view_link": folder.get("webViewLink"),
            }
        except HttpError as e:
            logger.error("Failed to create folder: %s", e)
            return {"success": False, "error": str(e)}

    def upload_file(self, file_path: str, name: Optional[str] = None,
                   folder_id: Optional[str] = None, confirm: bool = False) -> dict:
        """Upload a file to Drive."""
        if self.config.security.read_only:
            return {"success": False, "error": "Drive is in read-only mode"}
        if self.config.security.require_confirmation and not confirm:
            return {"success": False, "error": "Set confirm=true to upload file"}

        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        try:
            mime_type, _ = mimetypes.guess_type(str(path))
            if not mime_type:
                mime_type = "application/octet-stream"

            body = {"name": name or path.name, "mimeType": mime_type}
            if folder_id:
                body["parents"] = [folder_id]

            media = MediaFileUpload(str(path), mimetype=mime_type, resumable=True)
            file = self.service.files().create(
                body=body,
                media_body=media,
                fields="id,name,mimeType,size,webViewLink",
            ).execute()

            return {
                "success": True,
                "file_id": file["id"],
                "name": file["name"],
                "mime_type": file["mimeType"],
                "size": file.get("size"),
                "web_view_link": file.get("webViewLink"),
            }
        except HttpError as e:
            logger.error("Failed to upload file: %s", e)
            return {"success": False, "error": str(e)}

    def rename_file(self, file_id: str, new_name: str, confirm: bool = False) -> dict:
        """Rename a file."""
        if self.config.security.read_only:
            return {"success": False, "error": "Drive is in read-only mode"}
        if self.config.security.require_confirmation and not confirm:
            return {"success": False, "error": "Set confirm=true to rename file"}

        try:
            file = self.service.files().update(
                fileId=file_id,
                body={"name": new_name},
                fields="id,name",
            ).execute()

            return {"success": True, "file_id": file_id, "name": file["name"]}
        except HttpError as e:
            logger.error("Failed to rename file: %s", e)
            return {"success": False, "error": str(e)}

    def trash_file(self, file_id: str, confirm: bool = False) -> dict:
        """Move a file to trash."""
        if self.config.security.read_only:
            return {"success": False, "error": "Drive is in read-only mode"}
        if self.config.security.require_confirmation and not confirm:
            return {"success": False, "error": "Set confirm=true to trash file"}

        try:
            self.service.files().trash(fileId=file_id).execute()
            return {"success": True, "file_id": file_id}
        except HttpError as e:
            logger.error("Failed to trash file: %s", e)
            return {"success": False, "error": str(e)}

    def restore_file(self, file_id: str, confirm: bool = False) -> dict:
        """Restore a trashed file."""
        if self.config.security.read_only:
            return {"success": False, "error": "Drive is in read-only mode"}
        if self.config.security.require_confirmation and not confirm:
            return {"success": False, "error": "Set confirm=true to restore file"}

        try:
            self.service.files().untrash(fileId=file_id).execute()
            return {"success": True, "file_id": file_id}
        except HttpError as e:
            logger.error("Failed to restore file: %s", e)
            return {"success": False, "error": str(e)}
