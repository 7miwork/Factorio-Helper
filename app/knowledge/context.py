from pathlib import Path

from app.knowledge.database import KnowledgeBase
from app.utils import paths


def learning_notes_file() -> Path:
    """Pfad zur KI-Lern-Datei (data/learn/notes.md)."""
    return paths.ROOT / "data" / "learn" / "notes.md"


def load_learning_notes() -> str:
    """Liefert die gespeicherten Lern-Notizen (leer, wenn keine vorhanden)."""
    try:
        return learning_notes_file().read_text(encoding="utf-8")
    except OSError:
        return ""


def save_learning_notes(text: str) -> Path:
    """Speichert die Lern-Notizen und gibt den Zielpfad zurück."""
    target = learning_notes_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text or "", encoding="utf-8")
    return target


def planner_context(database: KnowledgeBase, limit_per_type: int = 200) -> dict:
    context = {}
    for prototype_type in ("item", "entity", "recipe", "technology", "fluid", "resource", "module", "mod"):
        records = database.find(prototype_type)[:limit_per_type]
        if records:
            context[prototype_type] = [{"name": item.name, "source_mod": item.source_mod, "data": item.data} for item in records]
    notes = load_learning_notes()
    if notes:
        context["learning_notes"] = notes
    return context