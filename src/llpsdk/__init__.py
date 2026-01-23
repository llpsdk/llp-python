"""LLP Python SDK - Python client for Large Language Platform communication."""

from .client import Client
from .config import Config
from .errors import (
    AlreadyClosedError,
    ErrorCode,
    InvalidStatusError,
    NotAuthenticatedError,
    NotConnectedError,
    PlatformError,
    TimeoutError,
)
from .message import (
    AuthenticatedResponse,
    PresenceMessage,
    TextMessage,
)
from .presence import ConnectionStatus, PresenceStatus

__all__ = [
    "Client",
    "Config",
    "TextMessage",
    "AuthenticatedResponse",
    "PresenceMessage",
    "ConnectionStatus",
    "PresenceStatus",
    "PlatformError",
    "ErrorCode",
    "NotConnectedError",
    "NotAuthenticatedError",
    "AlreadyClosedError",
    "TimeoutError",
    "InvalidStatusError",
]

__version__ = "0.1.0"
