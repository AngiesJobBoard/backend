import asyncio
from kafka import KafkaConsumer
from kafka.consumer.fetcher import ConsumerRecord

from ajb.base.events import KafkaGroup, KafkaTopic
from ajb.vendor.kafka.client_factory import KafkaConsumerFactory

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
    commit_counter += 1
    current_time = asyncio.get_running_loop().time()
    if (
        commit_counter >= COMMIT_INTERVAL
        or (current_time - last_commit_time) >= COMMIT_TIME
    ):
        consumer.commit()
        commit_counter = 0


async def handle_messages(consumer: KafkaConsumer):
    commit_counter = 0
    last_commit_time = asyncio.get_running_loop().time()

    # Create a separate task for running the status report
    asyncio.create_task(status())

    while True:
        topic_messages = consumer.poll(timeout_ms=10)
        if (
            topic_messages is None
            or sum(len(messages) for messages in topic_messages.values()) == 0
        ):
            await asyncio.sleep(0.1)
            continue

        for messages in topic_messages.values():
            for message in messages:
                asyncio.create_task(
                    handle_message(message, commit_counter, last_commit_time, consumer)
                )

                # Yield to the event loop to allow other tasks to run
                await asyncio.sleep(0)


async def consumer():
    consumer = KafkaConsumerFactory(group_id=KafkaGroup.DEFAULT.value).get_client()
    topics_to_subscribe = [topic.value for topic in KafkaTopic]
    consumer.subscribe(topics_to_subscribe)
    print(f"Connected to server {consumer.config['bootstrap_servers'][0]}")
    print(f"Consumer Subscribed to {topics_to_subscribe}...")
    task = asyncio.create_task(handle_messages(consumer))
    try:
        await task
    except asyncio.CancelledError:
        print("Consumer is shutting down...")
        consumer.close()
