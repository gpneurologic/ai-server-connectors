"""Tests for configuration."""

import os
from pathlib import Path

from google_workspace_mcp.config import get_config, Config, GoogleConfig, SecurityConfig


def test_get_config():
    """Test getting default configuration."""
    config = get_config()
    assert isinstance(config, Config)
    assert isinstance(config.google, GoogleConfig)
    assert isinstance(config.security, SecurityConfig)


def test_config_validate_missing_credentials():
    """Test validation with missing credentials."""
    config = Config()
    config.google.client_id = ""
    config.google.client_secret = ""
    errors = config.validate()
    assert len(errors) == 2
    assert "GOOGLE_CLIENT_ID is required" in errors
    assert "GOOGLE_CLIENT_SECRET is required" in errors


def test_config_validate_with_credentials():
    """Test validation with credentials."""
    config = Config()
    config.google.client_id = "test_client_id"
    config.google.client_secret = "test_client_secret"
    errors = config.validate()
    assert len(errors) == 0


def test_read_only_default():
    """Test that read-only mode is enabled by default."""
    config = get_config()
    assert config.security.read_only is True


def test_require_confirmation_default():
    """Test that confirmation is required by default."""
    config = get_config()
    assert config.security.require_confirmation is True
