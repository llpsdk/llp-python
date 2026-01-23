"""Error types and codes for the LLP client."""

from dataclasses import dataclass
from enum import IntEnum


class ErrorCode(IntEnum):
    """Platform error codes."""

    INVALID_JSON = 0
    NOT_AUTHENTICATED = 1
    INVALID_SCHEMA = 2
    INVALID_PRESENCE_SCHEMA = 3
    INVALID_MESSAGE_SCHEMA = 4
    GENERAL_SERVER_ERROR = 5
    INVALID_KEY = 100
    NAME_ALREADY_REGISTERED = 101
    MISSING_RECIPIENT = 102
    UNRECOGNIZED_TYPE = 104
    ENCRYPTION_UNSUPPORTED = 105
    AGENT_NOT_FOUND = 106


@dataclass
class PlatformError(Exception):
    """Platform error from server."""

    code: ErrorCode
    message: str
    id: str = ""

    def __str__(self) -> str:
        """Return string representation of the error."""
        return f"[{self.code}] {self.message}"


class LLPClientError(Exception):
    """Base error for all LLP-related client errors"""

    pass


class TextMessageEmptyError(LLPClientError):
    """Message prompt is empty"""

    pass


class NotConnectedError(LLPClientError):
    """Client is not connected."""

    pass


class NotAuthenticatedError(LLPClientError):
    """Client is not authenticated."""

    pass


class AlreadyClosedError(LLPClientError):
    """Client is already closed."""

    pass


class TimeoutError(LLPClientError):
    """Operation timed out."""

    pass


class InvalidStatusError(LLPClientError):
    """Invalid presence status."""

    pass
