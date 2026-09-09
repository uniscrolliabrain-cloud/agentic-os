"""TAREA 2 - Discovery/difusión progresiva de Prompt Skills en el Proposer."""

import pytest

import agentic_os.cognition.skills.library as lib
from agentic_os.cognition.beliefs.belief import Belief
from agentic_os.cognition.memory.retrieval import retrieve_prompt_skills
from agentic_os.cognition.memory.store import MemoryItem, MemoryStore
from agentic_os.cognition.reasoning.proposer import LLMProposer, IntentProposalResponse
from agentic_os.interfaces.llm.prompts import build_intent_proposal_prompt, format_skills
from agentic_os.interfaces.llm.provider import MockLLMProvider


def _skill_item(name, tenant_id, pipeline_id, content, n=1):
    return MemoryItem(
        id=f"skill:{name}:prompt",
        content=content,
        metadata={
            "name": name,
            "tenant_id": tenant_id,
            "version": "1.0.0",
            "pipeline_id": pipeline_id,
            "content_md5": f"hash-{name}-{n}",
        },
    )


def test_retrieve_prompt_skills_aisla_por_tenant_y_tope_k():
    store = MemoryStore()
    store.put(_skill_item("a", "tenant-a", "inbox_zero", "leer inbox y clasificar"))
    store.put(_skill_item("b", "tenant-a", "schedule_meeting", "leer inbox calendario"))
    store.put(_skill_item("c", "tenant-a", "scrape_web", "inbox documentar"))
    store.put(_skill_item("d", "tenant-a", "slack_respond", "solo slack"))
    # Skill de otro tenant: NUNCA debe filtrarse aunque tenga mayor coincidencia.
    store.put(_skill_item("x", "tenant-b", "inbox_zero", "leer inbox y clasificar"))

    results = retrieve_prompt_skills(store, "leer inbox", tenant_id="tenant-a", k=3)
    assert len(results) == 3
    assert all(item.metadata["tenant_id"] == "tenant-a" for item, _ in results)
    # Orden determinista por magnetismo: el que más coincide primero.
    top_score = results[0][1]
    assert all(score <= top_score for _, score in results)


def test_proposer_inyecta_skill_beliefs_y_respeta_capacidad_miller():
    store = MemoryStore()
    for i in range(5):  # 5 skills instaladas
        store.put(
            _skill_item(f"sk{i}", "tenant-a", "inbox_zero",
                        f"instruccion consultiva skill numero {i}: procesa el inbox")
        )
    wm_beliefs = [
        Belief(kind="context", content={"paciente": f"P{i}"})
        for i in range(6)  # 6 creencias previas: cupo 7 - 6 = 1 skill cabe
    ]
    provider = MockLLMProvider(
        structured_response=IntentProposalResponse(intents=[])
    )
    proposer = LLMProposer(provider=provider, skill_store=store, tenant_id="tenant-a")

    proposer.propose(beliefs=wm_beliefs, goal="procesar el inbox del paciente")

    # Solo 1 skill entró (7 - 6 creencias previas = cupo restante).
    assert len(proposer.last_skill_beliefs) == 1
    belief = proposer.last_skill_beliefs[0]
    assert belief.kind == "skill_available"
    assert belief.content["pipeline_id"] == "inbox_zero"
    # Confianza proporcional al magnetismo.
    assert 0.0 < belief.confidence <= 1.0
    # El working memory no se satura (nº beliefs <= capacity)
    assert "Current Beliefs" in (provider.last_prompt or "")
    assert "skill_available" in (provider.last_prompt or "")


def test_proposer_sin_credencias_previas_inyecta_top3():
    store = MemoryStore()
    store.put(_skill_item("inbox", "tenant-a", "inbox_zero", "instrucciones inbox"))
    store.put(_skill_item("meet", "tenant-a", "schedule_meeting", "instrucciones reunion"))
    store.put(_skill_item("scrape", "tenant-a", "scrape_web", "instrucciones scraping"))
    provider = MockLLMProvider(
        structured_response=IntentProposalResponse(intents=[])
    )
    proposer = LLMProposer(provider=provider, skill_store=store, tenant_id="tenant-a")

    proposer.propose(beliefs=[], goal="organizar inbox agendar reunion y scraping")

    assert len(proposer.last_skill_beliefs) == 3
    # El contenido de las instrucciones de los top-3 está en el prompt.
    assert "instrucciones inbox" in (provider.last_prompt or "")
    assert "instrucciones reunion" in (provider.last_prompt or "")
    assert "instrucciones scraping" in (provider.last_prompt or "")


def test_proposer_ignora_skills_de_otro_tenant():
    store = MemoryStore()
    store.put(_skill_item("inboxA", "tenant-a", "inbox_zero", "instrucciones inbox A"))
    store.put(_skill_item("inboxB", "tenant-b", "inbox_zero", "instrucciones inbox B"))
    provider = MockLLMProvider(
        structured_response=IntentProposalResponse(intents=[])
    )
    proposer = LLMProposer(provider=provider, skill_store=store, tenant_id="tenant-a")

    proposer.propose(beliefs=[], goal="leer el inbox")

    assert proposer.last_skill_beliefs  # al menos uno para el tenant correcto
    assert all(
        b.content["skill_name"] == "inboxA"
        for b in proposer.last_skill_beliefs
    )


def test_prompt_skills_seccion_consultiva_y_back_compat():
    # Sin skills -> prompt idéntico a la versión previa (back-compat).
    p0 = build_intent_proposal_prompt(goal="g", beliefs=[], domain_context=None)
    assert "Available Prompt Skills" not in p0
    assert "Current Goal: g" in p0

    # Con skills -> sección consultiva que nunca autoriza ejecusión directa.
    item = _skill_item("inbox", "tenant-a", "inbox_zero", "no ejecutes esto directamente")
    p1 = build_intent_proposal_prompt(goal="g", beliefs=[], skills=[item])
    assert "Available Prompt Skills" in p1
    assert "consultative" in p1
    assert "no ejecutes esto directamente" in p1
    assert "formal frozen" in p1


def test_format_skills_vacio():
    assert format_skills([]) == ""