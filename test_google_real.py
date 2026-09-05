"""Test de conexion real con Google APIs (Gmail, Drive, Calendar)."""
import os
import sys
import io

# Fix encoding para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))


def load_env():
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),
        os.path.join(os.getcwd(), '.env'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env.txt'),
        os.path.join(os.getcwd(), '.env.txt'),
    ]
    for env_path in candidates:
        if os.path.exists(env_path):
            with open(env_path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
            return env_path
    return None


loaded = load_env()

from agentic_os.connectors.adapters.google_auth import GoogleAuth, MissingCredentials
from agentic_os.connectors.adapters.google_gmail import GoogleGmailAdapter
from agentic_os.connectors.adapters.google_drive import GoogleDriveAdapter
from agentic_os.connectors.adapters.google_calendar import GoogleCalendarAdapter
from agentic_os.connectors.google import GoogleConnector
from agentic_os.infrastructure.config.settings import settings

def test_google_auth_connection():
    print("\n=== TEST 1: GoogleAuth - Carga de credenciales ===")
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    refresh_token = os.getenv('GOOGLE_REFRESH_TOKEN')
    print(f"CLIENT_ID: {client_id[:50]}..." if client_id else "CLIENT_ID: NO ENCONTRADO")
    print(f"CLIENT_SECRET: {client_secret[:20]}..." if client_secret else "CLIENT_SECRET: NO ENCONTRADO")
    print(f"REFRESH_TOKEN: {refresh_token[:30]}..." if refresh_token else "REFRESH_TOKEN: NO ENCONTRADO")
    if not all([client_id, client_secret, refresh_token]):
        print("[FAIL] FALTAN CREDENCIALES EN .env.txt")
        return False
    try:
        auth = GoogleAuth()
        token = auth.access_token()
        print(f"[PASS] GoogleAuth OK - Access Token obtenido: {token[:20]}...")
        return True
    except MissingCredentials as e:
        print(f"[FAIL] MissingCredentials: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error en GoogleAuth: {type(e).__name__}: {e}")


def test_gmail_connection():
    print("\n=== TEST 2: Gmail API - Listar mensajes ===")
    try:
        auth = GoogleAuth()
        gmail = GoogleGmailAdapter(auth)
        messages = gmail.list_messages(max_results=5)
        print(f"[PASS] Gmail API OK - Mensajes encontrados: {len(messages)}")
        for msg in messages[:3]:
            snippet = msg.get('snippet', 'N/A')[:50]
            print(f"  - ID: {msg.get('id', 'N/A')}, Snippet: {snippet}")
        gmail.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error en Gmail API: {type(e).__name__}: {e}")

def test_drive_connection():
    print("\n=== TEST 3: Google Drive API - Listar archivos ===")
    try:
        auth = GoogleAuth()
        drive = GoogleDriveAdapter(auth)
        files = drive.list_files()
        print(f"[PASS] Drive API OK - Archivos encontrados: {len(files)}")
        for f in files[:3]:
            print(f"  - {f.get('name', 'N/A')} (ID: {f.get('id', 'N/A')})")
        drive.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error en Drive API: {type(e).__name__}: {e}")
        return False


def test_calendar_connection():
    print("\n=== TEST 4: Google Calendar API - Listar eventos ===")
    try:
        auth = GoogleAuth()
        cal = GoogleCalendarAdapter(auth)
        events = cal.list_events(max_results=5)
        print(f"[PASS] Calendar API OK - Eventos encontrados: {len(events)}")
        for e in events[:3]:
            print(f"  - {e.get('title', 'N/A')}: {e.get('start', 'N/A')}")
        cal.close()
        return True
    except Exception as e:
        print(f"[FAIL] Error en Calendar API: {type(e).__name__}: {e}")
        return False


def test_google_connector():
    print("\n=== TEST 5: GoogleConnector - Conexion completa ===")
    try:
        conn = GoogleConnector()
        print(f"[PASS] GoogleConnector creado - Connected: {conn.connected}")
        print(f"  Capabilities: {conn.capabilities}")
        return conn.connected
    except Exception as e:
        print(f"[FAIL] Error en GoogleConnector: {type(e).__name__}: {e}")
        return False


def test_google_real_flag():
    print("\n=== TEST 6: Flag GOOGLE_REAL ===")
    print(f"GOOGLE_REAL: {settings.google_real}")
    print(f"GOOGLE_CLIENT_ID configurado: {bool(settings.google_client_id)}")
    print(f"GOOGLE_CLIENT_SECRET configurado: {bool(settings.google_client_secret)}")
    print(f"GOOGLE_REFRESH_TOKEN configurado: {bool(settings.google_refresh_token)}")
    if settings.google_real and settings.google_client_id:
        print("[PASS] Google Real ACTIVADO y credenciales presentes")
        return True
    else:
        print("[WARN] Google Real NO activo o faltan credenciales")
        return False

def main():
    print("=" * 60)
    print("TEST DE CONEXION REAL CON GOOGLE APIS")
    print("=" * 60)
    print(f"GOOGLE_REAL: {os.getenv('GOOGLE_REAL', 'NO CONFIGURADO')}")
    print(f"ENV: {os.getenv('ENV', 'NO CONFIGURADO')}")
    results = []
    results.append(("GoogleAuth", test_google_auth_connection()))
    results.append(("Gmail API", test_gmail_connection()))
    results.append(("Drive API", test_drive_connection()))
    results.append(("Calendar API", test_calendar_connection()))
    results.append(("GoogleConnector", test_google_connector()))
    results.append(("GOOGLE_REAL Flag", test_google_real_flag()))
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    passed = sum(1 for _, r in results if r)
    failed = sum(1 for _, r in results if not r)
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} - {name}")
    print(f"\nTotal: {passed} pasados, {failed} fallados")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
