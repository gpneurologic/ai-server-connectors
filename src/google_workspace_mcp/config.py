"""Configuration for Google Workspace MCP server."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


@dataclass
class GoogleConfig:
    """Google API configuration."""

    client_id: str = field(default_factory=lambda: os.getenv("GOOGLE_CLIENT_ID", ""))
    client_secret: str = field(default_factory=lambda: os.getenv("GOOGLE_CLIENT_SECRET", ""))
    token_path: Path = field(
        default_factory=lambda: Path(os.getenv("GOOGLE_TOKEN_PATH", "~/.config/google-workspace-mcp/token.json"))
    )
    credentials_path: Optional[Path] = field(
        default_factory=lambda: Path(os.getenv("GOOGLE_CREDENTIALS_PATH", ""))
        if os.getenv("GOOGLE_CREDENTIALS_PATH")
        else None
    )
    redirect_uri: str = field(default_factory=lambda: os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/oauth2callback"))

    def resolve_paths(self) -> None:
        """Expand user home directory in paths."""
        self.token_path = self.token_path.expanduser()
        if self.credentials_path:
            self.credentials_path = self.credentials_path.expanduser()


@dataclass
class SecurityConfig:
    """Security and write policy configuration."""

    read_only: bool = field(default_factory=lambda: os.getenv("MCP_READ_ONLY", "true").lower() == "true")
    require_confirmation: bool = field(
        default_factory=lambda: os.getenv("MCP_REQUIRE_CONFIRMATION", "true").lower() == "true"
    )
    max_results: int = field(default_factory=lambda: int(os.getenv("MCP_MAX_RESULTS", "50")))
    max_email_body_chars: int = field(default_factory=lambda: int(os.getenv("MCP_MAX_EMAIL_BODY_CHARS", "10000")))
    max_file_size_bytes: int = field(default_factory=lambda: int(os.getenv("MCP_MAX_FILE_SIZE_BYTES", "10485760")))  # 10MB
    allowed_mime_types: list[str] = field(
        default_factory=lambda: [
            "text/plain",
            "text/html",
            "text/csv",
            "text/markdown",
            "application/json",
            "application/xml",
            "application/pdf",
            "image/png",
            "image/jpeg",
            "image/gif",
            "application/vnd.google-apps.document",
            "application/vnd.google-apps.spreadsheet",
            "application/vnd.google-apps.presentation",
        ]
    )


@dataclass
class ServiceConfig:
    """Which Google services to enable."""

    gmail: bool = field(default_factory=lambda: os.getenv("MCP_ENABLE_GMAIL", "true").lower() == "true")
    calendar: bool = field(default_factory=lambda: os.getenv("MCP_ENABLE_CALENDAR", "true").lower() == "true")
    sheets: bool = field(default_factory=lambda: os.getenv("MCP_ENABLE_SHEETS", "true").lower() == "true")
    slides: bool = field(default_factory=lambda: os.getenv("MCP_ENABLE_SLIDES", "true").lower() == "true")
    drive: bool = field(default_factory=lambda: os.getenv("MCP_ENABLE_DRIVE", "true").lower() == "true")


@dataclass
class Config:
    """Main configuration object."""

    google: GoogleConfig = field(default_factory=GoogleConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    services: ServiceConfig = field(default_factory=ServiceConfig)
    log_level: str = field(default_factory=lambda: os.getenv("MCP_LOG_LEVEL", "INFO"))

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        if not self.google.client_id:
            errors.append("GOOGLE_CLIENT_ID is required")
        if not self.google.client_secret:
            errors.append("GOOGLE_CLIENT_SECRET is required")
        return errors


def get_config() -> Config:
    """Get the application configuration."""
    config = Config()
    config.google.resolve_paths()
    return config
