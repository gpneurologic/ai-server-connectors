"""Google OAuth 2.0 authentication."""

import json
import logging
import os
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)

# Base scopes for all services
BASE_SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
]

# Service-specific scopes (read-only)
GMAIL_SCOPES_READONLY = [
    "https://www.googleapis.com/auth/gmail.readonly",
]

CALENDAR_SCOPES_READONLY = [
    "https://www.googleapis.com/auth/calendar.readonly",
]

SHEETS_SCOPES_READONLY = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

SLIDES_SCOPES_READONLY = [
    "https://www.googleapis.com/auth/presentations.readonly",
]

DRIVE_SCOPES_READONLY = [
    "https://www.googleapis.com/auth/drive.readonly",
]

# Service-specific scopes (read-write)
GMAIL_SCOPES_READWRITE = [
    "https://www.googleapis.com/auth/gmail.modify",
]

CALENDAR_SCOPES_READWRITE = [
    "https://www.googleapis.com/auth/calendar",
]

SHEETS_SCOPES_READWRITE = [
    "https://www.googleapis.com/auth/spreadsheets",
]

SLIDES_SCOPES_READWRITE = [
    "https://www.googleapis.com/auth/presentations",
]

DRIVE_SCOPES_READWRITE = [
    "https://www.googleapis.com/auth/drive",
]


def get_scopes(config) -> list[str]:
    """Determine OAuth scopes based on configuration."""
    scopes = list(BASE_SCOPES)

    if config.services.gmail:
        if config.security.read_only:
            scopes.extend(GMAIL_SCOPES_READONLY)
        else:
            scopes.extend(GMAIL_SCOPES_READWRITE)

    if config.services.calendar:
        if config.security.read_only:
            scopes.extend(CALENDAR_SCOPES_READONLY)
        else:
            scopes.extend(CALENDAR_SCOPES_READWRITE)

    if config.services.sheets:
        if config.security.read_only:
            scopes.extend(SHEETS_SCOPES_READONLY)
        else:
            scopes.extend(SHEETS_SCOPES_READWRITE)

    if config.services.slides:
        if config.security.read_only:
            scopes.extend(SLIDES_SCOPES_READONLY)
        else:
            scopes.extend(SLIDES_SCOPES_READWRITE)

    if config.services.drive:
        if config.security.read_only:
            scopes.extend(DRIVE_SCOPES_READONLY)
        else:
            scopes.extend(DRIVE_SCOPES_READWRITE)

    return scopes


def load_credentials(token_path: Path) -> Optional[Credentials]:
    """Load existing OAuth credentials from file."""
    if not token_path.exists():
        return None

    try:
        with open(token_path, "r") as f:
            token_data = json.load(f)
        return Credentials.from_authorized_user_info(token_data)
    except Exception as e:
        logger.warning("Failed to load credentials from %s: %s", token_path, e)
        return None


def save_credentials(credentials: Credentials, token_path: Path) -> None:
    """Save OAuth credentials to file with restrictive permissions."""
    token_path.parent.mkdir(parents=True, exist_ok=True)

    token_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }

    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=2)

    # Set restrictive permissions (600)
    try:
        os.chmod(token_path, 0o600)
    except OSError as e:
        logger.warning("Failed to set permissions on %s: %s", token_path, e)


def refresh_credentials(credentials: Credentials) -> bool:
    """Refresh expired OAuth credentials."""
    try:
        credentials.refresh(Request())
        return True
    except Exception as e:
        logger.error("Failed to refresh credentials: %s", e)
        return False


def authenticate(config) -> Credentials:
    """Perform OAuth authentication and return credentials."""
    token_path = config.google.token_path
    scopes = get_scopes(config)

    # Try to load existing credentials
    credentials = load_credentials(token_path)

    if credentials:
        # Check if token is expired and refresh if needed
        if credentials.expired and credentials.refresh_token:
            logger.info("Refreshing expired OAuth token")
            if not refresh_credentials(credentials):
                logger.warning("Token refresh failed, re-authentication required")
                credentials = None
        elif credentials.expired:
            logger.warning("Token expired and no refresh token available")
            credentials = None

    if credentials and credentials.valid:
        logger.info("Using existing valid OAuth credentials")
        return credentials

    # Need to authenticate
    logger.info("Starting OAuth authentication flow")

    # Check for service account credentials
    if config.google.credentials_path and config.google.credentials_path.exists():
        logger.info("Using service account credentials")
        # Service account flow would go here
        pass

    # Interactive OAuth flow
    flow = InstalledAppFlow.from_client_config(
        {
            "client_id": config.google.client_id,
            "client_secret": config.google.client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        },
        scopes=scopes,
        redirect_uri=config.google.redirect_uri,
    )

    credentials = flow.run_local(
        port=8080,
        open_browser=True,
        authorization_prompt_message="Open the following URL in your browser to authenticate:",
    )

    # Save credentials
    save_credentials(credentials, token_path)
    logger.info("OAuth credentials saved to %s", token_path)

    return credentials
