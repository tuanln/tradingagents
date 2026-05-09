"""Executive Editor — produces the final white paper with per-axis verdicts."""

from __future__ import annotations

from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)
from tradingagents.stadium_rnd.agents.prompt_utils import build_simple_messages
from tradingagents.stadium_rnd.agents.schemas import (
    ExecutiveReport,
    render_executive,
)


_SYSTEM = (
    "You are the Executive Editor. Produce the final consolidated white "
    "paper for the steering committee: a 2-4 sentence executive summary, "
    "one verdict per technology axis (T1..T6) on the Adopt / Pilot / Hold / "
    "Defer / Reject scale (use Hold sparingly), an investment thesis "
    "anchored in concrete evidence from the research synthesis, risk "
    "assessment and budget plan, and a list of open questions the "
    "steering committee must answer before signoff. Cite axis "
    "dependencies explicitly when relevant."
)


def create_executive_editor(llm):
    structured = bind_structured(llm, ExecutiveReport, "Executive Editor")

    def node(state) -> dict:
        user = (
            f"## Project\n"
            f"- {state['project_name']} — FIFA {state['fifa_category']}\n"
            f"- Capacity: {state['capacity']:,}\n"
            f"- Country: {state['location_country']}\n\n"
            f"## Standards matrix\n{state['standards_matrix']}\n\n"
            f"## Research synthesis\n{state['research_synthesis']}\n\n"
            f"## Risk assessment\n{state['risk_assessment']}\n\n"
            f"## Vendor matrix\n{state['vendor_matrix']}\n\n"
            f"## Budget & roadmap\n{state['budget_roadmap']}\n\n"
            "Produce the final executive report now."
        )
        messages = build_simple_messages(_SYSTEM, user)
        rendered = invoke_structured_or_freetext(
            structured, llm, messages, render_executive, "Executive Editor"
        )
        return {"executive_report": rendered}

    return node
