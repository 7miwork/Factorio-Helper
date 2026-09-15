from dataclasses import replace


STRATEGIES = {"compact", "balanced", "expandable", "main_bus", "city_block"}


def arrange(machines: list[dict], strategy: str = "balanced", columns: int = 4) -> list[dict]:
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown layout strategy: {strategy}")
    if columns < 1:
        raise ValueError("columns must be positive")
    spacing = {"compact": 2, "balanced": 3, "expandable": 4, "main_bus": 5, "city_block": 6}[strategy]
    arranged = []
    for index, machine in enumerate(machines):
        entity = dict(machine)
        row, column = divmod(index, columns)
        entity["position"] = {"x": column * spacing, "y": row * spacing}
        arranged.append(entity)
    return arranged