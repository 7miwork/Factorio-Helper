from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
from typing import Iterable

from app.knowledge.entities import Prototype


class KnowledgeBase:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("CREATE TABLE IF NOT EXISTS prototypes (name TEXT NOT NULL, prototype_type TEXT NOT NULL, source_mod TEXT NOT NULL, source_file TEXT NOT NULL, data_json TEXT NOT NULL, PRIMARY KEY (name, prototype_type, source_mod))")
        self.connection.execute("CREATE INDEX IF NOT EXISTS idx_prototypes_type ON prototypes(prototype_type)")
        self.connection.commit()

    def add(self, prototypes: Iterable[Prototype]) -> int:
        rows = [(item.name, item.prototype_type, item.source_mod, item.source_file, json.dumps(item.data, sort_keys=True)) for item in prototypes]
        self.connection.executemany("INSERT OR REPLACE INTO prototypes VALUES (?, ?, ?, ?, ?)", rows)
        self.connection.commit()
        return len(rows)

    def count(self) -> int:
        return self.connection.execute("SELECT COUNT(*) FROM prototypes").fetchone()[0]

    def find(self, prototype_type: str | None = None) -> list[Prototype]:
        if prototype_type:
            rows = self.connection.execute("SELECT name, prototype_type, source_mod, source_file, data_json FROM prototypes WHERE prototype_type = ? ORDER BY name", (prototype_type,)).fetchall()
        else:
            rows = self.connection.execute("SELECT name, prototype_type, source_mod, source_file, data_json FROM prototypes ORDER BY prototype_type, name").fetchall()
        return [Prototype(row[0], row[1], row[2], row[3], json.loads(row[4])) for row in rows]

    def close(self) -> None:
        self.connection.close()


def database_path(project_root: str | Path) -> Path:
    return Path(project_root) / "data" / "factorio" / "knowledge.db"