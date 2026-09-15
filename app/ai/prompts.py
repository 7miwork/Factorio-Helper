import json


def planner_prompt(context: dict, requirements: str, layout_strategy: str) -> str:
    return "Return only valid JSON matching this schema: name, description, layout_strategy, production, machines, inputs, outputs, constraints.\n" + json.dumps({"factorio": context, "requirements": requirements, "layout_strategy": layout_strategy}, ensure_ascii=False)