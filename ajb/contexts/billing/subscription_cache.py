"""
The subscriptions object is accessed frequently as users are performing actions in the application
so we keep this TTL cache. This cache is updated if the subscription changes which is why
it is kept in its own module.
"""

from cachetools import TTLCache

SUBSCRIPTION_CACHE = TTLCache(maxsize=100, ttl=60 * 5)
