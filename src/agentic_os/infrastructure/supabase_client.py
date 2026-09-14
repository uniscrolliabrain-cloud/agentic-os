from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .config.settings import settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Cliente Supabase unificado: Auth + DB (PostgREST) + Storage.

    Singleton por proceso. Expone los 3 subclientes:
      - .db:   PostgREST (SQL/relacional sobre el esquema Supabase)
      - .auth: Supabase Auth (JWT RS256)
      - .storage: Supabase Storage (buckets de archivos)
    """

    _instance: Optional["SupabaseClient"] = None

    def __init__(self) -> None:
        url = settings.supabase_url
        key = settings.supabase_key
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL y SUPABASE_KEY deben estar configurados"
            )
        self._url = url
        self._key = key
        self._db: Optional[Any] = None
        self._auth: Optional[Any] = None
        self._storage: Optional[Any] = None
        self._initialized = False

    @classmethod
    def get(cls) -> "SupabaseClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    def _init(self) -> None:
        if self._initialized:
            return
        try:
            from supabase import create_client

            self._db = create_client(self._url, self._key)
            self._auth = self._db.auth
            self._storage = self._db.storage
            self._initialized = True
        except Exception as exc:
            logger.error("Failed to init Supabase client: %s", exc)
            raise

    @property
    def db(self) -> Any:
        """PostgREST client: .table(name).select().eq().execute()"""
        if self._db is None:
            self._init()
        return self._db

    @property
    def auth(self) -> Any:
        """Supabase Auth client: sign_in, verify, get_user"""
        if self._auth is None:
            self._init()
        return self._auth

    @property
    def storage(self) -> Any:
        """Supabase Storage client: bucket operations"""
        if self._storage is None:
            self._init()
        return self._storage

    def service_key_client(self) -> Any:
        """Cliente con service_role_key (admin, sin restricciones RLS)."""
        sk = settings.supabase_service_role_key
        if not sk:
            raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY no configurado")
        try:
            from supabase import create_client

            return create_client(self._url, sk)
        except Exception as exc:
            logger.error("Failed to init Supabase service client: %s", exc)
            raise


def get_supabase() -> SupabaseClient:
    return SupabaseClient.get()
