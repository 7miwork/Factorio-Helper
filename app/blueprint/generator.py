from app.blueprint.models import Blueprint
from app.layout.engine import arrange


def generate(plan: dict) -> dict:
    """Convert structured machine instructions into deterministic blueprint JSON."""
    entities = []
    strategy = plan.get("layout_strategy", "balanced")
    machines = arrange(plan.get("machines", []), strategy, columns=8 if strategy == "main_bus" else 4)
    for index, machine in enumerate(machines):
        entity = {"entity_number": index + 1, "name": machine["name"], "position": machine.get("position", {"x": index, "y": 0})}
        if machine.get("recipe"):
            entity["recipe"] = machine["recipe"]
        entities.append(entity)
    return Blueprint(label=plan.get("name", "Generated Blueprint"), entities=entities).to_dict()