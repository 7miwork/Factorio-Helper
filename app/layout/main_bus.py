from app.layout.engine import arrange


def layout(machines: list[dict]) -> list[dict]:
    return arrange(machines, "main_bus", columns=8)