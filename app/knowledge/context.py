from app.knowledge.database import KnowledgeBase


def planner_context(database: KnowledgeBase, limit_per_type: int = 200) -> dict:
    context = {}
    for prototype_type in ("item", "entity", "recipe", "technology", "fluid", "resource", "module", "mod"):
        records = database.find(prototype_type)[:limit_per_type]
        if records:
            context[prototype_type] = [{"name": item.name, "source_mod": item.source_mod, "data": item.data} for item in records]
    return context