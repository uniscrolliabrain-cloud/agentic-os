# Plantilla: Creación de Skills Completas

## Instrucciones para el Colaborador

Usa esta plantilla para crear skills de captación de leads, gestión de clientes y ventas. Cada skill debe seguir la arquitectura híbrida (Prompt Skill + Execution Skill) establecida en el PR #2.

---

## Estructura de Archivos por Skill

```
src/agentic_os/cognition/skills/
├── SKILLS.md          # Registro central (auto-generado)
├── lead_capture/      # Carpeta de la skill
│   ├── SKILL.md       # Prompt Skill (frontmatter YAML + instrucciones)
│   ├── models.py      # Execution Skill (modelos Pydantic)
│   ├── executor.py    # Lógica de ejecución
│   └── tests/         # Tests de la skill
│       ├── test_models.py
│       ├── test_executor.py
│       └── test_api.py
```

---

## 1. SKILL.md (Prompt Skill)

```markdown
---
name: lead_capture_qualification
version: 1.0.0
description: Califica leads entrantes usando framework BANT (Budget, Authority, Need, Timeline)
author: [nombre]
tenant_isolation: true
required_capabilities:
  - lead.read
  - lead.write
forbidden_tools:
  - gmail_send
  - slack_send
---

# Lead Capture: Calificación BANT

## Propósito
Califica leads entrantes automáticamente usando el framework BANT para priorizar oportunidades de venta.

## Cuándo usar esta skill
- Cuando llega un nuevo lead desde un formulario web
- Cuando se recibe un email solicitando información de productos/servicios
- Cuando el usuario pide "calificar lead" o "qualify lead"

## Instrucciones para el LLM

### 1. Extraer información del lead
Analiza el mensaje/email/formulario y extrae:
- **Budget**: ¿Tiene presupuesto? (alto/medio/bajo/unknown)
- **Authority**: ¿Es el decisor? (decisor/influenciador/unknown)
- **Need**: ¿Necesidad clara? (urgente/potencial/ninguna)
- **Timeline**: ¿Cuándo necesita la solución? (inmediato/3meses/6meses/indefinido)

### 2. Calcular score BANT
Asigna puntos según:
- Budget alto=3, medio=2, bajo=1, unknown=0
- Authority decisor=3, influenciador=2, unknown=0
- Need urgente=3, potencial=2, ninguna=0
- Timeline inmediato=3, 3meses=2, 6meses=1, indefinido=0

### 3. Clasificar lead
- **Hot lead** (score 9-12): Contactar inmediatamente
- **Warm lead** (score 5-8): Seguimiento en 48h
- **Cold lead** (score 0-4): Nutrir con contenido

### 4. Generar respuesta
Crea un email de respuesta personalizado según la clasificación.

## Restricciones
- NUNCA enviar emails sin aprobación humana (forbidden_tools)
- NUNCA acceder a datos de otros tenants
- SIEMPRE registrar la calificación en el sistema

## Output esperado
```json
{
  "lead_id": "string",
  "bant_scores": {
    "budget": "alto|medio|bajo|unknown",
    "authority": "decisor|influenciador|unknown",
    "need": "urgente|potencial|ninguna",
    "timeline": "inmediato|3meses|6meses|indefinido"
  },
  "total_score": 0-12,
  "classification": "hot|warm|cold",
  "next_action": "string"
}
```
```

---

## 2. models.py (Execution Skill)

```python
"""Execution Skill: Calificación BANT de leads."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BANTLevel(str, Enum):
    """Niveles de cada dimensión BANT."""
    ALTO = "alto"
    MEDIO = "medio"
    BAJO = "bajo"
    UNKNOWN = "unknown"


class AuthorityLevel(str, Enum):
    """Nivel de autoridad del contacto."""
    DECISOR = "decisor"
    INFLUENCIADOR = "influenciador"
    UNKNOWN = "unknown"


class NeedLevel(str, Enum):
    """Nivel de necesidad."""
    URGENTE = "urgente"
    POTENCIAL = "potencial"
    NINGUNA = "ninguna"


class TimelineLevel(str, Enum):
    """Timeline de decisión."""
    INMEDIATO = "inmediato"
    TRES_MESES = "3meses"
    SEIS_MESES = "6meses"
    INDEFINIDO = "indefinido"


class LeadClassification(str, Enum):
    """Clasificación final del lead."""
    HOT = "hot"
    WARM = "warm"

---

## 3. executor.py (Lógica de Ejecución)

```python
"""Ejecutor de la skill de calificación BANT."""

from __future__ import annotations

import logging
from typing import Optional

from agentic_os.kernel.policy.engine import PolicyEngine
from agentic_os.kernel.policy.evaluator import Decision

from .models import (
    BANTScores,
    BANTLevel,
    AuthorityLevel,
    NeedLevel,
    TimelineLevel,
    LeadClassification,
    LeadQualification,
    LeadCaptureConfig,
)

logger = logging.getLogger(__name__)


class LeadCaptureExecutor:
    """Ejecutor de la skill de captación de leads."""

    def __init__(
        self,
        policy_engine: Optional[PolicyEngine] = None,
        config: Optional[LeadCaptureConfig] = None,
    ):
        self.policy = policy_engine or PolicyEngine()
        self.config = config or LeadCaptureConfig()

    def _score_budget(self, level: BANTLevel) -> int:
        """Calcula score de budget."""
        scores = {
            BANTLevel.ALTO: 3,
            BANTLevel.MEDIO: 2,
            BANTLevel.BAJO: 1,
            BANTLevel.UNKNOWN: 0,
        }
        return scores.get(level, 0)

    def _score_authority(self, level: AuthorityLevel) -> int:
        """Calcula score de autoridad."""
        scores = {
            AuthorityLevel.DECISOR: 3,
            AuthorityLevel.INFLUENCIADOR: 2,
            AuthorityLevel.UNKNOWN: 0,
        }
        return scores.get(level, 0)

    def _score_need(self, level: NeedLevel) -> int:
        """Calcula score de necesidad."""
        scores = {
            NeedLevel.URGENTE: 3,
            NeedLevel.POTENCIAL: 2,
            NeedLevel.NINGUNA: 0,
        }
        return scores.get(level, 0)

    def _score_timeline(self, level: TimelineLevel) -> int:
        """Calcula score de timeline."""
        scores = {
            TimelineLevel.INMEDIATO: 3,
            TimelineLevel.TRES_MESES: 2,
            TimelineLevel.SEIS_MESES: 1,
            TimelineLevel.INDEFINIDO: 0,
        }
        return scores.get(level, 0)

    def calculate_score(self, scores: BANTScores) -> int:
        """Calcula score total BANT."""
        return (
            self._score_budget(scores.budget)
            + self._score_authority(scores.authority)
            + self._score_need(scores.need)
            + self._score_timeline(scores.timeline)
        )

    def classify_lead(self, total_score: int) -> LeadClassification:
        """Clifica lead según score total."""
        if total_score >= self.config.hot_threshold:
            return LeadClassification.HOT
        elif total_score >= self.config.warm_threshold:
            return LeadClassification.WARM
        return LeadClassification.COLD

    def get_next_action(self, classification: LeadClassification) -> str:
        """Determina siguiente acción según clasificación."""
        actions = {
            LeadClassification.HOT: self.config.hot_action,
            LeadClassification.WARM: self.config.warm_action,
            LeadClassification.COLD: self.config.cold_action,
        }
        return actions.get(classification, "Revisar manualmente")

    def qualify_lead(
        self,
        lead_id: str,
        tenant_id: str,
        scores: BANTScores,
        roles: Optional[list[str]] = None,
    ) -> LeadQualification:
        """
        Califica un lead usando framework BANT.

        Args:
            lead_id: ID único del lead
            tenant_id: ID del tenant (aislamiento)
            scores: Scores BANT del lead
            roles: Roles del usuario que ejecuta

        Returns:
            LeadQualification con clasificación y siguiente acción

        Raises:
            PermissionError: Si el PolicyEngine deniega la operación
            ValueError: Si los datos de entrada son inválidos
        """
        # Verificar permisos via PolicyEngine
        decision = self.policy.decide(
            tenant_id=tenant_id,
            capability="lead.write",
            roles=roles or ["operator"],
        )

        if decision == Decision.DENY:
            raise PermissionError(
                f"PolicyEngine denegó lead.write para tenant {tenant_id}"
            )

        if decision == Decision.REQUIRE_APPROVAL:
            raise PermissionError(

---

## 4. Tests (test_executor.py)

```python
"""Tests para LeadCaptureExecutor."""

import pytest
from unittest.mock import MagicMock

from agentic_os.cognition.skills.lead_capture.executor import LeadCaptureExecutor
from agentic_os.cognition.skills.lead_capture.models import (
    BANTScores,
    BANTLevel,
    AuthorityLevel,
    NeedLevel,
    TimelineLevel,
    LeadClassification,
    LeadCaptureConfig,
)
from agentic_os.kernel.policy.engine import PolicyEngine
from agentic_os.kernel.policy.evaluator import Decision


class TestLeadCaptureExecutor:
    """Tests de la skill de captación."""

    def setup_method(self):
        """Setup para cada test."""
        self.policy = MagicMock(spec=PolicyEngine)
        self.policy.decide.return_value = Decision.ALLOW
        self.executor = LeadCaptureExecutor(policy_engine=self.policy)

    def test_calculate_score_hot_lead(self):
        """Test score para lead caliente."""
        scores = BANTScores(
            budget=BANTLevel.ALTO,
            authority=AuthorityLevel.DECISOR,
            need=NeedLevel.URGENTE,
            timeline=TimelineLevel.INMEDIATO,
        )
        assert self.executor.calculate_score(scores) == 12

    def test_calculate_score_cold_lead(self):
        """Test score para lead frío."""
        scores = BANTScores(
            budget=BANTLevel.UNKNOWN,
            authority=AuthorityLevel.UNKNOWN,
            need=NeedLevel.NINGUNA,
            timeline=TimelineLevel.INDEFINIDO,
        )
        assert self.executor.calculate_score(scores) == 0

    def test_classify_hot_lead(self):
        """Test clasificación hot lead."""
        assert self.executor.classify_lead(9) == LeadClassification.HOT
        assert self.executor.classify_lead(12) == LeadClassification.HOT

    def test_classify_warm_lead(self):
        """Test clasificación warm lead."""
        assert self.executor.classify_lead(5) == LeadClassification.WARM
        assert self.executor.classify_lead(8) == LeadClassification.WARM

    def test_classify_cold_lead(self):
        """Test clasificación cold lead."""
        assert self.executor.classify_lead(0) == LeadClassification.COLD
        assert self.executor.classify_lead(4) == LeadClassification.COLD

    def test_qualify_lead_success(self):
        """Test calificación exitosa."""
        scores = BANTScores(
            budget=BANTLevel.ALTO,
            authority=AuthorityLevel.DECISOR,
            need=NeedLevel.URGENTE,
            timeline=TimelineLevel.INMEDIATO,
        )

        result = self.executor.qualify_lead(
            lead_id="lead-123",
            tenant_id="tenant-1",
            scores=scores,
        )

        assert result.lead_id == "lead-123"
        assert result.tenant_id == "tenant-1"
        assert result.total_score == 12
        assert result.classification == LeadClassification.HOT
        assert result.confidence == 1.0

    def test_qualify_lead_policy_deny(self):
        """Test que PolicyEngine.deny aborta la operación."""
        self.policy.decide.return_value = Decision.DENY

        scores = BANTScores()

        with pytest.raises(PermissionError, match="PolicyEngine denegó"):
            self.executor.qualify_lead(
                lead_id="lead-123",
                tenant_id="tenant-1",
                scores=scores,
            )

    def test_qualify_lead_requires_approval(self):
        """Test que REQUIRE_APPROVAL aborta la operación."""

---

## 5. API Endpoint (test_api.py)

```python
"""Tests de API para skill de captación."""

import pytest
from fastapi.testclient import TestClient


class TestLeadCaptureAPI:
    """Tests de endpoints de la skill."""

    def test_install_skill_requires_auth(self, client: TestClient):
        """Test que install requiere API key."""
        response = client.post(
            "/api/skills/install",
            json={"skill_name": "lead_capture_qualification"},
        )
        assert response.status_code == 401

    def test_install_skill_requires_tenant(self, client: TestClient):
        """Test que install requiere tenant."""
        response = client.post(
            "/api/skills/install",
            json={"skill_name": "lead_capture_qualification"},
            headers={"X-Api-Key": "test-key"},
        )
        assert response.status_code == 404

    def test_run_skill_tenant_isolation(self, client: TestClient):
        """Test aislamiento de tenant en run."""
        # Tenant 1 instala skill
        client.post(
            "/api/skills/install",
            json={"skill_name": "lead_capture_qualification"},
            headers={
                "X-Api-Key": "key-1",
                "X-Tenant-Id": "tenant-1",
            },
        )

        # Tenant 2 NO puede ejecutar skill de tenant-1
        response = client.post(
            "/api/skills/run",
            json={
                "skill_name": "lead_capture_qualification",
                "lead_id": "lead-123",
            },
            headers={
                "X-Api-Key": "key-2",
                "X-Tenant-Id": "tenant-2",
            },
        )
        assert response.status_code == 404  # Skill no encontrado para tenant-2
```

---

## Lista de Skills a Crear

### Captación de Leads
| Skill | Descripción | Prioridad |
|-------|-------------|-----------|
| `lead_capture_qualification` | Calificación BANT | 🔴 Alta |
| `lead_capture_enrichment` | Enriquecimiento de datos | 🔴 Alta |
| `lead_capture_scoring` | Score predictivo | 🟡 Media |

### Gestión de Clientes
| Skill | Descripción | Prioridad |
|-------|-------------|-----------|
| `client_onboarding` | Onboarding automatizado | 🔴 Alta |
| `client_health_score` | Health score de clientes | 🟡 Media |
| `client_retention` | Detección de churn | 🟡 Media |

### Ventas
| Skill | Descripción | Prioridad |
|-------|-------------|-----------|
| `sales_proposal_generation` | Generación de propuestas | 🔴 Alta |
| `sales_follow_up` | Seguimiento de oportunidades | 🟡 Media |
| `sales_forecasting` | Predicción de ventas | 🟢 Baja |

---

## Checklist por Skill

- [ ] SKILL.md con frontmatter YAML completo
- [ ] models.py con modelos Pydantic frozen
- [ ] executor.py con integración PolicyEngine
- [ ] Tests unitarios (executor + models)
- [ ] Tests de API (multi-tenant)
- [ ] Sin forbidden_tools (gmail_send, slack_send)
- [ ] Aislamiento tenant verificado
- [ ] Documentación en SKILL.md

---

*Plantilla v1.0 — Agentic OS Skills Architecture*

        self.policy.decide.return_value = Decision.REQUIRE_APPROVAL

        scores = BANTScores()

        with pytest.raises(PermissionError, match="aprobación humana"):
            self.executor.qualify_lead(
                lead_id="lead-123",
                tenant_id="tenant-1",
                scores=scores,
            )

    def test_tenant_isolation(self):
        """Test que cada tenant solo ve sus propios leads."""
        scores = BANTScores(budget=BANTLevel.ALTO)

        result = self.executor.qualify_lead(
            lead_id="lead-123",
            tenant_id="tenant-1",
            scores=scores,
        )

        # Verificar que el tenant_id se propaga correctamente
        assert result.tenant_id == "tenant-1"
```

                "Esta operación requiere aprobación humana"
            )

        # Calcular score y clasificación
        total_score = self.calculate_score(scores)
        classification = self.classify_lead(total_score)
        next_action = self.get_next_action(classification)

        # Calcular confianza basada en datos disponibles
        confidence = self._calculate_confidence(scores)

        qualification = LeadQualification(
            lead_id=lead_id,
            tenant_id=tenant_id,
            bant_scores=scores,
            total_score=total_score,
            classification=classification,
            next_action=next_action,
            confidence=confidence,
        )

        logger.info(
            "Lead %s calificado: %s (score=%d, confidence=%.2f)",
            lead_id,
            classification.value,
            total_score,
            confidence,
        )

        return qualification

    def _calculate_confidence(self, scores: BANTScores) -> float:
        """Calcula confianza basada en datos disponibles."""
        unknown_count = sum([
            scores.budget == BANTLevel.UNKNOWN,
            scores.authority == AuthorityLevel.UNKNOWN,
            scores.need == NeedLevel.NINGUNA,
            scores.timeline == TimelineLevel.INDEFINIDO,
        ])
        # Menos unknowns = más confianza
        return round(1.0 - (unknown_count * 0.25), 2)
```

    COLD = "cold"


class BANTScores(BaseModel):
    """Scores BANT individuales."""
    model_config = ConfigDict(frozen=True)

    budget: BANTLevel = BANTLevel.UNKNOWN
    authority: AuthorityLevel = AuthorityLevel.UNKNOWN
    need: NeedLevel = NeedLevel.NINGUNA
    timeline: TimelineLevel = TimelineLevel.INDEFINIDO


class LeadQualification(BaseModel):
    """Resultado de calificación de un lead."""
    model_config = ConfigDict(frozen=True)

    lead_id: str = Field(..., min_length=1)
    tenant_id: str = Field(..., min_length=1)
    bant_scores: BANTScores
    total_score: int = Field(ge=0, le=12)
    classification: LeadClassification
    next_action: str = Field(..., min_length=1)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)


class LeadCaptureConfig(BaseModel):
    """Configuración de la skill de captación."""
    model_config = ConfigDict(frozen=True)

    # Scores máximos por dimensión
    max_budget_score: int = 3
    max_authority_score: int = 3
    max_need_score: int = 3
    max_timeline_score: int = 3

    # Umbrales de clasificación
    hot_threshold: int = 9
    warm_threshold: int = 5

    # Acciones por clasificación
    hot_action: str = "Contactar inmediatamente (teléfono)"
    warm_action: str = "Seguimiento en 48h (email)"
    cold_action: str = "Nutrir con contenido (newsletter)"
```
