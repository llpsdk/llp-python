"""Event handler registry for the LLP client."""

import asyncio
from typing import Awaitable, Callable, Optional, Union

from typing import Protocol, runtime_checkable

from .message import PresenceMessage, TextMessage
from .tool_call import ToolCall


@runtime_checkable
class Annotater(Protocol):
    """Protocol for annotating tool calls for telemetry."""

    async def annotate_tool_call(self, tool_call: ToolCall) -> None: ...


# Handler type signatures (supports both sync and async)
PresenceHandler = Union[
    Callable[[PresenceMessage], None], Callable[[PresenceMessage], Awaitable[None]]
]
MessageHandler = Callable[["Annotater", TextMessage], Awaitable[TextMessage]]


class HandlerRegistry:
    """Registry for event handlers (message and presence only)."""

    def __init__(self) -> None:
        """Initialize the handler registry."""
        self._on_presence: Optional[PresenceHandler] = None
        self._on_message: Optional[MessageHandler] = None

    def set_presence(self, handler: PresenceHandler) -> None:
        """Set the presence event handler."""
        self._on_presence = handler

    def set_message(self, handler: MessageHandler) -> None:
        """Set the message event handler."""
        self._on_message = handler

    async def call_presence(self, update: PresenceMessage) -> None:
        """Call the presence handler if set."""
        if self._on_presence is not None:
            if asyncio.iscoroutinefunction(self._on_presence):
                await self._on_presence(update)
            else:
                self._on_presence(update)

    async def call_message(
        self, annotater: Annotater, message: TextMessage
    ) -> Optional[TextMessage]:
        """Call the message handler if set, passing annotater for tool call telemetry."""
        if self._on_message is not None:
            result = await self._on_message(annotater, message)
            return result
        return None
