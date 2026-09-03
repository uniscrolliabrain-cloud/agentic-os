from __future__ import annotations

import asyncio
import ipaddress
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
        """Protección SSRF fail-closed.

        Bloquea los rangos de red privados/loopback/link-local/multicast/
        unspecified y las representaciones alternas de IP (decimal, octal, hex)
        que algunos clientes resuelven aunque `urlparse` no las normalice.
        Si la URL no se puede validar -> se bloquea.
        """
        try:
            parsed = urlparse(url)
        except Exception:
            return True
        host = parsed.hostname
        if host is None:
            return True

        lowered = host.strip("[]").lower()

        # 1) IPv4/IPv6 directa: descartar según propiedades del address.
        try:
            addr = ipaddress.ip_address(lowered)
        except ValueError:
            addr = None

        if addr is not None:
            return (
                addr.is_loopback
                or addr.is_link_local
                or addr.is_multicast
                or addr.is_private
                or addr.is_unspecified
                or addr.is_reserved
            )

        # 2) IPv6 no parseable (zona, malformado) -> fail-closed.
        if ":" in lowered:
            return True

        # 3) Nombres de host locales.
        if lowered in {"localhost", "localtest.me", "0"}:
            return True
        if lowered.endswith(".localhost"):
            return True

        # 4) Representaciones alternas de IP (decimal/octal/hex, octetos mixtos).
        if HttpClient._is_alt_ip(lowered):
            return True

        return False

    @staticmethod
    def _is_alt_ip(host: str) -> bool:
        """Detecta IPs en notación decimal entera, octal, hex u octetos mixtos."""

        # Entero sin puntos en decimal: "2130706433" -> 127.0.0.1
        if re.fullmatch(r"[0-9]{1,10}", host):
            try:
                addr = ipaddress.ip_address(int(host))
            except ValueError:
                return False
            return (
                addr.is_private
                or addr.is_loopback
                or addr.is_link_local
                or addr.is_unspecified
            )

        # Entero hex: "0x7f000001"
        if re.fullmatch(r"0[xX][0-9a-fA-F]{1,8}", host):
            try:
                addr = ipaddress.ip_address(int(host, 16))
            except ValueError:
                return False
            return (
                addr.is_private
                or addr.is_loopback
                or addr.is_link_local
                or addr.is_unspecified
            )

        # Entero octal: "017700000001"
        if re.fullmatch(r"0[0-7]{1,11}", host):
            try:
                addr = ipaddress.ip_address(int(host, 8))
            except ValueError:
                return False
            return (
                addr.is_private
                or addr.is_loopback
                or addr.is_link_local
                or addr.is_unspecified
            )

        # IPv4 con octetos alternos: "0177.0.0.1", "0x7f.0.0.1", "127.1"
        parts = host.split(".")
        if 2 <= len(parts) <= 4:
            octets = []
            try:
                for part in parts:
                    if not part:
                        raise ValueError
                    if part.startswith("0x") or part.startswith("0X"):
                        octets.append(int(part, 16))
                    elif part.startswith("0") and len(part) > 1:
                        octets.append(int(part, 8))
                    else:
                        octets.append(int(part, 10))
            except (ValueError, TypeError):
                return False
            if all(0 <= o <= 255 for o in octets):
                try:
                    addr = ipaddress.ip_address(bytes(octets))
                except ValueError:
                    return False
                return (
                    addr.is_private
                    or addr.is_loopback
                    or addr.is_link_local
                    or addr.is_unspecified
                )

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
