"""Agent example demonstrating basic LLP SDK usage."""
import asyncio
from datetime import timedelta
from typing import Any
import llpsdk as llp
import os
from dotenv import load_dotenv


async def main() -> None:
    """Run a simple agent that connects, sends presence, and sends a message."""
    load_dotenv()
    platform_url = os.getenv("LLP_URL")
    api_key = os.getenv("LLP_API_KEY")

    if platform_url is None:
        raise Exception("LLP_URL env var is not defined")

    if api_key is None:
        raise Exception("LLP_API_KEY env var is not defined")

    cfg = llp.Config(platform_url=platform_url)
    cfg.platform_url = platform_url
    client = llp.Client("simple-agent", api_key, cfg)

    # Set up handlers
    async def on_message(_agent: Any, annotater: llp.Annotater, msg: llp.TextMessage) -> llp.TextMessage:
        tc = msg.tool_call("get_weather", '{"city":"Seattle"}', "rainy", timedelta(seconds=1))
        await annotater.annotate_tool_call(tc)
        return msg.reply("this is my response")

    # Register handlers
    client.on_message(on_message)

    try:
        # Connect and authenticate
        print("Connecting to server...")
        await client.connect()
        print(f"Connected! Session ID: {client.session_id}")

        # Keep running
        print("Agent running. Press Ctrl+C to exit...")
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()
        print("Disconnected.")


if __name__ == "__main__":
    asyncio.run(main())
