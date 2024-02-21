import logging
import asyncio
from kafka import KafkaConsumer
from kafka.consumer.fetcher import ConsumerRecord

from ajb.base.events import KafkaGroup, KafkaTopic
from ajb.vendor.kafka.client_factory import KafkaConsumerFactory

from .routing import topic_router
from .health_check import status


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


COMMIT_INTERVAL = 100  # Commit after every 100 messages
COMMIT_TIME = 10  # Commit every 10 seconds, whichever comes first


async def handle_message(
    message: ConsumerRecord,
    commit_counter: int,
    last_commit_time: float,
    consumer: KafkaConsumer,
):
    await topic_router(message)
    logger.info("SUCCESS: processed message")
    commit_counter += 1
    current_time = asyncio.get_running_loop().time()
    if (
        commit_counter >= COMMIT_INTERVAL
        or (current_time - last_commit_time) >= COMMIT_TIME
    ):
        consumer.commit()
        logger.info("Committed %s messages", commit_counter)
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
            or sum(len(messages) for messages in topic_messages.values()) == 0
        ):
            await asyncio.sleep(0.1)
            continue

        tasks = []
        for messages in topic_messages.values():
            for message in messages:
                logger.info("Message received")
                task = handle_message(message, commit_counter, last_commit_time, consumer)
                tasks.append(task)

        # Run all tasks concurrently
        await asyncio.gather(*tasks)


async def consumer():
    consumer = KafkaConsumerFactory(group_id=KafkaGroup.DEFAULT.value).get_client()
    consumer.subscribe([topic.value for topic in KafkaTopic])
    logger.info("Consumer Started...")

    # Create multiple tasks for handle_messages
    tasks = [asyncio.create_task(handle_messages(consumer)) for _ in range(4)]

    try:
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logger.info("Consumer is shutting down...")
        consumer.close()