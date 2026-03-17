"""Event handler registry for the LLP client."""

from typing import Awaitable, Callable, Optional, Any

from typing import Protocol, runtime_checkable

from .message import TextMessage
from .tool_call import ToolCall


@runtime_checkable
class Annotater(Protocol):
    """Protocol for annotating tool calls for telemetry."""

    async def annotate_tool_call(self, tool_call: ToolCall) -> None: ...


# Handler type signatures (supports both sync and async)
MessageHandler = Callable[[Any | None, "Annotater", TextMessage], Awaitable[TextMessage]]
StartHandler = Callable[[], Any]


class HandlerRegistry:
    """Registry for event handlers (message and presence only)."""

    def __init__(self) -> None:
        """Initialize the handler registry."""
        self._on_message: Optional[MessageHandler] = None
        self._on_start: Optional[StartHandler] = None

    def set_start(self, handler: StartHandler) -> None:
        """Set the start event handler."""
        self._on_start = handler

    def set_message(self, handler: MessageHandler) -> None:
        """Set the message event handler."""
        self._on_message = handler

    def call_start(self) -> Any | None:
        """
        Call the start handler if set.

        Returns: If set, returns initial state (e.g. langchain agent instance).
        """
        if self._on_start is not None:
            return self._on_start()
        else:
            return None

    async def call_message(
        self, agent: Any | None, annotater: Annotater, message: TextMessage
    ) -> Optional[TextMessage]:
        """Call the message handler if set, passing annotater for tool call telemetry."""
        if self._on_message is not None:
            result = await self._on_message(agent, annotater, message)
            return result
        return None
