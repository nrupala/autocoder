"""
AutoCoder MCP (Model Context Protocol) Implementation
=====================================================
Custom MCP client/server implementation for AutoCoder ecosystem.
Built from scratch with JSON-RPC 2.0 protocol.
"""

from .client import MCPClient, MCPConnection
from .server import MCPServer, MCPTool, MCPResource, MCPPrompt
from .types import MCPMessage, MCPRequest, MCPResponse, MCPError

__all__ = [
    "MCPClient",
    "MCPConnection", 
    "MCPServer",
    "MCPTool",
    "MCPResource", 
    "MCPPrompt",
    "MCPMessage",
    "MCPRequest", 
    "MCPResponse",
    "MCPError",
]