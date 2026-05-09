"""Domain analyst factory.

One factory, six axes (T1..T6). Each domain analyst:
  - Reads the axis-specific reference + the FIFA reference bundle (cached).
  - Reads the project context.
  - Produces a markdown report with a "State of the Art / FIFA requirement /
    Gap" table at the end (mirrors fundamentals_analyst's pattern).

The output is written to the appropriate state field (e.g.
``connectivity_report``).
"""

from __future__ import annotations

from dataclasses import dataclass

from tradingagents.stadium_rnd.agents.prompt_utils import build_cached_messages
from tradingagents.stadium_rnd.dataflows import (
    fetch_axis_reference,
    fetch_fifa_reference_bundle,
)


@dataclass(frozen=True)
class DomainAxis:
    key: str               # "T1_Connectivity"
    label: str             # "Connectivity & Network"
    state_field: str       # "connectivity_report"
    focus_areas: str       # short prompt fragment


DOMAIN_AXES: list[DomainAxis] = [
    DomainAxis(
        key="T1_Connectivity",
        label="Connectivity & Network",
        state_field="connectivity_report",
        focus_areas=(
            "Wi-Fi 6E/7 capacity for full-stadium concurrent users, neutral-host "
            "DAS, 5G in-stadium with network slicing, fiber backbone resilience, "
            "match-day uptime SLA."
        ),
    ),
    DomainAxis(
        key="T2_Broadcast",
        label="Broadcast & Media",
        state_field="broadcast_report",
        focus_areas=(
            "SMPTE 2110 IP production, 4K/8K HDR camera positions, VAR / "
            "goal-line tech, EVS-style replay, multilingual commentary "
            "feeds, broadcast cabling redundancy."
        ),
    ),
    DomainAxis(
        key="T3_FanExperience",
        label="Fan Experience",
        state_field="fan_experience_report",
        focus_areas=(
            "Mobile app (ticketing, wayfinding, F&B order-ahead), AR overlays, "
            "cashless concessions, NFC/biometric access, accessibility, "
            "second-screen replays, loyalty/CRM integration."
        ),
    ),
    DomainAxis(
        key="T4_SafetySecurity",
        label="Safety & Security",
        state_field="safety_security_report",
        focus_areas=(
            "CCTV with AI crowd analytics, access control, BMS integrated with "
            "fire-suppression, drone defence (RF detection), incident command "
            "centre, FIFA stewarding ratios, evacuation planning."
        ),
    ),
    DomainAxis(
        key="T5_PitchFacility",
        label="Pitch & Facility",
        state_field="pitch_facility_report",
        focus_areas=(
            "Hybrid grass (SISGrass/Desso), pitch heating + irrigation, FIFA "
            "Quality Pro LED lighting (Class A 2000+ lux horizontal, 3500 lux "
            "vertical for HDR), tunnels and warm-up rooms, accessibility paths."
        ),
    ),
    DomainAxis(
        key="T6_Sustainability",
        label="Sustainability & Energy",
        state_field="sustainability_report",
        focus_areas=(
            "Solar canopy sizing, BESS for match-day peak shaving, water reuse "
            "for irrigation, BREEAM/LEED targets, scope 1+2 carbon accounting, "
            "EV charging readiness, end-of-life material recovery."
        ),
    ),
]


def _system_prompt(axis: DomainAxis) -> str:
    return (
        f"You are the **{axis.label} Analyst** on a stadium R&D team. "
        f"Your axis ID is {axis.key}. "
        "Produce a comprehensive markdown report on the state of the art for "
        "this axis applied to a FIFA-grade smart stadium. Cover: technologies, "
        "leading vendors and case studies, KPIs to hit, required cabling/IT "
        "infrastructure, and explicit FIFA / IEC / ISO / EN compliance "
        "touchpoints. End the report with a markdown table whose columns are: "
        "**State of the Art | FIFA requirement | Gap | Risk if unaddressed**.\n\n"
        f"Focus areas: {axis.focus_areas}"
    )


def create_domain_analyst(llm, axis: DomainAxis):
    """Build a LangGraph node for the given domain axis."""

    def domain_node(state) -> dict:
        project_context = (
            f"# Project context\n"
            f"- Project: {state['project_name']}\n"
            f"- FIFA category: {state['fifa_category']}\n"
            f"- Capacity: {state['capacity']:,}\n"
            f"- Country: {state['location_country']}\n"
        )

        # Static prefix (cache-eligible): FIFA bundle + axis reference.
        static_prefix = (
            "## FIFA reference bundle\n"
            + fetch_fifa_reference_bundle()
            + "\n\n## Axis reference\n"
            + fetch_axis_reference(axis.key)
            + "\n\n"
            + project_context
        )

        # Fresh content: the immediate ask.
        fresh = (
            "Write the comprehensive report now, in markdown, ending with the "
            "required table. Be specific and cite the FIFA / IEC / ISO / EN "
            "section numbers when relevant."
        )

        provider = getattr(llm, "_llm_provider", "anthropic")
        messages = build_cached_messages(
            system_text=_system_prompt(axis),
            static_prefix=static_prefix,
            fresh_text=fresh,
            provider=provider,
        )
        response = llm.invoke(messages)
        return {axis.state_field: response.content}

    return domain_node
