from llpsdk import TextMessage
from llpsdk.handler import Annotater
from langchain.agents.middleware import AgentState, AgentMiddleware
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest
from langgraph.types import Command
from typing_extensions import Required
from typing import Awaitable, Callable, Any
from datetime import timedelta
import json
import time


class LLPState(AgentState):
    message: Required[TextMessage]
    annotater: Required[Annotater]


class LLPAnnotationMiddleware(AgentMiddleware[LLPState]):
    state_schema = LLPState

    async def awrap_tool_call(
        self, request: ToolCallRequest, handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]]
    ) -> ToolMessage | Command[Any]:
        start = time.perf_counter()
        result = await handler(request)
        duration = time.perf_counter() - start
        print("tool call made ", request.tool_call["name"])
        print(type(result))
        tool_call = request.tool_call
        msg = request.state["message"]
        annotater = request.state["annotater"]
        content = result.content if isinstance(result, ToolMessage) else ""
        annotation = msg.tool_call(
            tool_call["name"],
            json.dumps(tool_call["args"]),
            content,
            timedelta(seconds=duration),
        )
        await annotater.annotate_tool_call(annotation)
        return result
