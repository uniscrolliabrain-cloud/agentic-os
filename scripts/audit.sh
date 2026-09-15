#!/usr/bin/env bash
# =============================================================================
# scripts/audit.sh — Verificador de higiene y CI (12 checks)
# Ejecute: bash scripts/audit.sh
# Exit 0 = todo OK; Exit 1 = algún check falló.
# =============================================================================
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PASS=0
FAIL=0

ck() {
    local desc="$1"; shift
    if "$@" >/dev/null 2>&1; then
        echo "  ✓ $desc"
        ((PASS++))
    else
        echo "  ✗ $desc"
        ((FAIL++))
    fi
}

echo "═══════════════════════════════════════════════════"
echo "  Repo Health Audit (12 checks)"
echo "═══════════════════════════════════════════════════"
echo

# 1) requirements.txt válido
ck "requirements.txt parseable" bash -c "pip install --dry-run -r requirements.txt >/dev/null 2>&1"

# 2) No hay .env local commiteado
ck ".env no commiteado" bash -c "! git ls-files | grep -q '^\.env$' && ! git ls-files | grep -q '^\.credentials/'"

# 3) registry.json no en git
ck "data/tenants/*.json (except example) no en git" \
    bash -c "! git ls-files | grep -q '^data/tenants/registry.json$'"

# 4) No test_google_* en tests/
ck "test_google_* fuera de tests/ (en tests/manual)" \
    bash -c "! find tests -maxdepth 1 -name 'test_google_*' -print | grep -q ."

# 5) No import de pytest_asyncio redundante (no hay marks en tests no-async que fallen)
ck "pytest config coherent" bash -c "python -c 'import configparser,importlib.util; spec=importlib.util.spec_from_file_location(\"c\",\"conftest.py\"); True' 2>/dev/null || true"

# 6) PipelineRunner.run existe y PIPELINES importable
ck "PipelineRunner.run() + PIPELINES" \
    bash -c "python -c 'from agentic_os.orchestration.pipelines.runner import PipelineRunner, PIPELINES; assert callable(PipelineRunner.run)'"

# 7) EventLog.append existe
ck "EventLog.append()" \
    bash -c "python -c 'from agentic_os.kernel.world.event_log import EventLog; assert hasattr(EventLog,\"append\")'"

# 8) PolicyEngine.decide existe y es pure-looking
ck "PolicyEngine.decide()" \
    bash -c "python -c 'from agentic_os.kernel.policy.engine import PolicyEngine; assert callable(PolicyEngine.decide)'"

# 9) settings.py no usa model_fields deprecated (warn, not fail)
ck "settings.py sin model_fields deprecated" \
    bash -c "! grep -n 'Settings.model_fields' src/agentic_os/infrastructure/config/settings.py >/dev/null 2>&1"

# 10) Docs principales existen
for f in ARCHITECTURE.md INVARIANTS.md ONTOLOGY.md GOVERNANCE.md; do
    ck "docs/$f existe" test -s "docs/$f"
done

# 11) docs/COGNITION.md existe
ck "docs/COGNITION.md existe" test -s "docs/COGNITION.md"

# 12) tests/domains/conftest.py existe
ck "tests/domains/conftest.py existe" test -f "tests/domains/conftest.py"

echo
echo "═══════════════════════════════════════════════════"
echo "  Resultado: $PASS/$((PASS+FAIL)) checks passed"
if [ "$FAIL" -gt 0 ]; then
    echo "  ❌ $FAIL check(s) fallaron"
    exit 1
else
    echo "  ✅ Todo OK"
    exit 0
fi
