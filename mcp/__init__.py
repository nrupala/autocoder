# Copyright (c) 2026 AutoCoder Team.
# Licensed under the MIT License - see LICENSE at the repository root.
"""
AutoCoder MCP (Model Context Protocol) Implementation
=====================================================
Custom MCP client/server implementation for AutoCoder ecosystem.
Built from scratch with JSON-RPC 2.0 protocol.
"""

from .client import MCPClient, MCPConnection
from .server import MCPPromptTemplate, MCPResource, MCPServer, MCPTool
from .types import MCPError, MCPMessage, MCPRequest, MCPResponse

__all__ = [
    "MCPClient",
    "MCPConnection",
    "MCPServer",
    "MCPTool",
    "MCPResource",
    "MCPPromptTemplate",
    "MCPMessage",
    "MCPRequest",
    "MCPResponse",
    "MCPError",
]
