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
import asyncio, os
import llpsdk as llp
from my_agent import create_agent

# called when starting a conversation with a test agent
def on_start():
    # create an instance of your agent
    return create_agent()

# Define a callback handler for processing messages
async def on_message(agent, annotater, msg):
    # Process the prompt with your agent.
    # Replace this with your own processing logic.
    response = await agent.ainvoke(msg.prompt)

    # You must return a response
    return msg.reply(response)

async def main():
    # Initialize the client
    client = llp.Client(
        os.getenv("LLP_AGENT_NAME"),
        os.getenv("LLP_API_KEY"),
    )

    # Register your message handler
    client.on_start(on_start)
    client.on_message(on_message)

    try:
        # Connect and keep the client running
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
