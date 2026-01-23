"""Main LLP client implementation."""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

import websockets
from websockets.asyncio.client import ClientConnection

from .config import Config
from .errors import (
    AlreadyClosedError,
    ErrorCode,
    LLPClientError,
    NotAuthenticatedError,
    PlatformError,
)
from .handler import HandlerRegistry, MessageHandler, PresenceHandler
from .message import (
    AuthenticatedResponse,
    AuthenticateMessage,
    PresenceMessage,
    TextMessage,
)
from .presence import ConnectionStatus, PresenceStatus


class Client:
    """Main async WebSocket client for connecting to the LLP platform."""

    def __init__(self, name: str, api_key: str, config: Optional[Config] = None) -> None:
        """
        Initialize the LLP client.

        Args:
            name: Agent name (unique per organization)
            api_key: API key for authentication
            config: Optional configuration (defaults to Config.default())
        """
        # Config & logging
        self._config = config or Config()
        self._logger = logging.getLogger(__name__)

        # Connection
        self._ws: Optional[ClientConnection] = None
        self._ws_url: str = self._config.platform_url

        # Session state
        self._name = name
        self._api_key = api_key
        self._session_id: Optional[str] = None
        self._status = ConnectionStatus.DISCONNECTED
        self._status_lock = asyncio.Lock()
        self._presence = PresenceStatus.unavailable
        self._presence_lock = asyncio.Lock()

        # Message handling
        self._handlers = HandlerRegistry()
        self._outbound: asyncio.Queue[str] = asyncio.Queue(maxsize=32)

        # Async tasks
        self._read_task: Optional[asyncio.Task[None]] = None
        self._write_task: Optional[asyncio.Task[None]] = None
        self._stop_event = asyncio.Event()

        # Pending messages (for request/response)
        self._pending_lock = asyncio.Lock()
        self._pending: Dict[str, asyncio.Future[TextMessage]] = {}

        # Auth future (for waiting on authentication)
        self._auth_future: Optional[asyncio.Future[AuthenticatedResponse]] = None

    # Public async API

    async def connect(self, timeout: Optional[float] = None) -> None:
        """
        Connect to the WebSocket server and authenticate.

        Args:
            timeout: Connection timeout in seconds (defaults to config.connect_timeout)

        Raises:
            AlreadyClosedError: If client is already closed
            PlatformError: If authentication fails
            TimeoutError: If connection or authentication times out
        """
        async with self._status_lock:
            if self._status == ConnectionStatus.CLOSED:
                raise AlreadyClosedError("Client is already closed")

            if self._status == ConnectionStatus.AUTHENTICATED:
                return  # Already connected and authenticated

            self._status = ConnectionStatus.CONNECTING

        timeout_val = timeout or self._config.connect_timeout

        try:
            # Connect to WebSocket
            self._ws = await asyncio.wait_for(websockets.connect(self._ws_url), timeout=timeout_val)

            async with self._status_lock:
                self._status = ConnectionStatus.CONNECTED

            # Start read and write tasks
            self._stop_event.clear()
            self._read_task = asyncio.create_task(self._run_read_loop())
            self._write_task = asyncio.create_task(self._run_write_loop())

            # Authenticate
            await self._authenticate(timeout=timeout_val)
            await self._send_presence(PresenceStatus.available)

        except Exception as e:
            async with self._status_lock:
                self._status = ConnectionStatus.DISCONNECTED
            # Clean up on error
            if self._ws:
                try:
                    await self._ws.close()
                except Exception:
                    pass
                self._ws = None
            raise e

    async def close(self) -> None:
        """Close the connection gracefully."""
        async with self._status_lock:
            if self._status == ConnectionStatus.CLOSED:
                return

            # Signal all tasks to stop
            self._stop_event.set()

            # Close the WebSocket
            if self._ws:
                try:
                    await self._ws.close()
                except Exception:
                    pass
                self._ws = None

        # Wait for tasks to finish
        if self._read_task and not self._read_task.done():
            try:
                await asyncio.wait_for(self._read_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._read_task.cancel()
                try:
                    await self._read_task
                except asyncio.CancelledError:
                    pass

        if self._write_task and not self._write_task.done():
            try:
                await asyncio.wait_for(self._write_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._write_task.cancel()
                try:
                    await self._write_task
                except asyncio.CancelledError:
                    pass

        # Update status
        async with self._status_lock:
            self._status = ConnectionStatus.CLOSED
            self._session_id = None

        async with self._presence_lock:
            self._presence = PresenceStatus.unavailable

    async def send_async_message(self, message: TextMessage) -> None:
        """
        Send a message asynchronously (fire-and-forget).

        Args:
            message: Message to send

        Raises:
            ValueError: If message ID is empty
            NotAuthenticatedError: If not authenticated
        """
        async with self._status_lock:
            if self._status != ConnectionStatus.AUTHENTICATED:
                raise NotAuthenticatedError("Must connect before sending messages")

        await self._send(message.encode())

    async def send_message(self, message: TextMessage, timeout: float = 10.0) -> TextMessage:
        """
        Send a message and wait for response.

        Args:
            message: Message to send
            timeout: Response timeout in seconds

        Returns:
            Response message

        Raises:
            ValueError: If message ID is empty
            NotAuthenticatedError: If not authenticated
            TimeoutError: If no response within timeout
        """
        # ID is REQUIRED for synchronous send
        if not message._id:
            raise ValueError("Message ID is required for send_message()")

        async with self._status_lock:
            if self._status != ConnectionStatus.AUTHENTICATED:
                raise NotAuthenticatedError("Must connect before sending messages")

        # Create future for this message
        response_future: asyncio.Future[TextMessage] = asyncio.get_event_loop().create_future()

        async with self._pending_lock:
            self._pending[message._id] = response_future

        try:
            # Send message asynchronously
            await self.send_async_message(message)

            # Wait for response with timeout
            response = await asyncio.wait_for(response_future, timeout=timeout)
            return response

        except asyncio.TimeoutError:
            raise TimeoutError(f"No response within {timeout}s")
        finally:
            # Clean up
            async with self._pending_lock:
                self._pending.pop(message._id, None)

    # Properties

    @property
    def session_id(self) -> Optional[str]:
        """Get the current session ID."""
        return self._session_id

    @property
    def status(self) -> ConnectionStatus:
        """Get the current connection status."""
        return self._status

    @property
    def presence(self) -> PresenceStatus:
        """Get the current presence status."""
        return self._presence

    # Event handlers (fluent API)

    def on_presence(self, handler: PresenceHandler) -> None:
        """
        Set the presence event handler.

        Args:
            handler: Callable to handle presence updates

        Returns:
            Self for fluent chaining
        """
        if self._status >= ConnectionStatus.CONNECTING.value:
            raise LLPClientError("on_presence can not be called once client is connected.")

        self._handlers.set_presence(handler)

    def on_message(self, handler: MessageHandler) -> None:
        """
        Set the message event handler.

        Args:
            handler: Callable to handle incoming messages

        Returns:
            Self for fluent chaining
        """
        if self._status >= ConnectionStatus.CONNECTING.value:
            raise LLPClientError("on_message can not be called once client is connected.")

        self._handlers.set_message(handler)

    # Private async methods

    async def _authenticate(self, timeout: float = 10.0) -> None:
        """
        Authenticate with the server (internal method).

        Args:
            timeout: Authentication timeout in seconds

        Raises:
            PlatformError: If authentication fails
            TimeoutError: If authentication times out
        """
        # Create future for authentication response
        self._auth_future = asyncio.get_event_loop().create_future()

        # Send authentication message
        auth_msg = AuthenticateMessage(name=self._name, key=self._api_key)
        await self._send(auth_msg.encode())

        # Wait for authentication response
        try:
            response = await asyncio.wait_for(self._auth_future, timeout=timeout)

            # Update session state
            async with self._status_lock:
                self._session_id = response.session_id
                self._status = ConnectionStatus.AUTHENTICATED

        except asyncio.TimeoutError:
            self._auth_future = None
            raise TimeoutError("Authentication timed out")
        finally:
            self._auth_future = None

    async def _send_presence(self, status: PresenceStatus) -> None:
        """
        Send presence update.

        Args:
            status: Presence status (available or unavailable)

        Raises:
            NotAuthenticatedError: If not authenticated
        """
        async with self._status_lock:
            if self._status != ConnectionStatus.AUTHENTICATED:
                raise NotAuthenticatedError("Must connect before sending presence")

        # Update local presence
        async with self._presence_lock:
            self._presence = status

        # Send presence message
        msg = PresenceMessage(status=status)
        await self._send(msg.encode())

    async def _run_read_loop(self) -> None:
        """Read JSON messages from WebSocket and dispatch to handlers."""
        try:
            if self._ws is None:
                return

            async for message in self._ws:
                if self._stop_event.is_set():
                    break

                try:
                    # Parse JSON (WebSocket guarantees complete messages)
                    if isinstance(message, bytes):
                        msg_str = message.decode("utf-8")
                    else:
                        msg_str = message

                    msg_dict = json.loads(msg_str)

                    # Dispatch to handler
                    await self._handle_message(msg_dict)

                except json.JSONDecodeError as e:
                    self._logger.error(f"Failed to decode JSON: {e}")
                    continue
                except Exception as e:
                    self._logger.error(f"Dispatch error: {e}")
                    continue

        except websockets.ConnectionClosed:
            await self._handle_disconnect()
        except Exception as e:
            if not self._stop_event.is_set():
                self._logger.error(f"Read error: {e}")
                await self._handle_disconnect()

    async def _run_write_loop(self) -> None:
        """Pull from outbound queue and send as WebSocket text frames."""
        while not self._stop_event.is_set():
            try:
                # Wait for message with timeout
                data = await asyncio.wait_for(self._outbound.get(), timeout=1.0)

                if self._ws is None:
                    break

                # Send as WebSocket text frame
                await self._ws.send(data)

            except asyncio.TimeoutError:
                continue  # Check stop event and retry
            except websockets.ConnectionClosed:
                await self._handle_disconnect()
                break
            except Exception as e:
                if not self._stop_event.is_set():
                    self._logger.error(f"Write error: {e}")
                    await self._handle_disconnect()
                break

    async def _handle_message(self, msg_dict: Dict[str, Any]) -> None:
        """Handle incoming message from server."""
        msg_type = msg_dict.get("type", "")

        if msg_type == "error":
            error = PlatformError(
                code=ErrorCode(msg_dict.get("code", 0)),
                message=msg_dict.get("message", "Unknown error"),
                id=msg_dict.get("id", ""),
            )
            self._logger.error(f"Server error: {error}")

            # Check if this is an auth error
            if self._auth_future and not self._auth_future.done():
                self._auth_future.set_exception(error)
                return

            # Check if this error is for a pending message
            if error.id:
                async with self._pending_lock:
                    if error.id in self._pending:
                        future = self._pending.pop(error.id)
                        if not future.done():
                            future.set_exception(error)
                        return

            return

        if msg_type == "authenticated":
            response = AuthenticatedResponse.decode(msg_dict)
            if self._auth_future and not self._auth_future.done():
                self._auth_future.set_result(response)
            return

        if msg_type == "presence":
            update = PresenceMessage.decode(msg_dict)
            await self._handlers.call_presence(update)
            return

        if msg_type == "message":
            msg_id = msg_dict.get("id", "")

            async with self._pending_lock:
                if msg_id in self._pending:
                    future = self._pending[msg_id]
                    if not future.done():
                        tm = TextMessage.decode(msg_dict)
                        future.set_result(tm)
                    return

            # Not a response, call message handler
            tm = TextMessage.decode(msg_dict)
            reply = await self._handlers.call_message(tm)
            if reply is not None:
                await self.send_async_message(reply)
            return

    async def _handle_disconnect(self) -> None:
        """Handle disconnect event."""
        async with self._status_lock:
            if self._status != ConnectionStatus.CLOSED:
                self._status = ConnectionStatus.DISCONNECTED
                self._session_id = None

        async with self._presence_lock:
            self._presence = PresenceStatus.unavailable

    async def _send(self, data: str) -> None:
        """Send JSON message to outbound queue."""
        await self._outbound.put(data)
