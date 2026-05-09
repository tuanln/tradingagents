"""Risk Synthesizer — collapses the 4-way risk debate into a structured assessment."""

from __future__ import annotations

from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)
from tradingagents.stadium_rnd.agents.prompt_utils import build_simple_messages
from tradingagents.stadium_rnd.agents.schemas import RiskAssessment, render_risk


_SYSTEM = (
    "You are the Risk Synthesizer. Read the 4-way risk debate (Tech, "
    "Financial, Operational, Geopolitical) and produce a single structured "
    "risk assessment: top risks, one-line mitigations in matching order, "
    "residual risk paragraph, and an overall residual-risk level."
)


def create_risk_synthesizer(llm):
    structured = bind_structured(llm, RiskAssessment, "Risk Synthesizer")

    def node(state) -> dict:
        history = state["risk_debate_state"].get("history", "")
        user = (
            f"## Project: {state['project_name']} — FIFA {state['fifa_category']}\n\n"
            "## Risk debate transcript\n"
            + history
            + "\n\nProduce the structured risk assessment now."
        )
        messages = build_simple_messages(_SYSTEM, user)
        rendered = invoke_structured_or_freetext(
            structured, llm, messages, render_risk, "Risk Synthesizer"
        )
        debate = state["risk_debate_state"]
        new_debate = {**debate, "judge_decision": rendered}
        return {"risk_debate_state": new_debate, "risk_assessment": rendered}

    return node
