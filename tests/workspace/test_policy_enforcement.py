import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from agentic_os.infrastructure.auth.models import AuthenticatedUser
from agentic_os.domains.tools.google.models import (
    SendEmailParams,
    CreateCalendarEventParams,
    ReadFileParams,
)
from agentic_os.domains.tools.google.workspace_tools import (
    GmailTool,
    CalendarTool,
    DriveTool,
)
from agentic_os.kernel.policy.models import Policy, PolicyRule
from agentic_os.kernel.policy.engine import PolicyEngine
from agentic_os.execution.action import Action
from agentic_os.execution.executor import Executor
from agentic_os.execution.tools.registry import ToolRegistry


def test_send_email_params_validation():
    # Valid
    params = SendEmailParams(
        to="patient@example.com",
        subject="Appointment Confirmation",
        body="Your appointment is set for tomorrow at 10:00 AM.",
        cc=["doctor@example.com"],
    )
    assert params.to == "patient@example.com"
    assert params.cc == ["doctor@example.com"]

    # Missing required field
    with pytest.raises(ValidationError):
        SendEmailParams(to="patient@example.com", subject="No body")


def test_create_calendar_event_params_validation():
    start = datetime.now(timezone.utc)
    end = start + timedelta(hours=1)

    params = CreateCalendarEventParams(
        title="Consultation Dr. Smith",
        start_time=start,
        end_time=end,
        attendees=["patient@example.com"],
    )
    assert params.title == "Consultation Dr. Smith"
    assert len(params.attendees) == 1

    # Missing start_time
    with pytest.raises(ValidationError):
        CreateCalendarEventParams(title="Invalid Event", end_time=end)


def test_policy_denies_unauthorized_user_even_with_valid_token():
    """PolicyEngine must reject capability if user lacks required role, even if authenticated."""
    policy = Policy(
        id="strict_clinic",
        name="Strict Clinic Policy",
        rules=[
            PolicyRule(
                id="rule_gmail_send",
                capability="gmail:send",
                effect="allow",
                requires_roles=["clinician"],
            )
        ],
    )
    engine = PolicyEngine(policy)
    registry = ToolRegistry()
    gmail_tool = GmailTool()
    registry.register(gmail_tool)

    executor = Executor(policy_engine=engine, tools=registry)

    # User is fully authenticated via Google, but only has 'user' role
    regular_user = AuthenticatedUser(
        id="google_sub_999",
        email="patient@example.com",
        roles=["user"],
    )

    action = Action(
        capability="gmail:send",
        actor_id=regular_user.id,
        params={
            "to": "hospital@example.com",
            "subject": "Unauthorized request",
            "body": "Attempting action",
        },
    )

    # Execute should be denied by policy
    result = executor.execute(action, roles=regular_user.roles)
    assert result.success is False
    assert "denied" in (result.error or "")


def test_policy_allows_authorized_clinician():
    """PolicyEngine allows action when user has required 'clinician' role."""
    policy = Policy(
        id="strict_clinic",
        name="Strict Clinic Policy",
        rules=[
            PolicyRule(
                id="rule_gmail_send",
                capability="gmail:send",
                effect="allow",
                requires_roles=["clinician"],
            )
        ],
    )
    engine = PolicyEngine(policy)
    registry = ToolRegistry()
    gmail_tool = GmailTool()
    registry.register(gmail_tool)

    executor = Executor(policy_engine=engine, tools=registry)

    clinician = AuthenticatedUser(
        id="google_sub_101",
        email="doctor@hospital.com",
        roles=["clinician", "user"],
    )

    action = Action(
        capability="gmail:send",
        actor_id=clinician.id,
        params={
            "to": "patient@hospital.com",
            "subject": "Lab results ready",
            "body": "Your lab results are ready for review.",
        },
    )

    result = executor.execute(action, roles=clinician.roles)
    assert result.success is True
    assert result.output.get("kind") == "email_sent"
