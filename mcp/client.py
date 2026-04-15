"""
MCP Client - Model Context Protocol Client
=======================================
Custom MCP client for connecting to MCP servers.
Supports stdio, HTTP, and WebSocket transports.
"""

import asyncio
import json
import logging
import subprocess
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union
from dataclasses import dataclass, field
from enum import Enum

from .types import (
    MCPRequest, MCPResponse, MCPError, MCPErrorCode,
    MCPToolDefinition, MCPResourceDefinition, MCPPromptDefinition
)

logger = logging.getLogger(__name__)


class TransportType(Enum):
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"
    STREAMABLE_HTTP = "streamable-http"


@dataclass
class MCPConnection:
    transport: TransportType
    host: str = "localhost"
    port: int = 8000
    command: Optional[List[str]] = None
    cwd: Optional[str] = None
    
    @property
    def url(self) -> str:
        if self.transport in (TransportType.HTTP, TransportType.STREAMABLE_HTTP):
            return f"http://{self.host}:{self.port}"
        return ""


class MCPClient:
    """
    MCP Client for connecting to MCP servers and invoking tools.
    """
    
    def __init__(self, connection: Optional[MCPConnection] = None):
        self.connection = connection
        self._tools: Dict[str, MCPToolDefinition] = {}
        self._resources: Dict[str, MCPResourceDefinition] = {}
        self._prompts: Dict[str, MCPPromptDefinition] = {}
        self._capabilities: Dict[str, Any] = {}
        self._session_id: Optional[str] = None
        self._server_process: Optional[subprocess.Popen] = None
        self._stdin: Optional[asyncio.StreamReader] = None
        self._stdout: Optional[asyncio.StreamWriter] = None
    
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        if not self.connection:
            logger.error("No connection configured")
            return False
        
        try:
            if self.connection.transport == TransportType.STDIO:
                return await self._connect_stdio()
            elif self.connection.transport == TransportType.HTTP:
                return await self._connect_http()
            elif self.connection.transport == TransportType.STREAMABLE_HTTP:
                return await self._connect_streamable_http()
            else:
                logger.error(f"Unsupported transport: {self.connection.transport}")
                return False
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    async def _connect_stdio(self) -> bool:
        """Connect via stdio."""
        if not self.connection.command:
            logger.error("No command configured for stdio")
            return False
        
        try:
            self._server_process = subprocess.Popen(
                self.connection.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.connection.cwd
            )
            self._stdin = self._server_process.stdin
            self._stdout = self._server_process.stdout
            
            await self._initialize()
            return True
        except Exception as e:
            logger.error(f"stdio connection failed: {e}")
            return False
    
    async def _connect_http(self) -> bool:
        """Connect via HTTP."""
        import aiohttp
        self._http_session = aiohttp.ClientSession()
        await self._initialize()
        return True
    
    async def _connect_streamable_http(self) -> bool:
        """Connect via Streamable HTTP."""
        return await self._connect_http()
    
    async def _initialize(self) -> bool:
        """Send initialize request."""
        result = await self.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            },
            "clientInfo": {
                "name": "autocoder",
                "version": "1.0.0"
            }
        })
        
        if result and not result.is_error():
            self._capabilities = result.result.get("capabilities", {}) if result.result else {}
            self._session_id = result.result.get("protocolVersion") if result.result else None
            await self.request("initialized", {})
            return True
        return False
    
    async def request(
        self, 
        method: str, 
        params: Optional[Dict] = None,
        timeout: float = 30.0
    ) -> Optional[MCPResponse]:
        """Send a request to the server."""
        request = MCPRequest.create(method, params)
        
        try:
            if self.connection.transport == TransportType.STDIO:
                return await self._send_stdio_request(request, timeout)
            else:
                return await self._send_http_request(request, timeout)
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCode.INTERNAL_ERROR.value,
                    message=str(e)
                )
            )
    
    async def _send_stdio_request(self, request: MCPRequest, timeout: float) -> MCPResponse:
        """Send request via stdio."""
        if not self._stdin or not self._stdout:
            raise RuntimeError("Not connected")
        
        request_data = request.to_dict()
        request_json = json.dumps(request_data) + "\n"
        self._stdin.write(request_json.encode())
        self._stdin.flush()
        
        response_line = self._stdout.readline()
        if not response_line:
            raise RuntimeError("No response from server")
        
        response_data = json.loads(response_line.decode())
        return MCPResponse.from_dict(response_data)
    
    async def _send_http_request(self, request: MCPRequest, timeout: float) -> MCPResponse:
        """Send request via HTTP."""
        import aiohttp
        
        url = f"{self.connection.url}/mcp"
        async with self._http_session.post(url, json=request.to_dict()) as resp:
            response_data = await resp.json()
            return MCPResponse.from_dict(response_data)
    
    async def call_tool(
        self, 
        name: str, 
        arguments: Optional[Dict] = None
    ) -> Any:
        """Call a tool on the server."""
        result = await self.request("tools/call", {
            "name": name,
            "arguments": arguments or {}
        })
        
        if result and result.result:
            return result.result.get("content", [])
        return None
    
    async def list_tools(self) -> List[MCPToolDefinition]:
        """List available tools."""
        result = await self.request("tools/list")
        
        if result and result.result:
            tools = result.result.get("tools", [])
            self._tools = {
                t["name"]: MCPToolDefinition(
                    name=t["name"],
                    description=t.get("description", ""),
                    input_schema=t.get("inputSchema", {})
                )
                for t in tools
            }
            return list(self._tools.values())
        return []
    
    async def list_resources(self) -> List[MCPResourceDefinition]:
        """List available resources."""
        result = await self.request("resources/list")
        
        if result and result.result:
            resources = result.result.get("resources", [])
            self._resources = {
                r["uri"]: MCPResourceDefinition(
                    uri=r["uri"],
                    name=r["name"],
                    description=r.get("description"),
                    mime_type=r.get("mimeType")
                )
                for r in resources
            }
            return list(self._resources.values())
        return []
    
    async def read_resource(self, uri: str) -> Optional[Any]:
        """Read a resource."""
        result = await self.request("resources/read", {"uri": uri})
        
        if result and result.result:
            contents = result.result.get("contents", [])
            if contents:
                return contents[0].get("text") or contents[0].get("blob")
        return None
    
    async def list_prompts(self) -> List[MCPPromptDefinition]:
        """List available prompts."""
        result = await self.request("prompts/list")
        
        if result and result.result:
            prompts = result.result.get("prompts", [])
            self._prompts = {
                p["name"]: MCPPromptDefinition(
                    name=p["name"],
                    description=p.get("description", ""),
                    arguments=p.get("arguments")
                )
                for p in prompts
            }
            return list(self._prompts.values())
        return []
    
    async def get_prompt(self, name: str, arguments: Optional[Dict] = None) -> Optional[str]:
        """Get a prompt."""
        result = await self.request("prompts/get", {
            "name": name,
            "arguments": arguments or {}
        })
        
        if result and result.result:
            messages = result.result.get("messages", [])
            if messages:
                return messages[0].get("content", {}).get("text", "")
        return None
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get server capabilities."""
        return self._capabilities
    
    async def close(self):
        """Close the connection."""
        if self._server_process:
            self._server_process.terminate()
            self._server_process.wait()
        
        if hasattr(self, '_http_session'):
            await self._http_session.close()


class MultiMCPClient:
    """
    Manages multiple MCP server connections.
    """
    
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
    
    async def add_server(
        self, 
        name: str, 
        connection: MCPConnection
    ) -> bool:
        """Add and connect to a server."""
        client = MCPClient(connection)
        if await client.connect():
            self.clients[name] = client
            return True
        return False
    
    async def call_tool(
        self, 
        server: str, 
        tool: str, 
        arguments: Optional[Dict] = None
    ) -> Any:
        """Call a tool on a specific server."""
        client = self.clients.get(server)
        if not client:
            logger.error(f"Unknown server: {server}")
            return None
        return await client.call_tool(tool, arguments)
    
    async def call_tool_any(
        self, 
        tool: str, 
        arguments: Optional[Dict] = None
    ) -> tuple[Optional[str], Any]:
        """Call a tool on first available server that has it."""
        for name, client in self.clients.items():
            if tool in client._tools:
                result = await client.call_tool(tool, arguments)
                return name, result
        return None, None
    
    async def close_all(self):
        """Close all connections."""
        for client in self.clients.values():
            await client.close()
        self.clients.clear()


def create_stdio_connection(command: List[str], cwd: Optional[str] = None) -> MCPConnection:
    """Create a stdio connection."""
    return MCPConnection(
        transport=TransportType.STDIO,
        command=command,
        cwd=cwd
    )


def create_http_connection(host: str = "localhost", port: int = 8000) -> MCPConnection:
    """Create an HTTP connection."""
    return MCPConnection(
        transport=TransportType.HTTP,
        host=host,
        port=port
    )