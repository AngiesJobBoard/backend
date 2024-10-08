import time
import json
from kafka.consumer.fetcher import ConsumerRecord
from ajb.base.events import KafkaTopic, BaseKafkaMessage
from services.topics.companies import ROUTER as companies_router
from services.topics.users import ROUTER as users_router
from services.topics.applications import ROUTER as applications_router


ROUTER = {
    KafkaTopic.COMPANIES: companies_router,
    KafkaTopic.USERS: users_router,
    KafkaTopic.APPLICATIONS: applications_router,
}


async def topic_router(message: ConsumerRecord):
    message_data = BaseKafkaMessage(**json.loads(message.value))
    print(f"Received event: {message_data.event_type}")
    start = time.time()
    await ROUTER[message_data.topic][message_data.event_type](message_data)
    print(
        f"Completed processing event: {message_data.event_type} in {round(time.time() - start, 3)} seconds."
    )
