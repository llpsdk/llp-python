"""Tests for message types and serialization."""

import base64
import json
import pytest

from llpsdk.errors import TextMessageEmptyError
from llpsdk.message import (
    AuthenticatedResponse,
    AuthenticateMessage,
    PresenceMessage,
    TextMessage,
)
from llpsdk.presence import PresenceStatus


def test_text_message_creation():
    """Test TextMessage creation."""
    msg = TextMessage("bob","Hello")
    assert msg.recipient == "bob"
    assert msg.prompt == "Hello"
    assert msg.encrypted is False


def test_authenticate_message_encode():
    """Test AuthenticateMessage serialization."""
    msg = AuthenticateMessage(name="agent1", key="secret-key")
    json_data = json.loads(msg.encode())
    assert json_data["type"] == "authenticate"
    assert json_data["name"] == "agent1"
    assert json_data["key"] == "secret-key"


def test_presence_message_encode():
    """Test PresenceMessage serialization."""
    msg = PresenceMessage(sender="bob", status=PresenceStatus.available)
    json_data = json.loads(msg.encode())

    assert json_data["type"] == "presence"
    assert json_data["from"] == "bob"
    assert json_data["data"]["status"] == "available"
    assert json_data["data"]["supports_encryption"] is False

def test_text_message_encode():
    """Test TextMessage to JSON conversion."""
    msg = TextMessage("bob", "Hello, World!")
    prompt_b64 = base64.b64encode("Hello, World!".encode("utf-8")).decode("ascii")
    json_data = json.loads(msg.encode())

    assert json_data["type"] == "message"
    assert json_data["data"]["to"] == "bob"
    assert json_data["data"]["prompt"] == prompt_b64
    assert json_data["data"]["encrypted"] is False


def test_text_message_decode():
    """Test TextMessage from JSON conversion."""
    prompt_b64 = base64.b64encode("Test message".encode("utf-8")).decode("ascii")
    json_msg = {
        "type": "message",
        "id": "msg-2",
        "from": "alice",
        "data": {
            "to" : "bob",
            "prompt": prompt_b64,
            "encrypted": False
        }
    }

    text_msg = TextMessage.decode(json_msg)

    assert text_msg._id == "msg-2"
    assert text_msg.sender == "alice"
    assert text_msg.recipient == "bob"
    assert text_msg.prompt == "Test message"
    assert text_msg.encrypted is False


def test_authenticated_response_decode():
    """Test AuthenticatedResponse parsing."""
    json_data = {
        "type": "authenticated",
        "id": "auth",
        "data": {"session_id": "session-123"},
    }
    response = AuthenticatedResponse.decode(json_data)

    assert response._id == "auth"
    assert response.session_id == "session-123"


def test_presence_message_decode():
    """Test PresenceUpdate parsing."""
    json_data = {
        "type": "presence",
        "id": "pres-1",
        "from": "alice",
        "data": {"status": "available"},
    }
    update = PresenceMessage.decode(json_data)

    assert update.sender == "alice"
    assert update.status == PresenceStatus.available


def test_text_message_unicode():
    """Test TextMessage with Unicode characters."""
    msg = TextMessage("bob", "Hello 世界 🌍")
    json_msg = msg.encode()

    # Convert back
    text_msg = TextMessage.decode(json.loads(json_msg))
    assert text_msg.prompt == "Hello 世界 🌍"


def test_text_message_empty_prompt():
    """Test TextMessage with empty prompt."""
    with pytest.raises(TextMessageEmptyError):
        msg = TextMessage("bob", "")
        msg.encode()
