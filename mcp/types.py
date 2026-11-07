# Copyright (c) 2026 AutoCoder Team.
# Licensed under the MIT License - see LICENSE at the repository root.
"""
MCP Types - JSON-RPC 2.0 Protocol Types
================================
AutoCoder's custom implementation of Model Context Protocol types.
Based on JSON-RPC 2.0 specification.
"""

import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


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
    data: Any | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPError":
        return cls(
            code=data.get("code", -32603),
            message=data.get("message", "Internal error"),
            data=data.get("data"),
        )


@dataclass
class MCPRequest:
    method: str
    id: str | int | None
    jsonrpc: str = "2.0"
    params: dict[str, Any] | None = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = {"jsonrpc": self.jsonrpc, "method": self.method, "id": self.id}
        if self.params:
            result["params"] = self.params
        return result

    @classmethod
    def create(
        cls, method: str, params: dict | None = None, id: str | int | None = None
    ) -> "MCPRequest":
        return cls(id=id or str(uuid.uuid4()), method=method, params=params or {})

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPRequest":
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method", ""),
            params=data.get("params", {}),
        )


@dataclass
class MCPResponse:
    id: str | int | None
    jsonrpc: str = "2.0"
    result: Any | None = None
    error: MCPError | None = None

    def is_error(self) -> bool:
        return self.error is not None

    def to_dict(self) -> dict[str, Any]:
        result = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error:
            result["error"] = self.error.to_dict()
        elif self.result is not None:
            result["result"] = self.result
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPResponse":
        error = None
        if "error" in data:
            error = MCPError.from_dict(data["error"])
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            result=data.get("result"),
            error=error,
        )


@dataclass
class MCPMessage:
    request: MCPRequest
    response: MCPResponse | None = None

    def to_json(self) -> str:
        return json.dumps(self.request.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "MCPMessage":
        data = json.loads(json_str)
        return cls(request=MCPRequest.from_dict(data))


@dataclass
class MCPToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


@dataclass
class MCPResourceDefinition:
    uri: str
    name: str
    description: str | None = None
    mime_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
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
    arguments: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {"name": self.name, "description": self.description}
        if self.arguments:
            result["arguments"] = self.arguments
        return result


class MCPTransport(Enum):
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"
    STREAMABLE_HTTP = "streamable-http"
