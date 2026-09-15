from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class FactorioInstallation:
    path: Path
    version: str | None
    executable: Path | None


def detect_installation(path: str | Path) -> FactorioInstallation:
    root = Path(path).expanduser().resolve()
    executable = next((root / relative for relative in ("bin/x64/factorio.exe", "bin/factorio.exe") if (root / relative).is_file()), None)
    version = None
    for info_path in (root / "data/base/info.json", root / "data/core/info.json"):
        if info_path.is_file():
            try:
                info = json.loads(info_path.read_text(encoding="utf-8"))
                version = str(info.get("version")) if info.get("version") else None
            except (OSError, json.JSONDecodeError):
                pass
            if version:
                break
    if not root.is_dir():
        raise FileNotFoundError(f"Factorio installation not found: {root}")
    return FactorioInstallation(root, version, executable)