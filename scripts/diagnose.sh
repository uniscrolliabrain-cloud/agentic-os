#!/usr/bin/env bash
# =============================================================================
# scripts/diagnose.sh — Diagnóstico rápido del entorno
# Ejecute: bash scripts/diagnose.sh
# =============================================================================
set -u
cd "$(dirname "$0")/.." || exit 1

echo "══════════════════════════════════════════"
echo "  Agentic OS — Self Diagnosis"
echo "══════════════════════════════════════════"
echo

echo "📦 Python: $(python --version 2>&1)"
echo "📦 Pip:    $(pip --version 2>&1)"
echo

echo "🔍 Imports del kernel:"
python -c "
from agentic_os.kernel.world import Event, EventLog, WorldState
from agentic_os.kernel.policy import PolicyEngine, Policy
from agentic_os.kernel.ontology import OntologyBundle
print('  ✓ kernel.world / policy / ontology')
" 2>&1 || echo "  ✗ kernel import falló"

echo
echo "🔍 Imports de orchestration:"
python -c "
from agentic_os.orchestration.pipelines import PIPELINES
from agentic_os.orchestration.pipelines.runner import PipelineRunner
print(f'  ✓ {len(PIPELINES)} pipelines registrados')
" 2>&1 || echo "  ✗ orchestration import falló"

echo
echo "🔍 Imports de interfaces:"
python -c "
from agentic_os.interfaces.api.rest import app
print('  ✓ FastAPI app cargada')
" 2>&1 || echo "  ✗ interfaces import falló"

echo
echo "🔍 Configuración:"
python -c "
from agentic_os.infrastructure.config.settings import settings
print(f'  ✓ settings cargados: tenant_id default = {settings.default_tenant_id}')
" 2>&1 || echo "  ✗ settings falló"

echo
echo "✅ Diagnóstico completado."
