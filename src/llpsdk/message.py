"""Message types and serialization for the LLP client."""

import base64
import uuid
import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from llpsdk.errors import TextMessageEmptyError
from llpsdk.presence import PresenceStatus


class TextMessage:
    """User-facing message type."""

    _id: Optional[str] = None
    sender: str = ""
    recipient: str = ""
    prompt: str = ""  # Decoded string
    encrypted: bool = False

    def __init__(self, recipient: str, prompt: str) -> None:
        self.recipient = recipient
        self.prompt = prompt
        self._id = str(uuid.uuid4())
        self.encrypted = False

    def reply(self, msg: str) -> "TextMessage":
        if msg == "":
            raise TextMessageEmptyError()

        t = TextMessage(self.sender, msg)
        t._id = self._id
        return t

    def encode(self) -> str:
        """Encodes a TextMessage object into serialized JSON"""
        if self._id is None:
            self._id = str(uuid.uuid4())

        if self.prompt == "":
            raise TextMessageEmptyError()

        data = {
            "type": "message",
            "id": self._id,
            "from": self.sender,
            "data": {
                "to": self.recipient,
                "prompt": base64.b64encode(self.prompt.encode()).decode("utf-8"),
                "encrypted": False,
            },
        }
        return json.dumps(data)

    @staticmethod
    def decode(msg: Dict[str, Any]) -> "TextMessage":
        """Decodes a JSON dict into a TextMessage object"""
        prompt = base64.b64decode(msg["data"]["prompt"]).decode("utf-8")
        t = TextMessage(msg["data"]["to"], prompt)
        t._id = msg["id"]
        t.sender = msg["from"]
        t.encrypted = msg["data"]["encrypted"]
        return t


@dataclass
class PresenceMessage:
    """Presence update message."""

    sender: str = ""
    status: PresenceStatus = PresenceStatus.unavailable
    _id: Optional[str] = None

    def is_available(self) -> bool:
        return self.status == PresenceStatus.available

    def encode(self) -> str:
        """Encodes a PresenceMessage object into serialized JSON"""
        if self._id is None:
            self._id = str(uuid.uuid4())

        data = {
            "type": "presence",
            "id": self._id,
            "from": self.sender,
            "data": {"status": self.status.name, "supports_encryption": False},
        }
        return json.dumps(data)

    @staticmethod
    def decode(msg: Dict[str, Any]) -> "PresenceMessage":
        """Decodes a JSON dict into a PresenceMessage object"""
        p = PresenceMessage(
            _id=msg["id"], sender=msg["from"], status=PresenceStatus[msg["data"]["status"]]
        )
        return p


@dataclass
class AuthenticateMessage:
    """Authentication message sent to server."""

    _id: Optional[str] = None
    name: str = ""
    key: str = ""

    def encode(self) -> str:
        """Encode an AuthenticateMessage object into serialized JSON"""
        if self._id is None:
            self._id = str(uuid.uuid4())

        data = {"type": "authenticate", "id": self._id, "name": self.name, "key": self.key}
        return json.dumps(data)


@dataclass
class AuthenticatedResponse:
    """Response after successful authentication."""

    _id: Optional[str] = None
    session_id: str = ""

    @staticmethod
    def decode(msg: Dict[str, Any]) -> "AuthenticatedResponse":
        """Decodes a JSON dict into a AuthenticatedResponse object"""
        return AuthenticatedResponse(_id=msg["id"], session_id=msg["data"]["session_id"])
