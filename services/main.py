import asyncio
from services.app import consumer


if __name__ == "__main__":
    asyncio.run(consumer())
