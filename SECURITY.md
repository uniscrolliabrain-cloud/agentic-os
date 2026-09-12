# Política de seguridad

## Versiones soportadas

| Versión | Soportada |
|---------|-----------|
| 0.1.x   | ✅        |

## Reportar una vulnerabilidad

Si encuentras una vulnerabilidad de seguridad (SSRF, fuga de credenciales,
bypass de policy/tenancy, inyección en tools, etc.), **no abras un Issue público**.

Repórtala en privado a: `security@tu-dominio.com` (sustituye por tu email real,
o activa [GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories)
en Settings → Security → Advisories para reporte privado nativo de GitHub).

Incluye:
- Descripción del problema y componente afectado (kernel / connectors / policy / tenancy).
- Pasos para reproducir.
- Impacto potencial (ej. escalada entre tenants, fuga de OAuth tokens, etc.).

Nos comprometemos a confirmar recepción en un plazo razonable y a coordinar
la publicación de un fix antes de cualquier disclosure pública.

## Áreas de especial sensibilidad en este repo

- `src/agentic_os/connectors/auth/` — manejo de credenciales OAuth y tokens.
- `src/agentic_os/kernel/policy/` — motor de permisos y aprobación.
- `src/agentic_os/infrastructure/tenancy/` — aislamiento entre clientes.
- `.env` / `CredentialStore` — nunca deben commitearse (ver `.gitignore`).
