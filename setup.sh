#!/bin/bash
# Setup script for Google Workspace MCP Server

set -e

echo "=== Google Workspace MCP Server Setup ==="

# Check Python version
python3 --version

# Install dependencies
echo "Installing dependencies..."
pip install -e . --break-system-packages

# Create token directory
mkdir -p ~/.config/google-workspace-mcp
chmod 700 ~/.config/google-workspace-mcp

# Check for .env file
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env with your Google OAuth credentials."
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To run the MCP server:"
echo "  google-workspace-mcp"
echo ""
echo "To configure OpenCode, add to ~/.config/opencode/opencode.json:"
echo '  "mcp": {'
echo '    "servers": {'
echo '      "google-workspace": {'
echo '        "type": "local",'
echo '        "command": ["google-workspace-mcp"]'
echo '      }'
echo '    }'
echo '  }'
