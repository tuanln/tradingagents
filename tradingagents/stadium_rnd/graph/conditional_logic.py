"""Conditional routing for the R&D and risk debates.

Mirrors ``tradingagents/graph/conditional_logic.py``: count debate turns
and rotate speakers, then hand off to the moderator/synthesiser when the
configured round budget is consumed.
"""

from __future__ import annotations


class ConditionalLogic:
    def __init__(
        self,
        max_rnd_rounds: int = 1,
        max_risk_rounds: int = 1,
    ):
        self.max_rnd_rounds = max_rnd_rounds
        self.max_risk_rounds = max_risk_rounds

    # ----- R&D debate (3 speakers, rotation: Innovator → Sceptic → Pragmatist)
    def should_continue_rnd(self, state) -> str:
        debate = state["rnd_debate_state"]
        # 3 speakers × N rounds = max turns
        if debate["count"] >= 3 * self.max_rnd_rounds:
            return "R&D Moderator"
        last = debate.get("latest_speaker", "")
        if last == "Innovator":
            return "Sceptic"
        if last == "Sceptic":
            return "Pragmatist"
        return "Innovator"

    # ----- Risk debate (4 speakers, rotation: Tech → Financial → Operational → Geopolitical)
    def should_continue_risk(self, state) -> str:
        debate = state["risk_debate_state"]
        if debate["count"] >= 4 * self.max_risk_rounds:
            return "Risk Synthesizer"
        last = debate.get("latest_speaker", "")
        if last == "Tech-Risk":
            return "Financial-Risk Analyst"
        if last == "Financial-Risk":
            return "Operational-Risk Analyst"
        if last == "Ops-Risk":
            return "Geopolitical-Risk Analyst"
        return "Tech-Risk Analyst"
