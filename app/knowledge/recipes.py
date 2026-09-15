from dataclasses import dataclass


@dataclass(frozen=True)
class Ingredient:
    name: str
    amount: float


@dataclass(frozen=True)
class Recipe:
    name: str
    ingredients: tuple[Ingredient, ...]
    results: tuple[Ingredient, ...]
    energy: float


def _amount(value: dict) -> float:
    return float(value.get("amount", value.get("amount_min", 0)))


def parse_recipe(data: dict) -> Recipe:
    ingredients = tuple(Ingredient(str(item["name"] if isinstance(item, dict) else item[0]), _amount(item) if isinstance(item, dict) else float(item[1])) for item in data.get("ingredients", []))
    result_values = data.get("results") or ([{"name": data["result"], "amount": data.get("result_count", 1)}] if data.get("result") else [])
    results = tuple(Ingredient(str(item["name"] if isinstance(item, dict) else item[0]), _amount(item) if isinstance(item, dict) else float(item[1])) for item in result_values)
    return Recipe(str(data["name"]), ingredients, results, float(data.get("energy_required", 0.5)))