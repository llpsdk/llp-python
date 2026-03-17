"""Tests for ToolCall annotation feature."""

import json
from datetime import timedelta
from unittest.mock import AsyncMock

import pytest

from llpsdk.handler import Annotater, HandlerRegistry
from llpsdk.message import TextMessage
from llpsdk.tool_call import ToolCall


# --- ToolCall encode ---


def test_tool_call_encode():
    tc = ToolCall(
        id="msg-1",
        recipient="alice",
        name="search",
        parameters='{"query": "weather"}',
        result="Sunny, 72°F",
        threw_exception=False,
        duration=timedelta(milliseconds=150),
    )
    data = json.loads(tc.encode())

    assert data["type"] == "tool_call"
    assert data["id"] == "msg-1"
    assert data["data"]["to"] == "alice"
    assert data["data"]["name"] == "search"
    assert data["data"]["parameters"] == '{"query": "weather"}'
    assert data["data"]["result"] == "Sunny, 72°F"
    assert data["data"]["threw_exception"] is False
    assert data["data"]["duration_ms"] == 150


def test_tool_call_encode_exception():
    tc = ToolCall(
        id="msg-2",
        recipient="bob",
        name="fetch_data",
        parameters="{}",
        result="Connection refused",
        threw_exception=True,
        duration=timedelta(seconds=1),
    )
    data = json.loads(tc.encode())

    assert data["data"]["threw_exception"] is True
    assert data["data"]["duration_ms"] == 1000


def test_tool_call_encode_duration_fractional_seconds():
    tc = ToolCall(
        id="msg-3",
        recipient="bob",
        name="slow_tool",
        parameters="{}",
        result="done",
        threw_exception=False,
        duration=timedelta(milliseconds=1500),
    )
    data = json.loads(tc.encode())
    assert data["data"]["duration_ms"] == 1500


# --- TextMessage factory methods ---


def test_text_message_tool_call_factory():
    msg = TextMessage("bob", "hello")
    msg._id = "msg-42"
    msg.sender = "alice"

    tc = msg.tool_call("weather", '{"city": "NYC"}', "Sunny", timedelta(milliseconds=200))

    assert tc.id == "msg-42"
    assert tc.recipient == "alice"
    assert tc.name == "weather"
    assert tc.parameters == '{"city": "NYC"}'
    assert tc.result == "Sunny"
    assert tc.threw_exception is False
    assert tc.duration == timedelta(milliseconds=200)


def test_text_message_tool_call_exception_factory():
    msg = TextMessage("bob", "hello")
    msg._id = "msg-43"
    msg.sender = "carol"

    err = ValueError("service unavailable")
    tc = msg.tool_call_exception("fetch", '{"url": "..."}', err, timedelta(seconds=2))

    assert tc.id == "msg-43"
    assert tc.recipient == "carol"
    assert tc.name == "fetch"
    assert tc.result == "service unavailable"
    assert tc.threw_exception is True
    assert tc.duration == timedelta(seconds=2)


# --- Annotater Protocol ---


def test_annotater_protocol_satisfied():
    """Client-like objects that implement annotate_tool_call satisfy Annotater."""

    class FakeClient:
        async def annotate_tool_call(self, tool_call: ToolCall) -> None:
            pass

    assert isinstance(FakeClient(), Annotater)


def test_annotater_protocol_not_satisfied():
    """Objects without annotate_tool_call do not satisfy Annotater."""

    class NotAnAnnotater:
        pass

    assert not isinstance(NotAnAnnotater(), Annotater)


# --- HandlerRegistry with annotater ---


@pytest.mark.asyncio
async def test_message_handler_receives_annotater():
    """Message handler receives the annotater as its first argument."""
    registry = HandlerRegistry()
    received_annotater = []

    class FakeAnnotater:
        async def annotate_tool_call(self, tool_call: ToolCall) -> None:
            pass

    annotater = FakeAnnotater()

    async def handler(agent: None, ann: Annotater, msg: TextMessage) -> TextMessage:
        received_annotater.append(ann)
        return msg.reply("ok")

    registry.set_message(handler)
    msg = TextMessage("alice", "hello")
    msg.sender = "bob"
    await registry.call_message(None, annotater, msg)

    assert len(received_annotater) == 1
    assert received_annotater[0] is annotater


@pytest.mark.asyncio
async def test_handler_can_annotate_tool_call():
    """Handler can call annotate_tool_call on the annotater it receives."""
    registry = HandlerRegistry()
    annotated: list[ToolCall] = []

    class FakeAnnotater:
        async def annotate_tool_call(self, tool_call: ToolCall) -> None:
            annotated.append(tool_call)

    annotater = FakeAnnotater()

    async def handler(agent: None, ann: Annotater, msg: TextMessage) -> TextMessage:
        tc = msg.tool_call("lookup", "{}", "result", timedelta(milliseconds=50))
        await ann.annotate_tool_call(tc)
        return msg.reply("done")

    registry.set_message(handler)
    msg = TextMessage("alice", "hello")
    msg._id = "msg-99"
    msg.sender = "bob"
    await registry.call_message(None, annotater, msg)

    assert len(annotated) == 1
    assert annotated[0].name == "lookup"
    assert annotated[0].id == "msg-99"


@pytest.mark.asyncio
async def test_no_message_handler_with_annotater():
    """call_message returns None without error when no handler is set."""
    registry = HandlerRegistry()
    annotater = AsyncMock(spec=Annotater)

    result = await registry.call_message(None, annotater, TextMessage("alice", "test"))
    assert result is None
