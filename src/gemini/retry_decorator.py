import asyncio

def retry(max_retries=3, delay=1, backoff=2, exceptions=(Exception,)):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            retries = max_retries
            current_delay = delay
            while retries > 1:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    print(f"Retrying due to {e}, {retries-1} retries left...")
                    await asyncio.sleep(current_delay)
                    retries -= 1
                    current_delay *= backoff
            return await func(*args, **kwargs)  # Last attempt
        return wrapper
    return decorator
