# Enterprise JWT Verifier para Agentic OS

1. Copia jwt_verifier.py a: src/agentic_os/infrastructure/auth/jwt_verifier.py
2. pip install "pyjwt[crypto]" httpx
3. Configura SUPABASE_URL en .env
4. Activa el custom_access_token_hook en Supabase (ver MINIPROMPT 3)

Uso en rest.py:
from ...infrastructure.auth.jwt_verifier import get_verifier
