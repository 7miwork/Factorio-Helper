from dataclasses import dataclass
import math
from typing import Iterable


@dataclass(frozen=True)
class ValidationIssue:
    reason: str
    entity_number: int | None = None
    suggestion: str = ""


def validate(blueprint: dict) -> list[ValidationIssue]:
    issues = []
    root = blueprint.get("blueprint") if isinstance(blueprint, dict) else None
    if not isinstance(root, dict):
        return [ValidationIssue("Missing blueprint object")]
    if root.get("item") != "blueprint":
        issues.append(ValidationIssue("Blueprint item must be 'blueprint'"))
    entities = root.get("entities", [])
    if not isinstance(entities, list):
        return issues + [ValidationIssue("entities must be a list")]
    numbers = set()
    for entity in entities:
        number = entity.get("entity_number") if isinstance(entity, dict) else None
        if not isinstance(entity, dict) or not entity.get("name"):
            issues.append(ValidationIssue("Entity name is missing", number, "Add a valid Factorio entity name"))
            continue
        if number in numbers:
            issues.append(ValidationIssue("Duplicate entity_number", number))
        numbers.add(number)
        position = entity.get("position")
        if not isinstance(position, dict) or not all(isinstance(position.get(axis), (int, float)) and math.isfinite(position[axis]) for axis in ("x", "y")):
            issues.append(ValidationIssue("Invalid entity position", number, "Use finite numeric x and y coordinates"))
    return issues


def validate_against_knowledge(blueprint: dict, prototypes: Iterable) -> list[ValidationIssue]:
    issues = validate(blueprint)
    entities = {item.name: item for item in prototypes if item.prototype_type in {"entity", "assembling-machine"}}
    recipes = {item.name: item for item in prototypes if item.prototype_type == "recipe"}
    root = blueprint.get("blueprint", {}) if isinstance(blueprint, dict) else {}
    for entity in root.get("entities", []) if isinstance(root.get("entities", []), list) else []:
        name = entity.get("name")
        number = entity.get("entity_number")
        if entities and name not in entities:
            issues.append(ValidationIssue(f"Unknown entity: {name}", number, "Import the required mod or choose an installed entity"))
        recipe_name = entity.get("recipe")
        if recipe_name and recipes and recipe_name not in recipes:
            issues.append(ValidationIssue(f"Unknown recipe: {recipe_name}", number, "Import the recipe's source mod or choose an installed recipe"))
        if recipe_name and name in entities:
            supported = entities[name].data.get("crafting_categories", [])
            recipe_data = recipes.get(recipe_name).data if recipe_name in recipes else {}
            category = recipe_data.get("category", "crafting")
            if supported and category not in supported:
                issues.append(ValidationIssue(f"Entity {name} does not support recipe category {category}", number))
    return issues