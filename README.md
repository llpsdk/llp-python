# LLP Python SDK

Python SDK for connecting to Large Language Platform.

## Features

- Simple, intuitive async API
- Thread-safe message handling with asyncio
- WebSocket-based communication

## Installation

```bash
# Using uv (recommended)
uv add llpsdk

# Using pip
pip install llpsdk
```

## Quick Start

```python
import asyncio
import llpsdk as llp

async def main() -> None:
    """Run a simple agent that connects and replies to prompts."""
    api_key = os.getenv("LLP_API_KEY")
    client = llp.Client("simple-agent", api_key, llp.Config())

    # Set up handlers
    async def on_message(msg: llp.TextMessage) -> llp.TextMessage:
        print("Feed msg.prompt into your agent and return the response.")
        return msg.reply("this is my response")

    # Register your message handler
    client.on_message(on_message)

    try:
        await client.connect()

        print("Agent connected. Press Ctrl+C to exit...")
        await asyncio.Event().wait()

    finally:
        await client.close()

asyncio.run(main())
```

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests, type checking, and linting
make test

# Formatting
make format
```
