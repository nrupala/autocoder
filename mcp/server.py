"""
MCP Server - Model Context Protocol Server
=====================================
Custom MCP server implementation for AutoCoder.
Exposes tools, resources, and prompts to MCP clients.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
import uuid

from .types import (
    MCPRequest, MCPResponse, MCPError, MCPErrorCode,
    MCPToolDefinition, MCPResourceDefinition, MCPPromptDefinition,
    TransportType
)

logger = logging.getLogger(__name__)


class MCPTool:
    """Represents an MCP tool."""
    
    def __init__(
        self, 
        name: str, 
        description: str,
        input_schema: Dict[str, Any],
        handler: Optional[Callable[..., Awaitable[Any]]] = None
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.handler = handler
    
    async def call(self, arguments: Dict[str, Any]) -> Any:
        """Call the tool."""
        if self.handler:
            return await self.handler(**arguments)
        return {"status": "not implemented"}


class MCPPromptTemplate:
    """Represents an MCP prompt template."""
    
    def __init__(
        self,
        name: str,
        description: str,
        template: str,
        arguments: Optional[List[Dict[str, Any]]] = None
    ):
        self.name = name
        self.description = description
        self.template = template
        self.arguments = arguments or []
    
    def render(self, arguments: Dict[str, str]) -> str:
        """Render the prompt with arguments."""
        try:
            return self.template.format(**arguments)
        except KeyError as e:
            return f"Error: Missing argument {e}"


class MCPResource:
    """Represents an MCP resource."""
    
    def __init__(
        self,
        uri: str,
        name: str,
        content: str,
        mime_type: Optional[str] = None,
        description: Optional[str] = None
    ):
        self.uri = uri
        self.name = name
        self.content = content
        self.mime_type = mime_type
        self.description = description
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "uri": self.uri,
            "name": self.name,
            "content": {
                "text": self.content
            }
        }
        if self.mime_type:
            result["mimeType"] = self.mime_type
        if self.description:
            result["description"] = self.description
        return result


@dataclass
class MCPServerCapabilities:
    tools: bool = True
    resources: bool = True
    prompts: bool = True
    logging: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tools": {"listChanged": True} if self.tools else {},
            "resources": {"subscribe": True, "listChanged": True} if self.resources else {},
            "prompts": {"listChanged": True} if self.prompts else {},
            "logging": {} if self.logging else {}
        }


class MCPServer:
    """
    MCP Server that exposes tools, resources, and prompts.
    """
    
    def __init__(
        self,
        name: str = "AutoCoder Server",
        version: str = "1.0.0"
    ):
        self.name = name
        self.version = version
        self.capabilities = MCPServerCapabilities()
        self._tools: Dict[str, MCPTool] = {}
        self._resources: Dict[str, MCPResource] = {}
        self._prompts: Dict[str, MCPPromptTemplate] = {}
        self._request_handlers: Dict[str, Callable] = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default RPC method handlers."""
        self._request_handlers = {
            "initialize": self._handle_initialize,
            "initialized": self._handle_initialized,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
            "resources/subscribe": self._handle_resources_subscribe,
            "prompts/list": self._handle_prompts_list,
            "prompts/get": self._handle_prompts_get,
        }
    
    def tool(self, name: str = None):
        """Decorator to register a tool."""
        def decorator(func: Callable) -> MCPTool:
            tool_name = name or func.__name__
            tool = MCPTool(
                name=tool_name,
                description=func.__doc__ or "",
                input_schema={"type": "object"},
                handler=func
            )
            self._tools[tool_name] = tool
            return tool
        return decorator
    
    def resource(self, uri: str, name: str = None):
        """Decorator to register a resource."""
        def decorator(func: Callable) -> MCPResource:
            resource_name = name or func.__name__
            content = func()
            resource = MCPResource(
                uri=uri,
                name=resource_name,
                content=content if isinstance(content, str) else str(content)
            )
            self._resources[uri] = resource
            return resource
        return decorator
    
    def prompt(self, name: str):
        """Decorator to register a prompt."""
        def decorator(func: Callable) -> MCPPromptTemplate:
            prompt = MCPPromptTemplate(
                name=name,
                description=func.__doc__ or "",
                template=func()
            )
            self._prompts[name] = prompt
            return prompt
        return decorator
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle an MCP request."""
        handler = self._request_handlers.get(request.method)
        
        if not handler:
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCode.METHOD_NOT_FOUND.value,
                    message=f"Method not found: {request.method}"
                )
            )
        
        try:
            result = await handler(request.params or {})
            return MCPResponse(id=request.id, result=result)
        except Exception as e:
            logger.error(f"Handler error: {e}")
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCode.INTERNAL_ERROR.value,
                    message=str(e)
                )
            )
    
    async def _handle_initialize(self, params: Dict) -> Dict:
        """Handle initialize request."""
        self._protocol_version = params.get("protocolVersion", "2024-11-05")
        return {
            "protocolVersion": self._protocol_version,
            "capabilities": self.capabilities.to_dict(),
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }
    
    async def _handle_initialized(self, params: Dict) -> None:
        """Handle initialized notification."""
        logger.info("Client initialized")
    
    async def _handle_tools_list(self, params: Dict) -> Dict:
        """Handle tools/list request."""
        tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            }
            for tool in self._tools.values()
        ]
        return {"tools": tools}
    
    async def _handle_tools_call(self, params: Dict) -> Dict:
        """Handle tools/call request."""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        
        result = await tool.call(arguments)
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(result)
                }
            ]
        }
    
    async def _handle_resources_list(self, params: Dict) -> Dict:
        """Handle resources/list request."""
        resources = [
            {
                "uri": r.uri,
                "name": r.name,
                "description": r.description,
                "mimeType": r.mime_type
            }
            for r in self._resources.values()
        ]
        return {"resources": resources}
    
    async def _handle_resources_read(self, params: Dict) -> Dict:
        """Handle resources/read request."""
        uri = params.get("uri")
        resource = self._resources.get(uri)
        
        if not resource:
            raise ValueError(f"Resource not found: {uri}")
        
        return {"contents": [resource.to_dict()]}
    
    async def _handle_resources_subscribe(self, params: Dict) -> Dict:
        """Handle resources/subscribe request."""
        return {}
    
    async def _handle_prompts_list(self, params: Dict) -> Dict:
        """Handle prompts/list request."""
        prompts = [
            {
                "name": p.name,
                "description": p.description,
                "arguments": p.arguments
            }
            for p in self._prompts.values()
        ]
        return {"prompts": prompts}
    
    async def _handle_prompts_get(self, params: Dict) -> Dict:
        """Handle prompts/get request."""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        prompt = self._prompts.get(name)
        if not prompt:
            raise ValueError(f"Prompt not found: {name}")
        
        content = prompt.render(arguments)
        return {
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": content
                    }
                }
            ]
        }


class StdioMCPServer:
    """MCP Server with stdio transport."""
    
    def __init__(self, server: MCPServer):
        self.server = server
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
    
    async def start(self):
        """Start the stdio server."""
        self._reader = asyncio.StreamReader()
        self._writer = asyncio.StreamWriter(asyncio.get_event_loop().loop)
        
        while True:
            try:
                line = await self._reader.readline()
                if not line:
                    break
                
                data = json.loads(line.decode())
                request = MCPRequest.from_dict(data)
                response = await self.server.handle_request(request)
                
                if request.id is not None:
                    self._writer.write(json.dumps(response.to_dict()).encode() + b"\n")
            except Exception as e:
                logger.error(f"Error handling request: {e}")


class HTTPMCPServer:
    """MCP Server with HTTP transport."""
    
    def __init__(self, server: MCPServer, host: str = "0.0.0.0", port: int = 8000):
        self.server = server
        self.host = host
        self.port = port
        self._app = None
    
    async def start(self):
        """Start the HTTP server."""
        try:
            from aiohttp import web
        except ImportError:
            raise ImportError("aiohttp required for HTTP transport")
        
        self._app = web.Application()
        self._app.router.add_post("/mcp", self._handle_mcp)
        self._app.router.add_get("/health", self._handle_health)
        
        runner = web.AppRunner(self._app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"MCP server started on {self.host}:{self.port}")
    
    async def _handle_mcp(self, request) -> web.Response:
        """Handle MCP request."""
        data = await request.json()
        mcp_request = MCPRequest.from_dict(data)
        response = await self.server.handle_request(mcp_request)
        return web.json_response(response.to_dict())
    
    async def _handle_health(self, request) -> web.Response:
        """Handle health check."""
        return web.json_response({"status": "healthy"})


# Convenience decorators
def tool(server: MCPServer, name: str = None):
    """Decorator to register a tool on a server."""
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        t = MCPTool(
            name=tool_name,
            description=func.__doc__ or "",
            input_schema={"type": "object"},
            handler=func
        )
        server._tools[tool_name] = t
        return func
    return decorator


def resource(server: MCPServer, uri: str, name: str = None):
    """Decorator to register a resource."""
    def decorator(func: Callable) -> Callable:
        resource_name = name or func.__name__
        content = func()
        r = MCPResource(
            uri=uri,
            name=resource_name,
            content=content if isinstance(content, str) else str(content)
        )
        server._resources[uri] = r
        return func
    return decorator


def prompt(server: MCPServer, name: str):
    """Decorator to register a prompt."""
    def decorator(func: Callable) -> Callable:
        p = MCPPromptTemplate(
            name=name,
            description=func.__doc__ or "",
            template=func()
        )
        server._prompts[name] = p
        return func
    return decorator