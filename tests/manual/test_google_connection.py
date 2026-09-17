"""Test de conexión Google — verifica que las credenciales funcionan."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

print("=== Test de conexion Google ===")

# 1. Verificar credenciales en variables de entorno
client_id = os.environ.get("GOOGLE_CLIENT_ID")
refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN")
print(f"GOOGLE_CLIENT_ID (env): {'OK' if client_id else 'FALTA'}")
print(f"GOOGLE_REFRESH_TOKEN (env): {'OK' if refresh_token else 'FALTA'}")

# 2. Cargar Settings
from agentic_os.infrastructure.config.settings import settings
print(f"Settings.google_client_id: {'OK' if settings.google_client_id else 'FALTA'}")
print(f"Settings.google_refresh_token: {'OK' if settings.google_refresh_token else 'FALTA'}")

# 3. Probar GoogleAuth con detalle del error
try:
    from agentic_os.connectors.adapters.google_auth import GoogleAuth, MissingCredentials
    import httpx
    auth = GoogleAuth()
    cfg = auth._oauth_config()
    refresh_token = settings.google_refresh_token
    data = {
        "client_id": cfg["client_id"],
        "client_secret": cfg.get("client_secret", ""),
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    resp = httpx.post(cfg["token_url"], data=data, timeout=15)
    print(f"Status: {resp.status_code}")
    print(f"Respuesta: {resp.text[:500]}")
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        print(f"Token obtenido: {token[:20]}...")
        print("Google Auth: OK")
    elif resp.status_code == 401 and "invalid_client" in resp.text:
        print(
            "ACCION: el GOOGLE_CLIENT_SECRET no coincide con el GOOGLE_CLIENT_ID.\n"
            "  1. Ve a https://console.cloud.google.com/apis/credentials\n"
            "  2. Abre el OAuth 2.0 Client ID que corresponde a GOOGLE_CLIENT_ID\n"
            "  3. Copia el 'Client secret' actual (formato GOCSPX-...) y pégalo en .env\n"
            "  4. Si el secret se regeneró, el antiguo queda revocado: usa el nuevo"
        )
    else:
        print("Error en refresh token")
except MissingCredentials as e:
    print(f"Faltan credenciales: {e}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")