from ajb.base import ParentRepository, Collection, RepositoryRegistry
from .models import CreateScheduledEvent, ScheduledEvent


class ScheduledEventsRepository(ParentRepository[CreateScheduledEvent, ScheduledEvent]):
    collection = Collection.SCHEDULED_EVENTS
    entity_model = ScheduledEvent


RepositoryRegistry.register(ScheduledEventsRepository)
