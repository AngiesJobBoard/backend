from ajb.base.events import UserEvent, BaseKafkaMessage
from services.resolvers.users import UserEventResolver

from services.vendors import (
    openai,
    sendgrid,
    make_request_scope,
)


async def user_is_created(message: BaseKafkaMessage):
    await UserEventResolver(
        message,
        make_request_scope(message),
        openai,
        sendgrid,
    ).user_is_created()


ROUTER = {
    UserEvent.USER_IS_CREATED.value: user_is_created,
}
