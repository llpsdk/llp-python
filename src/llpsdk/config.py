"""Configuration for the LLP client."""

from dataclasses import dataclass


@dataclass
class Config:
    """Client configuration."""

    platform_url: str = "wss://llphq.com/agent/websocket"
    connect_timeout: float = 10.0  # seconds
