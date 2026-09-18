"""Tests C1a: 18 entity types del kernel (spec 03, D03)."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agentic_os.kernel.ontology.entities_catalog import (
    CORE_ENTITY_KIND_TO_CLASS,
    CORE_ENTITY_TYPES,
    Audio,
    Company,
    Dataset,
    Document,
    Email,
    Event,
    File,
    Image,
    Message,
    Organization,
    Person,
    Product,
    Service,
    SocialPost,
    Task,
    URL,
    Video,
    Website,
)


TID = "tenant-test"


def test_hay_exactamente_18_tipos():
    assert len(CORE_ENTITY_TYPES) == 18
    assert len(CORE_ENTITY_KIND_TO_CLASS) == 18


def test_todos_los_kinds_empiezan_por_core():
    for kind in CORE_ENTITY_KIND_TO_CLASS:
        assert kind.startswith("core."), kind


def test_person_minimo():
    p = Person(tenant_id=TID, name="Ana", emails=["a@b.com"])
    assert p.kind == "core.person"
    assert p.id
    assert p.organization_id is None


def test_person_rechaza_extra():
    with pytest.raises(ValidationError):
        Person(tenant_id=TID, name="Ana", emails=[], campo_inventado="x")


def test_person_requiere_tenant():
    with pytest.raises(ValidationError):
        Person(name="Ana", emails=[])


def test_organization_minimo():
    o = Organization(tenant_id=TID, name="ACME")
    assert o.kind == "core.organization"
    assert o.website is None


def test_company_minimo():
    c = Company(tenant_id=TID, legal_name="ACME SL", name="ACME")
    assert c.kind == "core.company"
    assert c.revenue is None


def test_product_minimo():
    p = Product(tenant_id=TID, name="Widget")
    assert p.kind == "core.product"


def test_service_minimo():
    s = Service(tenant_id=TID, name="Consultoria")
    assert s.kind == "core.service"


def test_website_minimo():
    w = Website(tenant_id=TID, url="https://x.com")
    assert w.kind == "core.website"


def test_url_minimo():
    u = URL(tenant_id=TID, url="https://x.com/a", scheme="https", host="x.com", path="/a")
    assert u.kind == "core.url"
    assert u.query is None


def test_file_minimo():
    f = File(tenant_id=TID, path="a/b.txt", name="b.txt", format="txt")
    assert f.kind == "core.file"


def test_document_minimo():
    d = Document(tenant_id=TID, title="T", format="md")
    assert d.kind == "core.document"
    assert d.metadata == {}


def test_dataset_minimo():
    ds = Dataset(tenant_id=TID, name="ventas", columns=["a", "b"], rows=10, format="csv")
    assert ds.kind == "core.dataset"


def test_dataset_rows_no_negativo():
    with pytest.raises(ValidationError):
        Dataset(tenant_id=TID, name="x", columns=[], rows=-1, format="csv")


def test_message_minimo():
    ts = datetime.now(timezone.utc)
    m = Message(tenant_id=TID, channel="slack", sender="u1", recipient="u2", content="hola", timestamp=ts)
    assert m.kind == "core.message"


def test_email_minimo():
    e = Email(tenant_id=TID, from_="a@b.com", to=["c@d.com"], subject="s", body="b")
    assert e.kind == "core.email"
    assert e.cc == []


def test_social_post_minimo():
    sp = SocialPost(tenant_id=TID, platform="meta", content="hola", status="draft")
    assert sp.kind == "core.social_post"
    assert sp.media == []


def test_image_minimo():
    i = Image(tenant_id=TID, format="png")
    assert i.kind == "core.image"
    assert i.url is None and i.path is None


def test_video_minimo():
    v = Video(tenant_id=TID, format="mp4")
    assert v.kind == "core.video"


def test_audio_minimo():
    a = Audio(tenant_id=TID, format="mp3")
    assert a.kind == "core.audio"


def test_event_minimo():
    ts = datetime.now(timezone.utc)
    ev = Event(tenant_id=TID, type="created", at=ts, actor_id="u1", entity_id="e1")
    assert ev.kind == "core.event"
    assert ev.payload == {}


def test_task_minimo():
    t = Task(tenant_id=TID, title="do X", status="pending")
    assert t.kind == "core.task"
    assert t.dependencies == []


def test_todos_frozen():
    p = Person(tenant_id=TID, name="Ana", emails=[])
    with pytest.raises(ValidationError):
        p.name = "Otro"


def test_kinds_unicos():
    kinds = [cls.model_fields["kind"].default for cls in CORE_ENTITY_TYPES]
    assert len(kinds) == len(set(kinds))


def test_registry_apunta_a_las_clases_correctas():
    assert CORE_ENTITY_KIND_TO_CLASS["core.person"] is Person
    assert CORE_ENTITY_KIND_TO_CLASS["core.task"] is Task
    assert CORE_ENTITY_KIND_TO_CLASS["core.email"] is Email

