"""Tests for error types and codes."""

from llpsdk.errors import (
    ErrorCode,
    PlatformError,
)


def test_error_code_values():
    """Test ErrorCode enum values."""
    assert ErrorCode.INVALID_JSON == 0
    assert ErrorCode.NOT_AUTHENTICATED == 1
    assert ErrorCode.INVALID_SCHEMA == 2
    assert ErrorCode.INVALID_PRESENCE_SCHEMA == 3
    assert ErrorCode.INVALID_MESSAGE_SCHEMA == 4
    assert ErrorCode.GENERAL_SERVER_ERROR == 5
    assert ErrorCode.INVALID_KEY == 100
    assert ErrorCode.NAME_ALREADY_REGISTERED == 101
    assert ErrorCode.MISSING_RECIPIENT == 102
    assert ErrorCode.UNRECOGNIZED_TYPE == 104
    assert ErrorCode.ENCRYPTION_UNSUPPORTED == 105
    assert ErrorCode.AGENT_NOT_FOUND == 106


def test_platform_error_str():
    """Test PlatformError string representation."""
    error = PlatformError(
        code=ErrorCode.INVALID_KEY, message="Invalid API key", id="test-id"
    )
    assert str(error) == "[100] Invalid API key"


def test_platform_error_without_id():
    """Test PlatformError without ID."""
    error = PlatformError(code=ErrorCode.NOT_AUTHENTICATED, message="Not authenticated")
    assert error.id == ""
    assert str(error) == "[1] Not authenticated"
