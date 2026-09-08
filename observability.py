"""Request correlation, structured access logging, and local safety-net rate limiting."""
from __future__ import annotations

import asyncio
from collections import OrderedDict, deque
from datetime import datetime, timezone
import json
import logging
import re
import time
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "request_id", "method", "path", "status", "latency_ms", "client_ip",
            "event", "database_revision", "api_version",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(*, level: str = "INFO", json_logs: bool = False) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter() if json_logs else logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    # Avoid duplicate handlers when tests reload/import the application.
    root.handlers.clear()
    root.addHandler(handler)
    logging.getLogger("uvicorn.access").disabled = True


def _request_id(request: Request) -> str:
    supplied = request.headers.get("x-request-id", "").strip()
    if supplied and _REQUEST_ID_RE.fullmatch(supplied):
        return supplied
    return str(uuid.uuid4())


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, log_client_ip: bool = False):
        super().__init__(app)
        self.log_client_ip = log_client_ip
        self.logger = logging.getLogger("medical_api.access")

    async def dispatch(self, request: Request, call_next):
        request_id = _request_id(request)
        request.state.request_id = request_id
        started = time.perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            latency_ms = round((time.perf_counter() - started) * 1000, 3)
            extra = {
                "request_id": request_id,
                "method": request.method,
                # Deliberately exclude query strings: SAE searches may reflect clinical context.
                "path": request.url.path,
                "status": status,
                "latency_ms": latency_ms,
            }
            if self.log_client_ip and request.client:
                extra["client_ip"] = request.client.host
            self.logger.info("request_complete", extra=extra)


class SlidingWindowLimiter:
    """Single-process sliding-window limiter.

    The reverse proxy remains authoritative for multi-worker/multi-instance deployments.
    This limiter is a defence-in-depth fallback and protects direct application access.
    """

    def __init__(self, max_clients: int = 10_000):
        self.max_clients = max_clients
        self._clients: OrderedDict[str, deque[float]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def check(self, key: str, *, limit: int, window_seconds: int = 60) -> tuple[bool, int, int]:
        now = time.monotonic()
        cutoff = now - window_seconds
        async with self._lock:
            bucket = self._clients.get(key)
            if bucket is None:
                if len(self._clients) >= self.max_clients:
                    self._clients.popitem(last=False)
                bucket = deque()
                self._clients[key] = bucket
            else:
                self._clients.move_to_end(key)
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                retry_after = max(1, int(window_seconds - (now - bucket[0])) + 1)
                return False, 0, retry_after
            bucket.append(now)
            remaining = max(0, limit - len(bucket))
            return True, remaining, window_seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        enabled: bool,
        api_limit_per_minute: int,
        search_limit_per_minute: int,
        max_clients: int = 10_000,
    ):
        super().__init__(app)
        self.enabled = enabled
        self.api_limit = api_limit_per_minute
        self.search_limit = search_limit_per_minute
        self.limiter = SlidingWindowLimiter(max_clients=max_clients)

    @staticmethod
    def _is_limited_path(path: str) -> bool:
        return path.startswith("/api/") or path.startswith("/sae/") or path.startswith("/policy/") or path == "/pnaism/"

    @staticmethod
    def _is_health_path(path: str) -> bool:
        return path in {"/api/v1/livez", "/api/v1/readyz", "/api/v1/healthz", "/healthz"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not self.enabled or self._is_health_path(path) or not self._is_limited_path(path):
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        limit = self.search_limit if path.endswith("/sae/search") else self.api_limit
        allowed, remaining, retry_after = await self.limiter.check(f"{client}:{path.endswith('/sae/search')}", limit=limit)
        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Retry later."},
                headers={"Retry-After": str(retry_after)},
            )
        else:
            response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
