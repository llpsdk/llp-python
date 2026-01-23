"""Agent example demonstrating basic LLP SDK usage."""
import asyncio
import llpsdk as llp
import os
from dotenv import load_dotenv


async def main() -> None:
    """Run a simple agent that connects, sends presence, and sends a message."""
    load_dotenv()
    platform_url = os.getenv("LLP_URL")
    if platform_url is None:
        raise Exception("LLP_URL env var is not defined")

    cfg = llp.Config()
    cfg.platform_url = platform_url
    client = llp.Client("simple-agent", "testkey", cfg)

    # Set up handlers
    async def on_message(msg: llp.TextMessage) -> llp.TextMessage:
        print("Feed msg.prompt into your agent and return the response.")
        return msg.reply("this is my response")

    # Register handlers
    client.on_message(on_message)

    try:
        # Connect and authenticate
        print("Connecting to server...")
        await client.connect()
        print(f"Connected! Session ID: {client.session_id}")

        # Send a message
        msg = llp.TextMessage(recipient="echo-agent", prompt="Hello from Python!")
        print(f"Sending message to {msg.recipient}...")
        await client.send_message(msg)

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
