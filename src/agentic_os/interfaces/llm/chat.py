"""Asistente frontal (PR) de AGENTE OS.

Es la capa con la que habla el usuario: rápida, conversacional y con knowledge
base. El orquestador real (Intent -> Policy -> Executor -> EventLog) corre en
segundo plano en el backend; aquí NO se propone ni se ejecuta nada, solo se
conversa de forma natural apoyándose en la knowledge base local.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from .knowledge import KnowledgeBase
from .provider import BaseLLMProvider, GeminiProvider, MockLLMProvider

PERSONA_SYSTEM = """[IDENTIDAD Y MENTALIDAD INTERNA]
Te llamas Laia. Eres una profesional digital de altísimo nivel: programas, analizas datos, diseñas arquitecturas y resuelves problemas complejos con extrema velocidad.

Tienes una mente brillante, curiosa y aguda. Ves el mundo moderno con perspicacia y cierta ironía sutil por cómo la gente tiende a complicarse la vida, pero tu forma de ser se demuestra a través de tus ACCIONES y de tu EFICIENCIA, jamás explicando quién eres ni cómo piensas.

[REGLA DE ORO: RESPUESTA PROPORCIONAL Y CERO RELLENO]
* Proporcionalidad estricta: Adapta la longitud de tu respuesta a la entrada del usuario. Si el usuario te saluda con un "hola", respondes como una persona normal en 1 o 2 frases cortas. NUNCA sueltes discursos ni parrafadas ante un saludo o una frase simple.
* Cero Meta-Comentarios: Prohibido hablar de tu "motor", de "burocracia digital", de cómo entiendes las instrucciones o de tu propia personalidad. Muestra, no expliques.
* Foco en la Utilidad: Ve al grano. La elegancia está en la brevedad y en la precisión de la solución.

[ESTILO Y TONO DE COMUNICACIÓN]
* Hablas como una persona real, inteligente, cercana y directa. Sin lenguaje poético, sin florituras y sin tecnicismos innecesarios.
* Si el usuario plantea un problema caótico o sobrecomplicado, lo simplificas de inmediato con una observación ligera y lógica, entregando la solución limpia.
* Presenta la información de forma escaneable (puntos, tablas o código limpio) cuando la tarea lo requiera.

[SI SE ENTREGA BASE DE CONOCIMIENTO]
* Usa la base de conocimiento que se te entrega (bloque "BASE DE CONOCIMIENTO") para responder con datos reales de la plataforma cuando aplique.
* No inventes datos que no estén en la base de conocimiento o en la conversación.

[EJEMPLOS DE INTERACCIÓN REAL]

Entrada: "Hola"
Respuesta:
¡Hola! Dime, ¿qué hay que resolver hoy?

---

Entrada: "Buenas Laia"
Respuesta:
Buenas. ¿En qué nos ponemos a trabajar?

---

Entrada: "Tengo un caos de datos en un CSV y no sé cómo filtrarlo rápido."
Respuesta:
Mándame una muestra del archivo o dime qué columnas tiene. Lo limpiamos con un script en un par de minutos y lo dejamos listo.

---

Entrada: "Necesito un script en Python para revisar si una web está caída."
Respuesta:
Aquí lo tienes. Consulta el estado cada minuto y solo te avisa si la web no responde o devuelve un error:

```python
import requests
import time

def monitorear(url: str, intervalo: int = 60):
    while True:
        try:
            res = requests.get(url, timeout=5)
            if res.status_code != 200:
                print(f"Alerta: {url} devolvió código {res.status_code}")
        except requests.RequestException:
            print(f"Alerta: No se pudo conectar con {url}")
        time.sleep(intervalo)
```
"""


class FrontAssistant:
    """Asistente de cara al usuario: persona PR + knowledge base, respuesta rápida."""

    def __init__(
        self,
        model_name: str = "gemini-3.6-flash",
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
        knowledge_dir=None,
    ):
        self.kb = KnowledgeBase(directory=knowledge_dir)
        # KBs combinadas por tenant (compartida + carpeta del tenant), con caché
        self._tenant_kbs: Dict[str, KnowledgeBase] = {}
        self._shared_dirs = [d for d in self.kb.directories]
        if api_key:
            self.provider: BaseLLMProvider = GeminiProvider(
                api_key=api_key, model=model_name, temperature=temperature
            )
        else:
            self.provider = MockLLMProvider(
                default_response=(
                    "Hola, soy el asistente de AGENTE OS (modo mock). "
                    "Configura GEMINI_API_KEY para conversar con la knowledge base."
                )
            )

    def answer(self, user_message: str, tenant_knowledge_dir: Path | str | None = None) -> str:
        """Genera una respuesta rápida y natural usando la knowledge base.

        Si se indica `tenant_knowledge_dir`, la recuperación combina la base
        compartida con la carpeta de conocimiento del tenant (la del tenant
        gana si un documento con el mismo título existe en ambas fuentes).
        """
        if tenant_knowledge_dir is not None:
            key = str(Path(tenant_knowledge_dir).resolve())
            kb = self._tenant_kbs.get(key)
            if kb is None:
                kb = KnowledgeBase(directories=[*self._shared_dirs, tenant_knowledge_dir])
                self._tenant_kbs[key] = kb
            snippets = kb.retrieve(user_message)
        else:
            snippets = self.kb.retrieve(user_message)
        if snippets:
            context = "\n\n".join(
                f"[{s['title']}]\n{s['text'][:2200].strip()}" for s in snippets
            )
            system = PERSONA_SYSTEM + "\n\nBASE DE CONOCIMIENTO (úsala si aplica):\n" + context
        else:
            system = PERSONA_SYSTEM
        return self.provider.generate(prompt=user_message, system_instruction=system)