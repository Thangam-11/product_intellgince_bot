from slowapi import Limiter
from slowapi.util import get_remote_address

# Uses client IP address as the rate limit key.
# In production with multiple ECS instances, use Redis backend
# so limits are shared across all containers:
#   Limiter(key_func=get_remote_address, storage_uri="redis://...")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/hour"],
)


def get_limiter() -> Limiter:
    """Returns the configured limiter instance."""
    return limiter
