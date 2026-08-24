from ...kernel.policy.models import Policy, PolicyRule

CLINIC_POLICY = Policy(
    id="clinic",
    name="Clinic Domain Policy",
    rules=[
        PolicyRule(
            id="rule_gmail_send",
            capability="gmail:send",
            description="Allows clinicians and operators to send patient emails",
            effect="allow",
            requires_roles=["clinician", "operator"],
        ),
        PolicyRule(
            id="rule_calendar_create",
            capability="calendar:create",
            description="Allows clinicians and operators to schedule appointments",
            effect="allow",
            requires_roles=["clinician", "operator"],
        ),
        PolicyRule(
            id="rule_drive_read",
            capability="drive:read",
            description="Allows clinicians to read medical records from Drive",
            effect="allow",
            requires_roles=["clinician"],
        ),
    ],
)

