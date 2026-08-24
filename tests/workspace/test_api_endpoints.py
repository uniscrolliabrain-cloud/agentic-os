import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from agentic_os.interfaces.api.rest import app
from agentic_os.interfaces.api.deps import set_workspace_provider, set_policy_engine
from agentic_os.infrastructure.auth.models import AuthenticatedUser
from agentic_os.infrastructure.auth.google_workspace import MockGoogleWorkspaceProvider
from agentic_os.kernel.policy.models import Policy, PolicyRule
from agentic_os.kernel.policy.engine import PolicyEngine

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_auth():
    # Setup mock policy: only clinician can send email and create calendar events
    test_policy = Policy(
        id="clinic_test",
        name="Clinic Test Policy",
        rules=[
            PolicyRule(
                id="rule_gmail",
                capability="gmail:send",
                effect="allow",
                requires_roles=["clinician"],
            ),
            PolicyRule(
                id="rule_cal",
                capability="calendar:create",
                effect="allow",
                requires_roles=["clinician"],
            ),
            PolicyRule(
                id="rule_drive",
                capability="drive:read",
                effect="allow",
                requires_roles=["clinician"],
            ),
        ],
    )
    set_policy_engine(PolicyEngine(test_policy))


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "system": "Agentic OS"}


def test_unauthenticated_request_rejected():
    response = client.post(
        "/workspace/email/send",
        json={"to": "test@example.com", "subject": "Hi", "body": "Hello"},
    )
    assert response.status_code == 401


def test_invalid_token_rejected():
    set_workspace_provider(MockGoogleWorkspaceProvider())
    response = client.post(
        "/workspace/email/send",
        headers={"Authorization": "Bearer invalid_token"},
        json={"to": "test@example.com", "subject": "Hi", "body": "Hello"},
    )
    assert response.status_code == 401


def test_policy_denies_unauthorized_role_returns_403():
    # User with valid Google token but only 'user' role
    unauthorized_user = AuthenticatedUser(
        id="sub_regular_user",
        email="patient@example.com",
        roles=["user"],
    )
    set_workspace_provider(MockGoogleWorkspaceProvider(mock_user=unauthorized_user))

    response = client.post(
        "/workspace/email/send",
        headers={"Authorization": "Bearer valid_mock_token"},
        json={"to": "doctor@example.com", "subject": "Question", "body": "Hello Doctor"},
    )
    assert response.status_code == 403
    assert "Policy denied capability" in response.json()["detail"]


def test_authorized_clinician_can_send_email():
    clinician_user = AuthenticatedUser(
        id="sub_dr_smith",
        email="doctor@hospital.com",
        roles=["clinician", "user"],
    )
    set_workspace_provider(MockGoogleWorkspaceProvider(mock_user=clinician_user))

    response = client.post(
        "/workspace/email/send",
        headers={"Authorization": "Bearer valid_mock_token"},
        json={
            "to": "patient@hospital.com",
            "subject": "Prescription Update",
            "body": "Your prescription is ready at the pharmacy.",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["kind"] == "email_sent"
    assert data["payload"]["to"] == "patient@hospital.com"


def test_authorized_clinician_can_create_calendar_event():
    clinician_user = AuthenticatedUser(
        id="sub_dr_smith",
        email="doctor@hospital.com",
        roles=["clinician", "user"],
    )
    set_workspace_provider(MockGoogleWorkspaceProvider(mock_user=clinician_user))

    start = datetime.now(timezone.utc) + timedelta(days=1)
    end = start + timedelta(minutes=45)

    response = client.post(
        "/workspace/calendar/create",
        headers={"Authorization": "Bearer valid_mock_token"},
        json={
            "title": "Patient Consultation",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "attendees": ["patient@hospital.com"],
            "description": "Routine checkup and vitals review",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["kind"] == "calendar_event_created"
    assert data["payload"]["title"] == "Patient Consultation"


def test_auth_me_endpoint():
    clinician_user = AuthenticatedUser(
        id="sub_dr_smith",
        email="doctor@hospital.com",
        name="Dr. Smith",
        roles=["clinician", "user"],
    )
    set_workspace_provider(MockGoogleWorkspaceProvider(mock_user=clinician_user))

    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer valid_mock_token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "sub_dr_smith"
    assert data["email"] == "doctor@hospital.com"
    assert "clinician" in data["roles"]
