"""
Server-side caching setup for all API endpoints
Caching strategy based on user requirements:

Daily Cache (24 hours):
- available-years (rarely change)
- available-weeks (rarely change)
- bench-heroes (daily updates)
- streak-records (daily analysis)

Weekly Cache (7 days):
- champions (historical data)
- team-legacy (historical analysis)

Hourly Cache (1 hour):
- matchups (game results)

Short Cache (5 minutes):
- league-stats (current season stats)
- standings (current standings)

No Cache:
- health (always fresh)
"""

import time
from functools import wraps

# Global cache storage
cache_storage = {}

# Cache TTL constants (in seconds)
CACHE_DURATIONS = {
    'daily': 24 * 60 * 60,      # 24 hours
    'weekly': 7 * 24 * 60 * 60, # 7 days
    'hourly': 60 * 60,          # 1 hour
    'short': 5 * 60,            # 5 minutes
    'never': 0                  # No cache
}

# Endpoint-specific cache settings
ENDPOINT_CACHE_CONFIG = {
    # Daily cache
    '/available-years': 'daily',
    '/available-weeks': 'daily',
    '/bench-heroes': 'daily',
    '/streak-records': 'daily',
    '/luck-analysis': 'daily',

    # Weekly cache
    '/champions': 'weekly',
    '/team-legacy': 'weekly',

    # Hourly cache
    '/matchups': 'hourly',

    # Short cache
    '/league/stats': 'short',
    '/standings': 'short',

    # No cache
    '/health': 'never'
}

def get_cache_duration(endpoint_path):
    """Get cache duration for an endpoint"""
    # Check exact matches first
    if endpoint_path in ENDPOINT_CACHE_CONFIG:
        cache_type = ENDPOINT_CACHE_CONFIG[endpoint_path]
        return CACHE_DURATIONS[cache_type]

    # Check partial matches for parameterized endpoints
    for pattern, cache_type in ENDPOINT_CACHE_CONFIG.items():
        if pattern.replace('/{', '/').replace('}', '') in endpoint_path:
            return CACHE_DURATIONS[cache_type]

    # Default to short cache
    return CACHE_DURATIONS['short']

def cached_endpoint(endpoint_path):
    """Decorator to add caching to FastAPI endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{endpoint_path}_{hash(str(args) + str(kwargs))}"
            current_time = time.time()

            # Get cache duration for this endpoint
            cache_duration = get_cache_duration(endpoint_path)

            # Skip cache if duration is 0
            if cache_duration == 0:
                print(f"🚫 No cache for {endpoint_path}")
                return await func(*args, **kwargs)

            # Check cache
            if cache_key in cache_storage:
                data, timestamp = cache_storage[cache_key]
                age = current_time - timestamp

                if age < cache_duration:
                    print(f"🔄 Cache HIT for {endpoint_path} (age: {int(age)}s)")
                    return data
                else:
                    print(f"⏰ Cache EXPIRED for {endpoint_path} (age: {int(age)}s)")

            # Cache miss - fetch fresh data
            print(f"🆕 Cache MISS for {endpoint_path} - fetching fresh data")
            result = await func(*args, **kwargs)

            # Store in cache
            cache_storage[cache_key] = (result, current_time)

            return result
        return wrapper
    return decorator

def get_cache_stats():
    """Get cache statistics"""
    current_time = time.time()
    stats = {
        'total_entries': len(cache_storage),
        'cache_entries': []
    }

    for key, (data, timestamp) in cache_storage.items():
        age = current_time - timestamp
        stats['cache_entries'].append({
            'key': key,
            'age_seconds': int(age),
            'size_estimate': len(str(data))
        })

    return stats

def clear_cache():
    """Clear all cache entries"""
    global cache_storage
    cache_storage = {}
    print("🗑️ Cache cleared")