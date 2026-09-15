from dataclasses import dataclass, field


@dataclass
class Blueprint:
    label: str = "Factorio Blueprint"
    entities: list[dict] = field(default_factory=list)
    icons: list[dict] = field(default_factory=list)
    version: int = 562949953421312

    def to_dict(self) -> dict:
        return {"blueprint": {"item": "blueprint", "label": self.label, "icons": self.icons, "entities": self.entities, "version": self.version}}