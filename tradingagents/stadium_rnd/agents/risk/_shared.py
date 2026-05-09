"""Shared helpers + factory for the 4-way risk debate.

All four agents share the same wiring; only system prompt and history
key differ. We build a single factory that takes the role config so we
keep the 4 agent files trivially small.
"""

from __future__ import annotations

from dataclasses import dataclass

from tradingagents.stadium_rnd.agents.prompt_utils import build_cached_messages


@dataclass(frozen=True)
class RiskRole:
    label: str          # "Tech Risk"
    history_key: str    # "tech_history"
    speaker_tag: str    # "Tech-Risk"
    focus: str          # short brief


def static_risk_prefix(state) -> str:
    """Cache-eligible prefix for every risk-debate turn."""
    return (
        f"## Project\n- {state['project_name']} — FIFA {state['fifa_category']}\n"
        f"- Country: {state['location_country']}\n\n"
        "## Standards matrix\n"
        + state["standards_matrix"]
        + "\n\n## Research synthesis\n"
        + state["research_synthesis"]
        + "\n\n## Vendor matrix\n"
        + state["vendor_matrix"]
    )


def create_risk_node(llm, role: RiskRole):
    system_text = (
        f"You are the **{role.label} Analyst** in a 4-way risk debate "
        "(Tech / Financial / Operational / Geopolitical). "
        "Engage directly with at least one argument from each of the "
        "other three angles, then add your own concerns. Be concrete: "
        "name the failure mode, quantify the impact, name the trigger. "
        f"Your domain focus: {role.focus}"
    )

    def node(state) -> dict:
        debate = state["risk_debate_state"]
        fresh = (
            "## Risk debate so far\n"
            + debate.get("history", "(no prior turns)")
            + "\n\n## Last argument\n"
            + debate.get("current_response", "(begin the debate)")
            + f"\n\nGive your next argument as the {role.label} Analyst now."
        )
        provider = getattr(llm, "_llm_provider", "anthropic")
        messages = build_cached_messages(
            system_text=system_text,
            static_prefix=static_risk_prefix(state),
            fresh_text=fresh,
            provider=provider,
        )
        response = llm.invoke(messages)
        argument = f"{role.speaker_tag}: {response.content}"
        new_state = {
            **debate,
            "history": debate.get("history", "") + "\n" + argument,
            role.history_key: debate.get(role.history_key, "") + "\n" + argument,
            "latest_speaker": role.speaker_tag,
            "current_response": argument,
            "count": debate.get("count", 0) + 1,
        }
        # Preserve all other history keys
        for hk in ("tech_history", "financial_history",
                   "operational_history", "geopolitical_history"):
            if hk != role.history_key:
                new_state[hk] = debate.get(hk, "")
        return {"risk_debate_state": new_state}

    return node


TECH_ROLE = RiskRole(
    label="Tech Risk",
    history_key="tech_history",
    speaker_tag="Tech-Risk",
    focus=(
        "Vendor lock-in, technology obsolescence, integration failure modes, "
        "cyber attack surface, IoT-device exposure, broadcast IP-network "
        "single-points-of-failure on match-day."
    ),
)
FINANCIAL_ROLE = RiskRole(
    label="Financial Risk",
    history_key="financial_history",
    speaker_tag="Financial-Risk",
    focus=(
        "CapEx overrun, FX exposure, interest-rate sensitivity, "
        "ticketing & sponsorship ROI miss, OpEx creep, hidden contract liabilities."
    ),
)
OPERATIONAL_ROLE = RiskRole(
    label="Operational Risk",
    history_key="operational_history",
    speaker_tag="Ops-Risk",
    focus=(
        "Match-day downtime SLA, staffing for stewarding/IT/broadcast, "
        "maintenance contracts, spare-part supply chain, weather and "
        "climate resilience, incident response."
    ),
)
GEOPOLITICAL_ROLE = RiskRole(
    label="Geopolitical/Regulatory Risk",
    history_key="geopolitical_history",
    speaker_tag="Geo-Risk",
    focus=(
        "Sanctions on vendors (e.g. Hikvision exposure), data sovereignty "
        "(GDPR/CCPA/local), biometric law restrictions, FIFA/AFC bid "
        "commitments, local content rules, customs and import duty."
    ),
)
