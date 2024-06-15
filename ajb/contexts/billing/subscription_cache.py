from cachetools import TTLCache

SUBSCRIPTION_CACHE = TTLCache(maxsize=100, ttl=60 * 5)
