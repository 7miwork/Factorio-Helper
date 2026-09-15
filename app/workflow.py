import json
from pathlib import Path

from app.ai.manager import ProviderManager
from app.ai.planner import ProductionPlanner
from app.blueprint.encoder import encode
from app.blueprint.generator import generate
from app.knowledge.context import planner_context
from app.knowledge.database import KnowledgeBase, database_path
from app.library.manager import LibraryManager


def generate_from_requirements(requirements: str, project_root: str | Path, slug: str = "generated") -> dict:
    root = Path(project_root)
    database = KnowledgeBase(database_path(root))
    try:
        context = planner_context(database)
    finally:
        database.close()
    config_path = root / "config" / "ai_providers.json"
    plan = ProductionPlanner(ProviderManager(config_path)).create_plan(context, requirements)
    blueprint = generate(plan)
    folder = LibraryManager(root / "blueprints").save(slug, blueprint, {"description": plan["description"], "layout_strategy": plan["layout_strategy"], "readme": f"# {plan['name']}\n\n{plan['description']}\n"})
    return {"folder": str(folder), "blueprint_string": encode(blueprint), "plan": plan}