from ajb.base import ParentRepository, RepositoryRegistry, Collection

from .models import CreateRawIngressApplication, RawIngressApplication


class RawIngressApplicationRepository(ParentRepository[CreateRawIngressApplication, RawIngressApplication]):
    collection = Collection.RAW_INGRESS_APPLICATIONS
    entity_model = RawIngressApplication


RepositoryRegistry.register(RawIngressApplicationRepository)
