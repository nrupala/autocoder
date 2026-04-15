"""
MCP Types - JSON-RPC 2.0 Protocol Types
================================
AutoCoder's custom implementation of Model Context Protocol types.
Based on JSON-RPC 2.0 specification.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid


class MCPErrorCode(Enum):
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


@dataclass
class MCPError:
    code: int
    message: str
    data: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPError":
        return cls(
            code=data.get("code", -32603),
            message=data.get("message", "Internal error"),
            data=data.get("data")
        )


@dataclass
class MCPRequest:
    jsonrpc: str = "2.0"
    id: Union[str, int, None]
    method: str
    params: Optional[Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result = {"jsonrpc": self.jsonrpc, "method": self.method, "id": self.id}
        if self.params:
            result["params"] = self.params
        return result

    @classmethod
    def create(cls, method: str, params: Optional[Dict] = None, id: Union[str, int, None] = None) -> "MCPRequest":
        return cls(
            id=id or str(uuid.uuid4()),
            method=method,
            params=params or {}
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPRequest":
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method", ""),
            params=data.get("params", {})
        )


@dataclass
class MCPResponse:
    jsonrpc: str = "2.0"
    id: Union[str, int, None]
    result: Optional[Any] = None
    error: Optional[MCPError] = None

    def is_error(self) -> bool:
        return self.error is not None

    def to_dict(self) -> Dict[str, Any]:
        result = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error:
            result["error"] = self.error.to_dict()
        elif self.result is not None:
            result["result"] = self.result
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPResponse":
        error = None
        if "error" in data:
            error = MCPError.from_dict(data["error"])
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            result=data.get("result"),
            error=error
        )


@dataclass 
class MCPMessage:
    request: MCPRequest
    response: Optional[MCPResponse] = None

    def to_json(self) -> str:
        return json.dumps(self.request.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "MCPMessage":
        data = json.loads(json_str)
        return cls(
            request=MCPRequest.from_dict(data)
        )


@dataclass
class MCPToolDefinition:
    name: str
    description: str
    input_schema: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }


@dataclass
class MCPResourceDefinition:
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"uri": self.uri, "name": self.name}
        if self.description:
            result["description"] = self.description
        if self.mime_type:
            result["mimeType"] = self.mime_type
        return result


@dataclass
class MCPPromptDefinition:
    name: str
    description: str
    arguments: Optional[List[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"name": self.name, "description": self.description}
        if self.arguments:
            result["arguments"] = self.arguments
        return result


class MCPTransport(Enum):
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"
    STREAMABLE_HTTP = "streamable-http"