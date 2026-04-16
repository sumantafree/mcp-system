"""Request logging middleware."""
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("mcp.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start) * 1000, 2)

        logger.info(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} ({duration_ms}ms) "
            f"[{request.client.host if request.client else 'unknown'}]"
        )
        response.headers["X-Process-Time"] = str(duration_ms)
        return response
