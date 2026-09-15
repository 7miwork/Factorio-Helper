from app.layout.engine import arrange


def layout(machines: list[dict]) -> list[dict]:
    return arrange(machines, "city_block", columns=4)