"""Unit tests for Multi-Agent Message Bus."""
import pytest
from app.multi_agent.message_bus import message_bus


@pytest.mark.anyio
async def test_message_bus_pub_sub():
    session_id = 42
    received = []
    
    async def cb(msg):
        received.append(msg)
        
    message_bus.subscribe(session_id, cb)
    
    # Test publish
    test_msg = {"content": "Hello agent"}
    await message_bus.publish(session_id, test_msg)
    
    assert len(received) == 1
    assert received[0] == test_msg
    
    # Clean up
    message_bus.unsubscribe(session_id, cb)
    message_bus.clear_session(session_id)
