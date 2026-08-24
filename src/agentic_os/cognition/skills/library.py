from .skill import Skill
SKILLS = {
  "inbox_zero": Skill(name="inbox_zero", description="Procesar email y proponer Intent", requires_tool="gmail_read"),
  "schedule_meeting": Skill(name="schedule_meeting", description="Proponer reunion", requires_tool="calendar_read")
}
