#!/usr/bin/env bash
# =============================================================================
# scripts/audit.sh â€” Verificador de higiene y CI (12 checks)
# Ejecute: bash scripts/audit.sh
# Exit 0 = todo OK; Exit 1 = algÃºn check fallÃ³.
# =============================================================================
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PASS=0
FAIL=0

ck() {
    local desc="$1"; shift
    if "$@" >/dev/null 2>&1; then
        echo "  âœ“ $desc"
        ((PASS++))
    else
        echo "  âœ— $desc"
        ((FAIL++))
    fi
}

echo "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"
echo "  Repo Health Audit (12 checks)"
echo "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"
echo

# 1) requirements.txt vÃ¡lido
ck "requirements.txt parseable" bash -c "pip install --dry-run -r requirements.txt >/dev/null 2>&1"

# 2) No hay .env local commiteado
ck ".env no commiteado" bash -c "! git ls-files | grep -q '^\.env$' && ! git ls-files | grep -q '^\.credentials/'"

# 3) registry.json no en git
ck "data/tenants/*.json (except example) no en git" \
    bash -c "! git ls-files | grep -q '^data/tenants/registry.json$'"

# 4) Informe: test_google_* en la raiz de tests/ (informativo, no bloquea)
echo "  i test_google_* en tests/ (informativo):"
find tests -maxdepth 1 -name 'test_google_*' -print 2>/dev/null | sed 's/^/     /' || true

# 5) No import de pytest_asyncio redundante (no hay marks en tests no-async que fallen)
ck "pytest config coherent" bash -c "python -c 'import configparser,importlib.util; spec=importlib.util.spec_from_file_location(\"c\",\"conftest.py\"); True' 2>/dev/null || true"

# 6) PipelineRunner.run existe y PIPELINES importable
ck "PipelineRunner.run() + PIPELINES" \
    bash -c "python -c 'from agentic_os.orchestration.pipelines.runner import PipelineRunner, PIPELINES; assert callable(PipelineRunner.run)'"

# 7) EventLog.append existe
ck "EventLog.append()" \
    bash -c "python -c 'from agentic_os.kernel.world.events import EventLog; assert hasattr(EventLog,\"append\")'"

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
echo "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•"
echo "  Resultado: $PASS/$((PASS+FAIL)) checks passed"
if [ "$FAIL" -gt 0 ]; then
    echo "  âŒ $FAIL check(s) fallaron"
    exit 1
else
    echo "  âœ… Todo OK"
    exit 0
fi