import time
import functools
import logging
import asyncio
import inspect
from sqlalchemy.exc import OperationalError
from typing import Callable, Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

def retry_db_op(func: Callable[[], T], max_retries: int = 5, base_delay: float = 0.5) -> T:
    """
    Functional retry helper for specific DB blocks.
    Executes 'func' (callable taking no args) with retries.
    """
    for attempt in range(max_retries):
        try:
            return func()
        except OperationalError as e:
            if "locked" in str(e).lower():
                if attempt < max_retries - 1:
                    sleep_time = base_delay * (2 ** attempt)
                    logger.warning(f"⚠️ DB Locked (Block). Retrying in {sleep_time}s (Attempt {attempt + 1}/{max_retries})...")
                    time.sleep(sleep_time)
                    continue
            logger.error(f"❌ DB Error (Block): {e}")
            raise e
        except Exception as e:
            raise e
    return None

def with_db_retries(max_retries: int = 5, base_delay: float = 0.5) -> Callable:
    """
    Smart Decorator for Sync AND Async functions.
    Retries database operations when a lock occurs.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except OperationalError as e:
                    if "locked" in str(e).lower():
                        if attempt < max_retries - 1:
                            sleep_time = base_delay * (2 ** attempt)
                            logger.warning(f"⚠️ DB Locked in async {func.__name__}. Retrying in {sleep_time}s (Attempt {attempt + 1}/{max_retries})...")
                            await asyncio.sleep(sleep_time)
                            continue
                    logger.error(f"❌ DB Error in async {func.__name__}: {e}")
                    raise e
                except Exception as e:
                    raise e
            return None

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if "locked" in str(e).lower():
                        if attempt < max_retries - 1:
                            sleep_time = base_delay * (2 ** attempt)
                            logger.warning(f"⚠️ DB Locked in {func.__name__}. Retrying in {sleep_time}s (Attempt {attempt + 1}/{max_retries})...")
                            time.sleep(sleep_time)
                            continue
                    logger.error(f"❌ DB Error in {func.__name__}: {e}")
                    raise e
                except Exception as e:
                    raise e
            return None

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
