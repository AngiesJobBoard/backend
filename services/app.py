import ssl
import asyncio
from aiokafka import AIOKafkaConsumer

from ajb.config.settings import SETTINGS
from ajb.base.events import KafkaGroup, KafkaTopic

from services.routing import topic_router


ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


async def consume():
    consumer = AIOKafkaConsumer(
        bootstrap_servers=SETTINGS.KAFKA_BOOTSTRAP_SERVER,
        group_id=KafkaGroup.DEFAULT.value,
        auto_offset_reset='earliest',
        sasl_mechanism='SCRAM-SHA-256',
        security_protocol='SASL_SSL',
        sasl_plain_username=SETTINGS.KAFKA_USERNAME,
        sasl_plain_password=SETTINGS.KAFKA_PASSWORD,
        ssl_context=ssl_context,  # Use default SSL context
    )
    consumer.subscribe([topic.value for topic in KafkaTopic])

    # Start the consumer
    await consumer.start()
    try:
        async for msg in consumer:
            # Asynchronously process the message
            asyncio.create_task(process_message(msg))
    finally:
        # Cleanup
        await consumer.stop()


async def process_message(msg):
    print(f"Received message")
    await topic_router(msg)
    print(f"Processed message: {msg.value.decode('utf-8')}")
    msg.commit()




import logging
import asyncio
from kafka import KafkaConsumer
from kafka.consumer.fetcher import ConsumerRecord

from ajb.base.events import KafkaGroup, KafkaTopic
from ajb.vendor.kafka.client_factory import KafkaConsumerFactory
from ajb.vendor.sentry import capture_exception

from .middleware import verify_message_header_token
from .routing import topic_router
from .health_check import status


COMMIT_INTERVAL = 100  # Commit after every 100 messages
COMMIT_TIME = 10  # Commit every 10 seconds, whichever comes first


async def handle_message(
    message: ConsumerRecord,
    commit_counter: int,
    last_commit_time: float,
    consumer: KafkaConsumer,
):
    await topic_router(message)
    print("SUCCESS: processed message")
    commit_counter += 1
    current_time = asyncio.get_running_loop().time()
    if (
        commit_counter >= COMMIT_INTERVAL
        or (current_time - last_commit_time) >= COMMIT_TIME
    ):
        consumer.commit()
        commit_counter = 0
        last_commit_time = current_time


async def handle_messages(consumer: KafkaConsumer):
    commit_counter = 0
    last_commit_time = asyncio.get_running_loop().time()

    # Create a separate task for running the status report
    asyncio.create_task(status())

    while True:
        topic_messages = consumer.poll(timeout_ms=10)
        if (
            topic_messages is None
            or sum([len(messages) for messages in topic_messages.values()]) == 0
        ):
            await asyncio.sleep(0.1)
            continue

        for messages in topic_messages.values():
            for message in messages:
                print("Message received")
                asyncio.create_task(
                    handle_message(message, commit_counter, last_commit_time, consumer)
                )

                # Yield to the event loop to allow other tasks to run
                await asyncio.sleep(0)


async def consumer():
    consumer = KafkaConsumerFactory(group_id=KafkaGroup.DEFAULT.value).get_client()
    consumer.subscribe([topic.value for topic in KafkaTopic])
    print("Consumer Started...")
    task = asyncio.create_task(handle_messages(consumer))
    try:
        await task
    except asyncio.CancelledError:
        print("Consumer is shutting down...")
        consumer.close()
