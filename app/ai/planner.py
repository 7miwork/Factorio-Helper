import json

from app.ai.prompts import planner_prompt
from app.ai.manager import ProviderManager


REQUIRED_FIELDS = {"name", "description", "layout_strategy", "production", "machines", "inputs", "outputs", "constraints"}


class ProductionPlanner:
    def __init__(self, manager: ProviderManager):
        self.manager = manager

    def create_plan(self, context: dict, requirements: str, layout_strategy: str = "expandable") -> dict:
        response = self.manager.complete(planner_prompt(context, requirements, layout_strategy), "planner")
        try:
            plan = json.loads(response)
        except json.JSONDecodeError as error:
            raise ValueError("AI planner returned invalid JSON") from error
        missing = REQUIRED_FIELDS - set(plan) if isinstance(plan, dict) else REQUIRED_FIELDS
        if missing:
            raise ValueError(f"AI planner response missing fields: {', '.join(sorted(missing))}")
        if plan["layout_strategy"] not in {"compact", "balanced", "expandable", "main_bus", "city_block"}:
            raise ValueError(f"Unsupported layout strategy: {plan['layout_strategy']}")
        if not isinstance(plan["machines"], list):
            raise ValueError("AI planner machines must be a list")
        return plan