from dataclasses import dataclass


@dataclass(frozen=True)
class Prototype:
    name: str
    prototype_type: str
    source_mod: str
    source_file: str
    data: dict