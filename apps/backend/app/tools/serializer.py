"""
Tool Calling Engine — Serializer.

Translates tool definitions and schemas to and from provider formats.
"""

from __future__ import annotations

import json
from typing import Any
from app.schemas.tool_execution import ToolCallRequest, ToolCallResult, ToolMetadata


class ToolSerializer:
    """
    Serializes and deserializes tool structures between internal models
    and provider-specific formats (Groq, OpenAI, etc.).
    """

    @staticmethod
    def to_openai_format(metadata: ToolMetadata) -> dict[str, Any]:
        """
        Convert internal tool metadata into the standard OpenAI tool definition format.
        """
        properties_dict: dict[str, Any] = {}
        for name, prop in metadata.parameters.properties.items():
            prop_dict: dict[str, Any] = {"type": prop.type}
            if prop.description:
                prop_dict["description"] = prop.description
            if prop.enum:
                prop_dict["enum"] = prop.enum
            properties_dict[name] = prop_dict

        return {
            "type": "function",
            "function": {
                "name": metadata.name,
                "description": metadata.description,
                "parameters": {
                    "type": "object",
                    "properties": properties_dict,
                    "required": metadata.parameters.required,
                },
            },
        }

    @staticmethod
    def parse_openai_call(tool_call: dict[str, Any]) -> ToolCallRequest:
        """
        Parse an OpenAI format tool call dictionary into our internal ToolCallRequest.
        """
        call_id = tool_call.get("id", "")
        function = tool_call.get("function", {})
        name = function.get("name", "")
        args_str = function.get("arguments", "{}")

        try:
            arguments = json.loads(args_str) if isinstance(args_str, str) else args_str
        except json.JSONDecodeError:
            arguments = {}

        return ToolCallRequest(
            call_id=call_id,
            tool_name=name,
            arguments=arguments,
        )

    @staticmethod
    def to_openai_result(result: ToolCallResult) -> dict[str, Any]:
        """
        Convert our internal ToolCallResult into OpenAI format result message.
        """
        return {
            "role": "tool",
            "tool_call_id": result.call_id,
            "name": result.tool_name,
            "content": result.content,
        }
