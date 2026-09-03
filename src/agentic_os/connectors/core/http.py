from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
import time
import uuid
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import httpx

from agentic_os.execution.tools.base import ToolValidationError

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
LINK_LOCAL_NET = ipaddress.ip_network("169.254.0.0/16")


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
        kwargs: Dict[str, Any] = {
            "timeout": self.timeout,
            "http2": False,
            "headers": {"X-Correlation-Id": self.correlation_id},
        }
        if self.base_url is not None:
            kwargs["base_url"] = self.base_url

        self._client = httpx.AsyncClient(**kwargs)
        return self

    async def __aexit__(self, *exc):
        if self._client:
            await self._client.aclose()
        self._client = None

    @staticmethod
    def _is_blocked_ip(addr: Union[ipaddress.IPv4Address, ipaddress.IPv6Address]) -> bool:
        if (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_reserved
            or addr.is_unspecified
            or str(addr) in ("0.0.0.0", "::")
        ):
            return True
        if isinstance(addr, ipaddress.IPv4Address) and addr in LINK_LOCAL_NET:
            return True
        return False

    @staticmethod
    def _is_ssrf(url: str) -> bool:
        """Protección SSRF fail-closed.

        Bloquea los rangos de red privados/loopback/link-local/multicast/
        unspecified y las representaciones alternas de IP (decimal, octal, hex)
        así como la resolución DNS hacia dichos rangos (DNS rebinding).
        Si la URL no se puede validar o DNS falla -> se bloquea.
        """
        try:
            parsed = urlparse(url)
        except Exception:
            return True
        host = parsed.hostname
        if host is None:
            return True

        lowered = host.strip("[]").lower()

        # 1) IPv4/IPv6 directa
        try:
            addr = ipaddress.ip_address(lowered)
            return HttpClient._is_blocked_ip(addr)
        except ValueError:
            pass

        # 2) IPv6 no parseable con dos puntos
        if ":" in lowered:
            return True

        # 3) Nombres de host locales conocidos
        if lowered in {"localhost", "localtest.me", "0"} or lowered.endswith(".localhost"):
            return True

        # 4) Representaciones alternas de IP
        if HttpClient._is_alt_ip(lowered):
            return True

        # 5) Resolución DNS para verificar todas las direcciones IP (v4 y v6)
        try:
            infos = socket.getaddrinfo(lowered, None)
            if not infos:
                return True
            for info in infos:
                ip_str = info[4][0]
                addr = ipaddress.ip_address(ip_str)
                if HttpClient._is_blocked_ip(addr):
                    return True
        except Exception:
            return True

        return False

    @staticmethod
    def _is_alt_ip(host: str) -> bool:
        """Detecta IPs en notación decimal entera, octal, hex u octetos mixtos."""

        # Entero sin puntos en decimal
        if re.fullmatch(r"[0-9]{1,10}", host):
            try:
                addr = ipaddress.ip_address(int(host))
            except ValueError:
                return False
            return HttpClient._is_blocked_ip(addr)

        # Entero hex: "0x7f000001"
        if re.fullmatch(r"0[xX][0-9a-fA-F]{1,8}", host):
            try:
                addr = ipaddress.ip_address(int(host, 16))
            except ValueError:
                return False
            return HttpClient._is_blocked_ip(addr)

        # Entero octal: "017700000001"
        if re.fullmatch(r"0[0-7]{1,11}", host):
            try:
                addr = ipaddress.ip_address(int(host, 8))
            except ValueError:
                return False
            return HttpClient._is_blocked_ip(addr)

        # IPv4 con octetos alternos
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
                return HttpClient._is_blocked_ip(addr)

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
            raise ToolValidationError("SSRF blocked")

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
