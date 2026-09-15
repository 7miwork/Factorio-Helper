from collections import defaultdict

from app.knowledge.recipes import Recipe


def calculate_requirements(recipes: list[Recipe], target: str, target_per_minute: float) -> dict[str, float]:
    by_result = {result.name: recipe for recipe in recipes for result in recipe.results}
    requirements: defaultdict[str, float] = defaultdict(float)
    visiting: set[str] = set()

    def visit(item: str, amount: float) -> None:
        recipe = by_result.get(item)
        if not recipe or item in visiting:
            requirements[item] += amount
            return
        result = next(result for result in recipe.results if result.name == item)
        batches = amount / result.amount
        visiting.add(item)
        for ingredient in recipe.ingredients:
            visit(ingredient.name, ingredient.amount * batches)
        visiting.remove(item)

    visit(target, target_per_minute / 60)
    return dict(requirements)