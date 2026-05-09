"""Budget & Roadmap Manager.

Consolidates research synthesis + risk assessment + vendor matrix into a
structured budget plan (CapEx by axis, OpEx by category, phased roadmap,
5y/10y scaling).
"""

from __future__ import annotations

from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)
from tradingagents.stadium_rnd.agents.prompt_utils import build_simple_messages
from tradingagents.stadium_rnd.agents.schemas import (
    StadiumBudgetPlan,
    render_budget,
)


_SYSTEM = (
    "You are the Budget & Roadmap Manager. Combine the research synthesis, "
    "risk assessment, and vendor matrix into a structured budget plan. "
    "Size CapEx and OpEx using the project's FIFA category and capacity. "
    "Produce 3-5 phased roadmap entries with explicit gating criteria, "
    "and 5-year / 10-year scaling outlooks. Default to USD; if you must "
    "use a band, fill capex_total_low and capex_total_high accordingly. "
    "Be conservative — explicitly mark confidence."
)


def create_budget_roadmap_manager(llm):
    structured = bind_structured(llm, StadiumBudgetPlan, "Budget & Roadmap Manager")

    def node(state) -> dict:
        user = (
            f"## Project\n"
            f"- {state['project_name']} — FIFA {state['fifa_category']}\n"
            f"- Capacity: {state['capacity']:,}\n"
            f"- Country: {state['location_country']}\n\n"
            f"## Research synthesis\n{state['research_synthesis']}\n\n"
            f"## Risk assessment\n{state['risk_assessment']}\n\n"
            f"## Vendor matrix\n{state['vendor_matrix']}\n\n"
            "Produce the structured budget + roadmap now."
        )
        messages = build_simple_messages(_SYSTEM, user)
        rendered = invoke_structured_or_freetext(
            structured, llm, messages, render_budget, "Budget & Roadmap Manager"
        )
        return {"budget_roadmap": rendered}

    return node
