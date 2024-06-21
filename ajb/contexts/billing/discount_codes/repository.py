from ajb.base import (
    ParentRepository,
    Collection,
    RepositoryRegistry,
)

from .models import CreateDiscountCode, DiscountCode


class DiscountCodeRepository(ParentRepository[CreateDiscountCode, DiscountCode]):
    collection = Collection.DISCOUNT_CODES
    entity_model = DiscountCode


RepositoryRegistry.register(DiscountCodeRepository)
