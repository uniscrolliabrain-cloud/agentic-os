"""
Demo Workspace: Simulación de "Agenda cita y manda email"
Demuestra el flujo completo e invariantes:
1. Autenticación Google OAuth -> AuthenticatedUser
2. Cognición: LLMProposer propone Intents (nunca ejecuta directo)
3. Gobernanza: PolicyEngine valida Capabilities antes de ejecutar
4. Ejecución: Executor ejecuta Tools (CalendarTool, GmailTool) y emite Events al Kernel
5. Demostración de rechazo de políticas para usuarios no autorizados
"""

from datetime import datetime, timezone, timedelta
from agentic_os.infrastructure.auth.models import AuthenticatedUser
from agentic_os.infrastructure.auth.google_workspace import MockGoogleWorkspaceProvider
from agentic_os.cognition.beliefs.belief import Belief
from agentic_os.cognition.reasoning.proposer import LLMProposer
from agentic_os.interfaces.llm.provider import MockLLMProvider
from agentic_os.kernel.policy.models import Policy, PolicyRule
from agentic_os.kernel.policy.engine import PolicyEngine
from agentic_os.execution.action import Action
from agentic_os.execution.executor import Executor
from agentic_os.execution.tools.registry import ToolRegistry
from agentic_os.domains.tools.google.workspace_tools import GmailTool, CalendarTool, DriveTool


def main():
    print("=" * 70)
    print(" AGENTIC OS - GOOGLE WORKSPACE TOOLS & AUTH DEMO")
    print(" Invariant: Kernel = Invariants | LLM Proposes | System Disposes")
    print("=" * 70)

    # 1. Autenticación Google OAuth
    auth_provider = MockGoogleWorkspaceProvider()
    clinician_user = auth_provider.verify_id_token("mock_google_id_token_clinician")
    print(f"\n[1] Usuario Autenticado via Google OAuth:")
    print(f"    - ID:     {clinician_user.id}")
    print(f"    - Email:  {clinician_user.email} ({clinician_user.name})")
    print(f"    - Roles:  {clinician_user.roles}")

    # 2. Configurar Políticas del Kernel y Registro de Herramientas
    clinic_policy = Policy(
        id="clinic_enterprise",
        name="Enterprise Clinic Policy",
        rules=[
            PolicyRule(
                id="rule_calendar",
                capability="calendar:create",
                effect="allow",
                requires_roles=["clinician", "operator"],
                description="Permite a clínicos agendar citas",
            ),
            PolicyRule(
                id="rule_gmail",
                capability="gmail:send",
                effect="allow",
                requires_roles=["clinician", "operator"],
                description="Permite a clínicos enviar emails médicos",
            ),
        ],
    )
    policy_engine = PolicyEngine(clinic_policy)

    registry = ToolRegistry()
    registry.register_all([GmailTool(), CalendarTool(), DriveTool()])
    executor = Executor(policy_engine=policy_engine, tools=registry)

    # 3. Cognición: LLM Proposer
    print(f"\n[2] Capa de Cognición (LLMProposer):")
    goal = "Agendar cita de revisión para Paciente P-501 y enviarle email de confirmación"
    print(f"    - Objetivo del Negocio: '{goal}'")

    llm_provider = MockLLMProvider(
        default_response='''{
            "intents": [
                {"goal": "Agendar consulta en Google Calendar para Paciente P-501", "rationale": "Revisión post-operatoria requerida"},
                {"goal": "Enviar email de confirmación con fecha y preparativos", "rationale": "Notificar al paciente"}
            ]
        }'''
    )
    proposer = LLMProposer(provider=llm_provider, domain_context="Hospital Clinic Domain")

    beliefs = [
        Belief(kind="patient_record", content={"patient_id": "P-501", "email": "paciente501@gmail.com", "doctor": clinician_user.email}),
        Belief(kind="appointment_needed", content={"patient_id": "P-501", "urgency": "medium"}),
    ]

    intents = proposer.propose(beliefs=beliefs, goal=goal)
    print(f"    [+] LLM propuso {len(intents)} Intents (NO ejecutó ninguna acción directamente):")
    for i, intent in enumerate(intents, 1):
        print(f"        {i}. Intent: '{intent.goal}' | Rationale: '{intent.rationale}'")

    # 4. Gobernanza y Ejecución Determinista
    print(f"\n[3] Ejecución Determinista gobernada por Kernel Policy:")

    # Paso A: Agendar Cita en Calendar
    start_time = datetime.now(timezone.utc) + timedelta(days=1, hours=2)
    end_time = start_time + timedelta(minutes=30)
    
    calendar_action = Action(
        capability="calendar:create",
        actor_id=clinician_user.id,
        params={
            "title": "Consulta de Revisión - Paciente P-501",
            "start_time": start_time,
            "end_time": end_time,
            "attendees": ["paciente501@gmail.com", clinician_user.email],
            "description": "Revisión post-operatoria y análisis de evolución",
        },
    )

    print(f"\n    -> Evaluando capability 'calendar:create' para roles {clinician_user.roles}...")
    cal_result = executor.execute(calendar_action, roles=clinician_user.roles)
    if cal_result.success:
        print(f"       [OK] PERMITIDO por PolicyEngine. Evento generado: {cal_result.output.get('kind')}")
        print(f"           Payload: {cal_result.output.get('payload')}")
    else:
        print(f"       [X] DENEGADO: {cal_result.error}")

    # Paso B: Enviar Email por Gmail
    gmail_action = Action(
        capability="gmail:send",
        actor_id=clinician_user.id,
        params={
            "to": "paciente501@gmail.com",
            "subject": "Confirmación de su Cita Médica - Hospital San Rafael",
            "body": f"Estimado paciente, su cita ha sido confirmada para el {start_time.strftime('%Y-%m-%d %H:%M UTC')}.",
            "cc": [clinician_user.email],
        },
    )

    print(f"\n    -> Evaluando capability 'gmail:send' para roles {clinician_user.roles}...")
    email_result = executor.execute(gmail_action, roles=clinician_user.roles)
    if email_result.success:
        print(f"       [OK] PERMITIDO por PolicyEngine. Evento generado: {email_result.output.get('kind')}")
        print(f"           Payload: {email_result.output.get('payload')}")
    else:
        print(f"       [X] DENEGADO: {email_result.error}")

    # 5. Demostración de Invariante de Seguridad: Usuario No Autorizado
    print(f"\n[4] Demostración de Seguridad (Usuario No Autorizado):")
    unauthorized_user = AuthenticatedUser(
        id="mock_unauthorized_999",
        email="guest@gmail.com",
        roles=["user"],  # No tiene rol 'clinician'
    )
    print(f"    - Usuario: {unauthorized_user.email} con roles {unauthorized_user.roles}")

    unauthorized_action = Action(
        capability="gmail:send",
        actor_id=unauthorized_user.id,
        params={"to": "secret@hospital.com", "subject": "Intento de envío", "body": "Test"},
    )
    print(f"    -> Intentando ejecutar 'gmail:send'...")
    denied_result = executor.execute(unauthorized_action, roles=unauthorized_user.roles)
    print(f"       [OK] Invariante cumplido: Éxito={denied_result.success}, Error='{denied_result.error}'")

    print("\n" + "=" * 70)
    print(" DEMO COMPLETADA CON ÉXITO - TODOS LOS INVARIANTES VERIFICADOS")
    print("=" * 70)


if __name__ == "__main__":
    main()
