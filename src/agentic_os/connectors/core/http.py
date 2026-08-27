from __future__ import annotations

import asyncio
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import httpx

from .errors import (
    AuthenticationError,
    NetworkError,
    ProviderError,
    RateLimitError,
    TimeoutError_,
    ValidationError,
    normalize_exception,
)

SENSITIVE_HEADERS = {"authorization", "authorization", "cookie", "set-cookie"}


def _safe_headers(headers: Optional[Dict[str, str]]) -> Dict[str, str]:
    if not headers:
        return {}
    safe = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in SENSITIVE_HEADERS:
            safe[k] = "***REDACTED***"
        elif lk in ("access_token", "refresh_token", "api_key", "password", "secret"):
            safe[k] = "***REDACTED***"
        else:
            safe[k] = v
    return safe


class HttpClient:
    def __init__(
        self,
        timeout_s: float = 30.0,
        retries: int = 3,
        base_url: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ):
        self.timeout = timeout_s
        self.retries = retries
        self.base_url = base_url
        self.correlation_id = correlation_id or uuid.uuid4().hex
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            http2=False,
            headers={"X-Correlation-Id": self.correlation_id},
        )
        return self

    async def __aexit__(self, *exc):
        if self._client:
            await self._client.aclose()
        self._client = None

    @staticmethod
    def _is_ssrf(url: str) -> bool:
        try:
            parsed = urlparse(url)
        except Exception:
            return True
        host = parsed.hostname or ""
        if host in {"localhost", "127.0.0.1", "::1"}:
            return True
        if host.startswith("10.") or host.startswith("192.168."):
            return True
        if host.startswith("172."):
            try:
                second = int(host.split(".")[1])
            except (IndexError, ValueError):
                return True
            if 16 <= second <= 31:
                return True
        return False

    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        content: Optional[Union[str, bytes]] = None,
        json: Optional[Dict[str, Any]] = None,
        form: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        if self._is_ssrf(url):
            raise ValidationError(f"URL bloqueada por SSRF protection: {url}")

        client = self._client or httpx.AsyncClient(timeout=self.timeout, http2=False)
        attempt = 0
        base_delay = 1.0
        while True:
            attempt += 1
            try:
                resp = await client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    params=params,
                    content=content,
                    json=json,
                    data=form,
                    files=files,
                    timeout=timeout or self.timeout,
                )
                return resp
            except httpx.TimeoutException as e:
                if attempt >= self.retries:
                    raise TimeoutError_(str(e)) from e
                await self._sleep(base_delay, attempt)
            except httpx.HTTPStatusError as e:
                code = e.response.status_code if hasattr(e, "response") else 500
                if code == 429:
                    retry_after = e.response.headers.get("Retry-After")
                    raise RateLimitError(
                        str(e), retry_after=retry_after, code=code
                    ) from e
                if code >= 500:
                    if attempt >= self.retries:
                        raise ProviderError(str(e), code=code) from e
                    await self._sleep(base_delay, attempt)
                elif code in (401, 403):
                    raise AuthenticationError(str(e), code=code) from e
                else:
                    raise normalize_exception(e) from e
            except httpx.HTTPError as e:
                if attempt >= self.retries:
                    raise NetworkError(str(e)) from e
                await self._sleep(base_delay, attempt)

    async def _sleep(self, base: float, attempt: int):
        delay = min(base * (2 ** (attempt - 1)), 30.0)
        await asyncio.sleep(delay + (0.1 * uuid.uuid4().int % 100))
