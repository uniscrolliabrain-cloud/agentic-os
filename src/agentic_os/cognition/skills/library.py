"""cognition.skills.library: registro de skills disponibles."""

from __future__ import annotations

from typing import List

from .skill import Skill

# Registro de skills disponibles en el sistema.
# Cada Skill es un SOP formal (ver cognition/skills/skill.py).
SKILLS: List[Skill] = []

