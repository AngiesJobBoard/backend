import asyncio
from services.app import consumer
from ajb.ascii_arts import print_ajb_ascii, print_services_ascii


if __name__ == "__main__":
    print_ajb_ascii()
    print_services_ascii()
    print("Ready to consume messages")
    asyncio.run(consumer())
