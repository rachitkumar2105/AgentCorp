"""Unit tests for Tool Calling Engine serialization."""
from app.tools.serializer import ToolSerializer


def test_parse_openai_call():
    openai_call = {
        "id": "call_123",
        "type": "function",
        "function": {
            "name": "calculate_tax",
            "arguments": '{"income": 50000, "state": "NY"}'
        }
    }
    
    parsed = ToolSerializer.parse_openai_call(openai_call)
    assert parsed.call_id == "call_123"
    assert parsed.tool_name == "calculate_tax"
    assert parsed.arguments == {"income": 50000, "state": "NY"}
