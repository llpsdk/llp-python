"""Tests for handler registry."""

import pytest

from llpsdk.handler import Annotater, HandlerRegistry
from llpsdk.message import PresenceMessage, TextMessage
from llpsdk.presence import PresenceStatus
from llpsdk.tool_call import ToolCall


class _FakeAnnotater:
    async def annotate_tool_call(self, tool_call: ToolCall) -> None:
        pass


_annotater = _FakeAnnotater()


@pytest.mark.asyncio
async def test_async_message_handler():
    """Test that async message handlers are called correctly."""
    registry = HandlerRegistry()
    calls = []

    async def async_handler(agent: None, ann: Annotater, msg: TextMessage) -> TextMessage:
        calls.append(("async", msg.prompt))
        return msg.reply("test")

    registry.set_message(async_handler)
    msg = TextMessage("alice", "World")
    msg.sender = "bob"
    await registry.call_message(None, _annotater, msg)

    assert len(calls) == 1
    assert calls[0] == ("async", "World")


@pytest.mark.asyncio
async def test_sync_presence_handler():
    """Test that sync presence handlers are called correctly."""
    registry = HandlerRegistry()
    calls = []

    def handler(update: PresenceMessage) -> None:
        calls.append((update.sender, update.status))

    registry.set_presence(handler)
    update = PresenceMessage(sender="alice", status=PresenceStatus.available)
    await registry.call_presence(update)

    assert len(calls) == 1
    assert calls[0] == ("alice", PresenceStatus.available)


@pytest.mark.asyncio
async def test_async_presence_handler():
    """Test that async presence handlers are called correctly."""
    registry = HandlerRegistry()
    calls = []

    async def handler(update: PresenceMessage) -> None:
        calls.append((update.sender, update.status))

    registry.set_presence(handler)
    update = PresenceMessage(sender="bob", status=PresenceStatus.unavailable)
    await registry.call_presence(update)

    assert len(calls) == 1
    assert calls[0] == ("bob", PresenceStatus.unavailable)


@pytest.mark.asyncio
async def test_no_handler_set():
    """Test that calling with no handler set doesn't crash."""
    registry = HandlerRegistry()

    # Should not raise
    await registry.call_message(None, _annotater, TextMessage("alice", "test"))
    await registry.call_presence(PresenceMessage(sender="alice", status=PresenceStatus.available))


@pytest.mark.asyncio
async def test_handler_replacement():
    """Test that handlers can be replaced."""
    registry = HandlerRegistry()
    calls = []

    async def handler1(agent: None, ann: Annotater, msg: TextMessage) -> TextMessage:
        calls.append("handler1")
        return msg.reply("test")

    async def handler2(agent: None, ann: Annotater, msg: TextMessage) -> TextMessage:
        calls.append("handler2")
        return msg.reply("test")

    registry.set_message(handler1)
    msg1 = TextMessage("alice", "test1")
    msg1.sender = "bob"
    await registry.call_message(None, _annotater, msg1)

    registry.set_message(handler2)
    msg2 = TextMessage("alice", "test2")
    msg2.sender = "bob"
    await registry.call_message(None, _annotater, msg2)

    assert calls == ["handler1", "handler2"]
