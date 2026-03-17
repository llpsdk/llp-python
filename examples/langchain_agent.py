"""Agent example demonstrating basic LLP SDK usage with langchain."""
import asyncio
import llpsdk as llp
from llpsdk.langchain import LLPAnnotationMiddleware
import os
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    city_lower = city.lower()
    weather_data = {
        "new york": "Partly cloudy, 45°F, wind 12 mph NW",
        "los angeles": "Sunny, 72°F, wind 5 mph SW",
        "chicago": "Overcast, 30°F, wind 20 mph N, chance of snow",
        "miami": "Humid and warm, 82°F, wind 8 mph SE",
        "seattle": "Rainy, 48°F, wind 10 mph W",
        "denver": "Clear skies, 38°F, wind 15 mph NE",
        "san francisco": "Foggy, 58°F, wind 14 mph W",
        "austin": "Sunny, 68°F, wind 7 mph S",
        "boston": "Cold and windy, 35°F, wind 22 mph NW",
        "london": "Drizzle, 50°F, wind 11 mph SW",
    }
    return weather_data.get(city_lower, f"No weather data available for {city}")

async def main() -> None:
    """Run a simple agent that connects, sends presence, and sends a message."""
    load_dotenv()
    platform_url = os.getenv("LLP_URL")
    api_key = os.getenv("LLP_API_KEY")
    ollama_key = os.getenv("OLLAMA_API_KEY")

    if platform_url is None:
        raise Exception("LLP_URL env var is not defined")

    if api_key is None:
        raise Exception("LLP_API_KEY env var is not defined")

    if ollama_key is None:
        raise Exception("OLLAMA_API_KEY env var is not defined")

    cfg = llp.Config(platform_url=platform_url)
    cfg.platform_url = platform_url
    client = llp.Client("simple-agent", api_key, cfg)

    # Set up handlers
    def on_start():
        model = ChatOllama(
            model="gpt-oss:120b",
            base_url="https://ollama.com",
            api_key=ollama_key,
        )
        return create_agent(
            model=model,
            tools=[get_weather],
            middleware=[LLPAnnotationMiddleware()],
            system_prompt="You are a helpful meteorologist that gives succinct responses regarding the weather for various American cities."
        )

    async def on_message(agent, annotater: llp.Annotater, msg: llp.TextMessage) -> llp.TextMessage:
        if agent is not None:
            result = await agent.ainvoke(
                {
                    "messages": [{"role": "user", "content": msg.prompt}],
                    "message": msg,
                    "annotater": annotater,
                }
            )
            reply = result["messages"][-1].content
            # tc = msg.tool_call("get_weather", '{"city":"Seattle"}', "rainy", timedelta(seconds=1))
            # await annotater.annotate_tool_call(tc)
            return msg.reply(reply)
        else:
            return msg.reply("I'm a helpful meteorologist!")

    # Register handlers
    client.on_start(on_start)
    client.on_message(on_message)

    try:
        # Connect and authenticate
        print("Connecting to server...")
        await client.connect()
        print(f"Connected!! Session ID: {client.session_id}")

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
