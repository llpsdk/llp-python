"""ToolCall message type for telemetry annotation."""

import json
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional


@dataclass
class ToolCall:
    """Tool call annotation sent to the platform for telemetry."""

    id: Optional[str]
    recipient: str
    name: str
    parameters: str
    result: str
    threw_exception: bool
    duration: timedelta

    def encode(self) -> str:
        """Encode a ToolCall into serialized JSON."""
        data = {
            "type": "tool_call",
            "id": self.id,
            "data": {
                "to": self.recipient,
                "name": self.name,
                "parameters": self.parameters,
                "result": self.result,
                "threw_exception": self.threw_exception,
                "duration_ms": int(self.duration.total_seconds() * 1000),
            },
        }
        return json.dumps(data)
