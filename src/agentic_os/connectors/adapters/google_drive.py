"""Adapter real de Google Drive API v3."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx

from ..core.errors import AuthenticationError, NotFoundError, ProviderError
from .google_auth import GoogleAuth

BASE_URL = "https://www.googleapis.com/drive/v3"
UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3"


class GoogleDriveAdapter:
    """Cliente síncrono para Google Drive API v3."""

    def __init__(self, auth: Optional[GoogleAuth] = None):
        self._auth = auth or GoogleAuth()
        self._client = httpx.Client(timeout=30.0, http2=False)

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._auth.access_token()}"}

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        url = f"{BASE_URL}{path}"
        resp = self._client.request(method, url, headers=self._headers(), **kwargs)
        if resp.status_code == 404:
            raise NotFoundError(f"Recurso Drive no encontrado: {path}", provider="google")
        if resp.status_code in (401, 403):
            raise AuthenticationError(
                f"Error autenticación Google Drive ({resp.status_code})",
                provider="google",
                code=resp.status_code,
            )
        if resp.status_code >= 400:
            raise ProviderError(
                f"Error Google Drive ({resp.status_code}): {resp.text[:200]}",
                provider="google",
                code=resp.status_code,
            )
        return resp.json()

    def list_files(self, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista archivos; si folder_id se proporciona, filtra por padres."""
        query = "trashed=false"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        params = {"q": query, "fields": "files(id,name,size,mimeType,modifiedTime)", "pageSize": 100}
        data = self._request("GET", "/files", params=params)
        return [
            {
                "id": f.get("id", ""),
                "name": f.get("name", ""),
                "size": f.get("size", ""),
                "mime_type": f.get("mimeType", ""),
                "modified": f.get("modifiedTime", ""),
            }
            for f in data.get("files", [])
        ]

    def read_file(self, file_id: str) -> Dict[str, Any]:
        """Lee metadata + contenido de un archivo de texto."""
        meta = self._request("GET", f"/files/{file_id}", params={"fields": "id,name,mimeType,size"})
        url = f"{BASE_URL}/files/{file_id}?alt=media"
        resp = self._client.get(url, headers=self._headers())
        if resp.status_code >= 400:
            raise ProviderError(f"Error leyendo archivo Drive ({resp.status_code})", provider="google")
        content = resp.text if "text" in meta.get("mimeType", "") else f"<binary:{meta.get('mimeType')}>"
        return {"id": meta["id"], "name": meta["name"], "mime_type": meta.get("mimeType", ""), "content": content}

    def create_file(self, name: str, content: str, mime_type: str = "text/plain", folder_id: Optional[str] = None) -> Dict[str, Any]:
        """Crea un archivo de texto en Drive vía multipart upload."""
        metadata = {"name": name, "mimeType": mime_type}
        if folder_id:
            metadata["parents"] = [folder_id]
        body = (
            "--boundary\r\n"
            "Content-Type: application/json; charset=UTF-8\r\n\r\n"
            f"{json.dumps(metadata)}\r\n"
            "--boundary\r\n"
            f"Content-Type: {mime_type}\r\n\r\n"
            f"{content}\r\n"
            "--boundary--\r\n"
        )
        headers = {
            **self._headers(),
            "Content-Type": "multipart/related; boundary=boundary",
        }
        resp = self._client.post(
            f"{UPLOAD_URL}/files?uploadType=multipart",
            headers=headers,
            content=body.encode("utf-8"),
        )
        if resp.status_code >= 400:
            raise ProviderError(
                f"Error creando archivo Drive ({resp.status_code}): {resp.text[:200]}",
                provider="google",
            )
        result = resp.json()
        return {
            "id": result.get("id", ""),
            "name": result.get("name", name),
            "mime_type": result.get("mimeType", mime_type),
        }

    def search(self, name_contains: str) -> List[Dict[str, Any]]:
        """Busca archivos por nombre (operador `contains`)."""
        query = f"name contains '{name_contains}' and trashed=false"
        params = {"q": query, "fields": "files(id,name,mimeType)"}
        data = self._request("GET", "/files", params=params)
        return [{"id": f.get("id", ""), "name": f.get("name", ""), "mime_type": f.get("mimeType", "")} for f in data.get("files", [])]

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "GoogleDriveAdapter":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
