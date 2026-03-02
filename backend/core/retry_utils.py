"""
Retry utilities with exponential backoff for network-resilient operations.
Used primarily by browser automation and proxy-based connections.
"""
import asyncio
import logging
from typing import Callable, Tuple, Type

logger = logging.getLogger(__name__)


async def retry_async(
    coro_factory: Callable,
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
    retryable_exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    context_label: str = "operation"
):
    """
    Executes an async callable with retry and exponential backoff.

    Args:
        coro_factory: Callable that returns a new coroutine on each call.
        max_retries: Maximum number of attempts.
        base_delay: Initial delay in seconds before first retry.
        max_delay: Maximum delay cap in seconds.
        retryable_exceptions: Tuple of exception types that trigger a retry.
        context_label: Label for log messages (e.g. "page.goto", "upload").
    
    Returns:
        The result of the successful coroutine call.
    
    Raises:
        The last exception if all retries are exhausted.
    """
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            return await coro_factory()
        except retryable_exceptions as e:
            last_exception = e
            if attempt == max_retries:
                logger.error(
                    f"[RETRY] {context_label} falhou definitivamente apos "
                    f"{max_retries} tentativas: {e}"
                )
                raise
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            logger.warning(
                f"[RETRY] {context_label} falhou (tentativa {attempt}/{max_retries}): {e}. "
                f"Retentando em {delay:.1f}s..."
            )
            await asyncio.sleep(delay)

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


class MissingProxyError(Exception):
    """
    Raised when a profile has no proxy configured in a production environment.
    This is a HARD BLOCK: Playwright must NEVER be launched in production
    using the native datacenter IP for social media automation.
    """

    def __init__(self, profile_slug: str):
        self.profile_slug = profile_slug
        super().__init__(
            f"HARD BLOCK: Perfil '{profile_slug}' nao possui proxy configurado. "
            f"Em ambiente de producao, toda automacao web DEVE usar proxy residencial. "
            f"Configure proxy_server no perfil antes de prosseguir."
        )
