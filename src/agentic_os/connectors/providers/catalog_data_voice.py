"""Catálogo de providers de datos, voz, firma y project management."""

from typing import Any, Dict

PROVIDER_SPECS_DATA_VOICE: Dict[str, Dict[str, Any]] = {
    "elevenlabs": {
        "connector_id": "elevenlabs", "provider": "ElevenLabs", "auth_type": "bearer",
        "caps": ["media.audio.generate", "media.voice.generate", "media.audio.transcribe"],
        "token_env": "ELEVENLABS_API_KEY",
    },
    "docusign": {
        "connector_id": "docusign", "provider": "DocuSign", "auth_type": "oauth2",
        "caps": ["document.signature.request", "document.signature.read",
                 "document.signature.status", "document.signature.download"],
        "oauth": {"client_id_env": "DOCUSIGN_INTEGRATION_KEY",
                  "client_secret_env": "DOCUSIGN_SECRET_KEY",
                  "authorization_url": "https://account.docusign.com/oauth/auth",
                  "token_url": "https://account.docusign.com/oauth/token"},
    },
    "storage_s3": {
        "connector_id": "storage_s3", "provider": "AWS S3", "auth_type": "bearer",
        "caps": ["storage.file.upload", "storage.file.download", "storage.file.read",
                 "storage.file.create", "storage.file.delete", "storage.file.move",
                 "storage.file.copy", "storage.file.search"],
        "extra_env": ["AWS_REGION"],
        "token_env": "AWS_SECRET_ACCESS_KEY",
        "extra_auth_env": ["AWS_ACCESS_KEY_ID"],
    },
    "supabase_storage": {
        "connector_id": "supabase_storage", "provider": "Supabase Storage", "auth_type": "bearer",
        "caps": ["storage.file.upload", "storage.file.download", "storage.file.read",
                 "storage.file.delete", "storage.folder.create"],
        "extra_env": ["SUPABASE_URL"],
        "token_env": "SUPABASE_SERVICE_ROLE_KEY",
    },
    "postgres": {
        "connector_id": "postgres", "provider": "PostgreSQL", "auth_type": "connection_string",
        "caps": ["database.schema.inspect", "database.query",
                 "database.record.create", "database.record.read",
                 "database.record.update", "database.record.delete"],
        "token_env": "POSTGRES_CONNECTION_STRING",
        "note": "Solo queries parametrizadas según policy del workspace.",
    },
    "redis": {
        "connector_id": "redis", "provider": "Redis", "auth_type": "connection_string",
        "caps": ["database.record.read", "database.record.create", "database.record.delete"],
        "token_env": "REDIS_URL",
    },
    "mongodb": {
        "connector_id": "mongodb", "provider": "MongoDB", "auth_type": "connection_string",
        "caps": ["database.schema.inspect", "database.record.create", "database.record.read",
                 "database.record.update", "database.record.delete"],
        "token_env": "MONGODB_URI",
    },
    "linear": {
        "connector_id": "linear", "provider": "Linear", "auth_type": "bearer",
        "caps": ["project.project.read", "project.task.create", "project.task.read",
                 "project.task.update", "project.task.assign", "project.task.complete",
                 "project.issue.create", "project.issue.update"],
        "token_env": "LINEAR_API_KEY",
    },
    "clickup": {
        "connector_id": "clickup", "provider": "ClickUp", "auth_type": "bearer",
        "caps": ["project.project.read", "project.task.create", "project.task.read",
                 "project.task.update", "project.task.assign", "project.task.complete"],
        "token_env": "CLICKUP_API_TOKEN",
    },
    "asana": {
        "connector_id": "asana", "provider": "Asana", "auth_type": "bearer",
        "caps": ["project.project.read", "project.project.update",
                 "project.task.create", "project.task.read", "project.task.update",
                 "project.task.complete"],
        "token_env": "ASANA_ACCESS_TOKEN",
    },
    "jira": {
        "connector_id": "jira", "provider": "Jira", "auth_type": "basic",
        "caps": ["project.project.read", "project.issue.create", "project.issue.update",
                 "project.task.create", "project.task.read"],
        "extra_env": ["JIRA_SITE_URL", "JIRA_EMAIL"],
        "token_env": "JIRA_API_TOKEN",
    },
    "vapi": {
        "connector_id": "vapi", "provider": "Vapi", "auth_type": "bearer",
        "caps": ["voice.call.create", "voice.call.read", "voice.call.end",
                 "voice.call.transcribe", "voice.call.analyze"],
        "token_env": "VAPI_API_KEY",
    },
    "retell": {
        "connector_id": "retell", "provider": "Retell AI", "auth_type": "bearer",
        "caps": ["voice.call.create", "voice.call.read", "voice.call.end",
                 "voice.call.analyze"],
        "token_env": "RETELL_API_KEY",
    },
}