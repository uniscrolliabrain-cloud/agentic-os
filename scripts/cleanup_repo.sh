#!/usr/bin/env bash
# =============================================================================
# scripts/cleanup_repo.sh — Higiene del repo (CHUNK 2)
#
# Limpia artefactos generados, datos sensibles y mezcla la higiene del repo.
# No requiere argumentos. Es idempotente.
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "🔧 Repo hygiene: $ROOT"
echo

# --- 1. Mover export/ → .scratch/ ---
if [ -d "export" ]; then
    mkdir -p .scratch
    mv export .scratch/export
    echo "  ✓ export/ → .scratch/export/"
fi

# --- 2. Mover archive/ → docs/archive/ ---
if [ -d "archive" ]; then
    mkdir -p docs/archive
    mv archive/* docs/archive/ 2>/dev/null || true
    rmdir archive 2>/dev/null || rm -rf archive
    echo "  ✓ archive/ → docs/archive/"
fi

# --- 3. Mover test_google_*.py → tests/manual/ ---
mkdir -p tests/manual
MOVED=0
for f in test_google_*.py; do
    [ -f "$f" ] || continue
    mv "$f" tests/manual/
    echo "  ✓ $f → tests/manual/"
    ((MOVED++))
done
if [ "$MOVED" -eq 0 ] && ls test_google_*.py 2>/dev/null; then
    : # nada que mover
fi

# --- 4. Sanitizar registry.json → example ---
if [ -f "data/tenants/registry.json" ]; then
    cp data/tenants/registry.json data/tenants/registry.local.bak.json
    rm -f data/tenants/registry.json
    echo "  ✓ data/tenants/registry.json removido (se mantiene registry.example.json)"
    echo "    (backup local: data/tenants/registry.local.bak.json — agregue .bak.json al .gitignore)"
fi

# --- 5. Limpiar .env.local y secrets ---
rm -f .env.local .env.*.local 2>/dev/null || true
echo "  ✓ .env.local limpiado"

# --- 6. Limpiar caches y pycache ---
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
echo "  ✓ caches limpiados"

# --- 7. Escribir registry.example.json si no existe ---
if [ ! -f "data/tenants/registry.example.json" ]; then
    cat > data/tenants/registry.example.json << 'JSON'
[
  {
    "id": "00000000-0000-0000-0000-000000000001",
    "slug": "acme",
    "config": {
      "name": "ACME Corp",
      "domain": "generic",
      "enabled_capabilities": ["lead_capture", "email_draft"]
    },
    "created_at": "2025-01-01T00:00:00.000000Z"
  }
]
JSON
    echo "  ✓ registry.example.json creado"
fi

echo
echo "✅ Higiene completada. Use 'git status' para revisar."
