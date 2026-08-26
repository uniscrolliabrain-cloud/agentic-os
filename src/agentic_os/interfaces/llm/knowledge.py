"""Knowledge base ligera (RAG-lite) para el asistente frontal.

Busca por palabras clave en los documentos Markdown/TXT de la carpeta `knowledge`
del repo y devuelve los fragmentos más relevantes para que el LLM frontal pueda
responder con datos de la empresa sin llamar al orquestador.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

# knowledge/ está en la raíz del repo (src/agentic_os/interfaces/llm/knowledge.py -> parents[4])
_REPO_KNOWLEDGE = Path(__file__).resolve().parents[4] / "knowledge"

_STOP_WORDS = {
    "que", "con", "para", "una", "los", "las", "por", "como", "del", "son", "esta",
    "este", "esto", "eso", "pero", "más", "muy", "the", "and", "for", "with", "into",
    "this", "that", "from", "what", "how", "when", "your", "you", "you",
}


class KnowledgeBase:
    """Carga los documentos de conocimiento en memoria y permite recuperarlos."""

    def __init__(self, directory: Path | str | None = None):
        self.directory = Path(directory) if directory else _REPO_KNOWLEDGE
        self._documents: List[Dict] = self._load()

    def _load(self) -> List[Dict]:
        docs: List[Dict] = []
        if not self.directory.exists():
            return docs
        paths = sorted(self.directory.glob("*.md")) + sorted(self.directory.glob("*.txt"))
        for path in paths:
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue
            title = path.stem.replace("_", " ").replace("-", " ").title()
            docs.append({"path": str(path), "title": title, "text": text})
        return docs

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """Devuelve los documentos más relevantes para la consulta."""
        if not query or not self._documents:
            return []
        tokens = self._tokenize(query)
        if not tokens:
            return []
        scored: List[tuple] = []
        for doc in self._documents:
            text_lower = doc["text"].lower()
            title_lower = doc["title"].lower()
            score = 0
            for tok in tokens:
                if tok in title_lower:
                    score += 4
                score += text_lower.count(tok)
            if score > 0:
                scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:top_k]]

    def count(self) -> int:
        return len(self._documents)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        words = re.findall(r"[a-záéíóúñü0-9]+", text.lower())
        return [w for w in words if w not in _STOP_WORDS and len(w) >= 3][:12]