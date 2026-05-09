"""R&D Debate Moderator — synthesises the 3-way debate into structured output."""

from __future__ import annotations

from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)
from tradingagents.stadium_rnd.agents.prompt_utils import build_simple_messages
from tradingagents.stadium_rnd.agents.schemas import (
    ResearchSynthesis,
    render_research_synthesis,
)


_SYSTEM = (
    "You are the R&D Debate Moderator. Read the full debate between the "
    "Innovator, Sceptic, and Pragmatist, and produce a structured "
    "synthesis: a single headline recommendation, the convergence points "
    "all three agreed on, the open disagreements that still need human "
    "review, and a conversational rationale that names which side carried "
    "each major question."
)


def create_rnd_moderator(llm):
    structured = bind_structured(llm, ResearchSynthesis, "R&D Moderator")

    def node(state) -> dict:
        history = state["rnd_debate_state"].get("history", "")
        user = (
            f"## Project: {state['project_name']} — FIFA {state['fifa_category']}\n\n"
            "## Full debate\n"
            + history
            + "\n\nProduce the synthesis now."
        )
        messages = build_simple_messages(_SYSTEM, user)
        rendered = invoke_structured_or_freetext(
            structured, llm, messages, render_research_synthesis, "R&D Moderator"
        )

        # Persist the moderator's verdict in both the debate state and a
        # top-level field so downstream nodes don't have to walk into the
        # nested debate dict.
        debate = state["rnd_debate_state"]
        new_debate = {**debate, "judge_decision": rendered}
        return {"rnd_debate_state": new_debate, "research_synthesis": rendered}

    return node
