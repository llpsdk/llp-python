"""Presence and connection status enums."""

from enum import IntEnum


class ConnectionStatus(IntEnum):
    """Client connection status."""

    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    AUTHENTICATED = 3
    CLOSED = 4


class PresenceStatus(IntEnum):
    """Agent presence status."""

    unavailable = 0
    available = 1
