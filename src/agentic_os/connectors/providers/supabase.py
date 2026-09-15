from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..core.base import Connector
from ..core.config import ConnectorConfig
from ..core.errors import ConnectorError, ConnectorUnavailable
from ..core.models import Command, CommandResult, CredentialStatus, HealthStatusModel

logger = logging.getLogger(__name__)


class SupabaseConnector(Connector):
    """Connector para toda la plataforma Supabase.

    Agrupa 3 familias de capabilities:
      - storage.*  (Storage buckets via Supabase Storage API)
      - auth.*     (Auth via Supabase Auth)
      - db.*       (SQL via PostgREST / Supabase DB)
    """

    connector_id = "supabase"
    provider = "Supabase"
    version = "0.1.0"

    capabilities: List[str] = [
        # Storage
        "storage.file.upload",
        "storage.file.download",
        "storage.file.read",
        "storage.file.delete",
        "storage.folder.create",
        "storage.folder.list",
        "storage.bucket.create",
        "storage.bucket.list",
        # Auth
        "auth.signin.email",
        "auth.signin.oauth",
        "auth.signout",
        "auth.user.get",
        "auth.user.update",
        "auth.token.refresh",
        "auth.jwt.verify",
        # DB (PostgREST)
        "db.query",
        "db.record.create",
        "db.record.read",
        "db.record.update",
        "db.record.delete",
        "db.schema.inspect",
    ]

    auth_type = "bearer"

    def __init__(
        self,
        connector_id: str = "supabase",
        provider: str = "Supabase",
        capabilities: List[str] | None = None,
        auth_type: str = "bearer",
        config: Optional[Dict[str, Any]] = None,
        credentials: Optional[Dict[str, Any]] = None,
        connected: bool = False,
    ) -> None:
        self.connector_id = connector_id
        self.provider = provider
        self.capabilities = capabilities or self.capabilities
        self.auth_type = auth_type
        self._config = config or {}
        self._credentials = credentials or {}
        self.connected = connected and bool(credentials)
        self._client: Optional[Any] = None

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        url = self._credentials.get("url") or self._config.get("url")
        key = self._credentials.get("key") or self._config.get("key")
        if not url or not key:
            return None
        try:
            from supabase import create_client

            self._client = create_client(url, key)
            return self._client
        except Exception as exc:
            logger.error("Supabase client init failed: %s", exc)
            return None

    async def health_check(self) -> HealthStatusModel:
        if not self.connected:
            return HealthStatusModel(
                status="AUTH_REQUIRED",
                provider=self.provider,
                detail="Connector 'supabase' sin conectar (falta SUPABASE_URL/SUPABASE_KEY).",
            )
        client = self._get_client()
        if client is None:
            return HealthStatusModel(
                status="UNAVAILABLE",
                provider=self.provider,
                detail="No se pudo conectar a Supabase.",
            )
        return HealthStatusModel(status="HEALTHY", provider=self.provider)

    async def validate_credentials(self) -> CredentialStatus:
        if not self.connected:
            return CredentialStatus(status="missing", provider=self.provider, detail="No configurado")
        client = self._get_client()
        if client is None:
            return CredentialStatus(status="invalid", provider=self.provider, detail="URL/KEY invlidos")
        return CredentialStatus(status="valid", provider=self.provider)

    async def execute(self, command: Command) -> CommandResult:
        if command.dry_run:
            return CommandResult(
                ok=True,
                dry_run=True,
                preview={
                    "connector": self.connector_id,
                    "provider": self.provider,
                    "capability": command.capability,
                    "payload_summary": {k: f"<{type(v).__name__}>" for k, v in (command.params or {}).items()},
                    "risk": "READ_ONLY",
                    "note": "dry-run: no se ejecut",
                },
                execution_id=command.execution_id,
                connector_id=self.connector_id,
                provider=self.provider,
                capability=command.capability,
            )

        if not self.connected:
            return self._not_configured(command)

        client = self._get_client()
        if client is None:
            return CommandResult(
                ok=False,
                error="No se pudo conectar a Supabase",
                error_type="CONNECTOR_NOT_CONFIGURED",
                execution_id=command.execution_id,
                connector_id=self.connector_id,
                provider=self.provider,
                capability=command.capability,
            )

        capability = command.capability
        params = command.params or {}

        try:
            if capability.startswith("storage."):
                return await self._exec_storage(client, capability, params, command)
            elif capability.startswith("auth."):
                return await self._exec_auth(client, capability, params, command)
            elif capability.startswith("db."):
                return await self._exec_db(client, capability, params, command)
            else:
                return CommandResult(
                    ok=False,
                    error=f"Capability no soportada: {capability}",
                    error_type="UNSUPPORTED_OPERATION",
                    execution_id=command.execution_id,
                    connector_id=self.connector_id,
                    provider=self.provider,
                    capability=capability,
                )
        except ConnectorError:
            raise
        except ValueError as exc:
            logger.warning("Validation error: %s", exc)
            return CommandResult(
                ok=False, error=str(exc), error_type="INVALID_PARAMS",
                execution_id=command.execution_id, connector_id=self.connector_id,
                provider=self.provider, capability=capability,
            )
        except Exception as exc:
            logger.exception("Supabase execute failed")
            return CommandResult(
                ok=False,
                error=f"Supabase error: {exc}",
                error_type="PROVIDER_ERROR",
                execution_id=command.execution_id,
                connector_id=self.connector_id,
                provider=self.provider,
                capability=capability,
            )

    async def _exec_storage(self, client: Any, capability: str, params: Dict[str, Any], command: Command) -> CommandResult:
        storage = client.storage
        _storage_from = getattr(storage, "from")

        if capability == "storage.file.upload":
            bucket = params.get("bucket", "")
            path = params.get("path", "")
            file_obj = params.get("file")
            if file_obj is None:
                raise ValueError("file es obligatorio")
            _storage_from(bucket).upload(path, file_obj)
            return CommandResult(ok=True, output={"path": path, "bucket": bucket}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "storage.file.download":
            bucket = params.get("bucket", "")
            path = params.get("path", "")
            res = _storage_from(bucket).download(path)
            return CommandResult(ok=True, output={"data": res, "bucket": bucket, "path": path}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "storage.file.read":
            bucket = params.get("bucket", "")
            path = params.get("path", "")
            res = _storage_from(bucket).download(path)
            return CommandResult(ok=True, output={"data": res}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability in ("storage.file.delete", "storage.file.remove"):
            bucket = params.get("bucket", "")
            path = params.get("path", "")
            _storage_from(bucket).remove([path])
            return CommandResult(ok=True, output={"deleted": path}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "storage.bucket.create":
            bucket = params.get("bucket", "")
            storage.create_bucket(bucket)
            return CommandResult(ok=True, output={"bucket": bucket}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "storage.bucket.list":
            try:
                buckets = storage.list_buckets()
            except Exception as exc:
                logger.error("Supabase bucket list failed: %s", exc)
                return CommandResult(
                    ok=False, error=f"Error al listar buckets: {exc}",
                    error_type="PROVIDER_ERROR",
                    execution_id=command.execution_id, connector_id=self.connector_id,
                    provider=self.provider, capability=capability,
                )
            return CommandResult(ok=True, output={"buckets": buckets}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "storage.folder.create":
            bucket = params.get("bucket", "")
            path = params.get("path", "")
            _storage_from(bucket).upload(path + "/.keep", b"")
            return CommandResult(ok=True, output={"folder": path}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "storage.folder.list":
            bucket = params.get("bucket", "")
            prefix = params.get("prefix", "")
            folder_prefix = (prefix.rstrip("/") + "/") if prefix else ""
            res = _storage_from(bucket).list(folder_prefix, {"limit": params.get("limit", 100)})
            return CommandResult(ok=True, output={"items": res}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "storage.file.list":
            bucket = params.get("bucket", "")
            prefix = params.get("prefix", "")
            res = _storage_from(bucket).list(prefix, {"limit": params.get("limit", 100)})
            return CommandResult(ok=True, output={"items": res}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        return CommandResult(ok=False, error=f"Unknown storage capability: {capability}", error_type="UNSUPPORTED_OPERATION", connector_id=self.connector_id, provider=self.provider, capability=capability)

    async def _exec_auth(self, client: Any, capability: str, params: Dict[str, Any], command: Command) -> CommandResult:
        auth = client.auth

        if capability == "auth.signin.email":
            email = params.get("email")
            password = params.get("password")
            res = auth.sign_in_with_password({"email": email, "password": password})
            return CommandResult(ok=True, output={"user": res.user, "access_token": res.access_token}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "auth.signin.oauth":
            provider = params.get("provider", "google")
            res = auth.sign_in_with_oauth({"provider": provider})
            return CommandResult(ok=True, output={"url": res.url}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "auth.signout":
            auth.sign_out()
            return CommandResult(ok=True, output={}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "auth.user.get":
            user = auth.get_user()
            return CommandResult(ok=True, output={"user": user}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "auth.user.update":
            data = params.get("data", {})
            res = auth.update_user(data)
            return CommandResult(ok=True, output={"user": res.user}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "auth.token.refresh":
            res = auth.refresh_session()
            return CommandResult(ok=True, output={"access_token": res.access_token}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "auth.jwt.verify":
            token = params.get("token")
            from ...infrastructure.auth.jwt_verifier import get_verifier
            verifier = get_verifier()
            claims = verifier.verify(token)
            return CommandResult(ok=True, output={"claims": claims.model_dump()}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        return CommandResult(ok=False, error=f"Unknown auth capability: {capability}", error_type="UNSUPPORTED_OPERATION", connector_id=self.connector_id, provider=self.provider, capability=capability)

    async def _exec_db(self, client: Any, capability: str, params: Dict[str, Any], command: Command) -> CommandResult:
        db = client.db

        if capability == "db.query":
            sql = params.get("query") or params.get("sql")
            if not sql:
                return CommandResult(
                    ok=False, error="Parámetro 'query' es obligatorio para db.query",
                    error_type="INVALID_PARAMS",
                    execution_id=command.execution_id, connector_id=self.connector_id,
                    provider=self.provider, capability=capability,
                )
            try:
                import psycopg
            except ImportError:
                return CommandResult(
                    ok=False, error="psycopg no instalado para db.query",
                    error_type="PROVIDER_ERROR",
                    execution_id=command.execution_id, connector_id=self.connector_id,
                    provider=self.provider, capability=capability,
                )
            dsn = self._credentials.get("dsn") or self._config.get("dsn")
            if not dsn:
                try:
                    from ...infrastructure.config.settings import settings as _s
                    dsn = _s.supabase_dsn or _s.postgres_dsn
                except Exception:
                    dsn = None
            if not dsn:
                return CommandResult(
                    ok=False,
                    error="DSN no configurada para db.query (SUPABASE_DSN o POSTGRES_DSN)",
                    error_type="CONNECTOR_NOT_CONFIGURED",
                    execution_id=command.execution_id, connector_id=self.connector_id,
                    provider=self.provider, capability=capability,
                )
            try:
                with psycopg.connect(dsn, connect_timeout=10) as conn:
                    with conn.cursor() as cur:
                        cur.execute(sql)
                        if cur.description:
                            columns = [d.name for d in cur.description]
                            rows = cur.fetchall()
                            data = [dict(zip(columns, r)) for r in rows]
                        else:
                            conn.commit()
                            data = {"affected": cur.rowcount}
                return CommandResult(
                    ok=True, output={"data": data},
                    execution_id=command.execution_id, connector_id=self.connector_id,
                    provider=self.provider, capability=capability,
                )
            except Exception as exc:
                logger.exception("db.query SQL execution failed")
                return CommandResult(
                    ok=False, error=f"Error ejecutando SQL: {exc}",
                    error_type="PROVIDER_ERROR",
                    execution_id=command.execution_id, connector_id=self.connector_id,
                    provider=self.provider, capability=capability,
                )
        elif capability == "db.record.create":
            values = params.get("values", {})
            res = db.table(params.get("table", "")).insert(values).execute()
            return CommandResult(ok=True, output={"data": res.data}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "db.record.read":
            filters = params.get("filters", {})
            select = params.get("select", "*")
            query = db.table(params.get("table", "")).select(select)
            for k, v in filters.items():
                query = query.eq(k, v)
            res = query.execute()
            return CommandResult(ok=True, output={"data": res.data}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "db.record.update":
            filters = params.get("filters", {})
            values = params.get("values", {})
            query = db.table(params.get("table", "")).update(values)
            for k, v in filters.items():
                query = query.eq(k, v)
            res = query.execute()
            return CommandResult(ok=True, output={"data": res.data}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "db.record.delete":
            filters = params.get("filters", {})
            query = db.table(params.get("table", "")).delete()
            for k, v in filters.items():
                query = query.eq(k, v)
            res = query.execute()
            return CommandResult(ok=True, output={"deleted": len(res.data) if res.data else 0}, connector_id=self.connector_id, provider=self.provider, capability=capability)
        elif capability == "db.schema.inspect":
            try:
                tables = db.table("information_schema.tables").select("table_name").execute()
                return CommandResult(ok=True, output={"tables": tables.data}, connector_id=self.connector_id, provider=self.provider, capability=capability)
            except Exception as exc:
                logger.error("Supabase schema inspect failed: %s", exc)
                return CommandResult(
                    ok=False, error=f"Error inspeccionando schema: {exc}",
                    error_type="PROVIDER_ERROR",
                    execution_id=command.execution_id, connector_id=self.connector_id,
                    provider=self.provider, capability=capability,
                )
        return CommandResult(ok=False, error=f"Unknown db capability: {capability}", error_type="UNSUPPORTED_OPERATION", connector_id=self.connector_id, provider=self.provider, capability=capability)
