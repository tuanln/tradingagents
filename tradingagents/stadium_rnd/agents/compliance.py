"""Standards Compliance Analyst.

Reads the 6 domain reports and produces a compliance matrix mapping
each proposed solution to FIFA / IEC / ISO / EN / local-code clauses.
"""

from __future__ import annotations

from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)
from tradingagents.stadium_rnd.agents.prompt_utils import build_cached_messages
from tradingagents.stadium_rnd.agents.schemas import ComplianceMatrix, render_compliance
from tradingagents.stadium_rnd.dataflows import fetch_fifa_reference_bundle


_SYSTEM = (
    "You are the Standards Compliance Analyst. Read all six domain reports "
    "and build a single compliance matrix that maps every proposed solution "
    "to the relevant clause of FIFA Stadium Guidelines, FIFA Quality "
    "Programme, IEC 60364, IEC 62305, EN 50132 / IEC 62676, ISO 14001, "
    "ISO 27001, ISO 20121, IBC/IFC, and the country-specific building/fire "
    "code. For every row, mark Status as Pass / Fail / Gap / Unknown."
)


def _combined_reports(state) -> str:
    return (
        "## T1 — Connectivity\n" + state["connectivity_report"] + "\n\n"
        "## T2 — Broadcast\n" + state["broadcast_report"] + "\n\n"
        "## T3 — Fan Experience\n" + state["fan_experience_report"] + "\n\n"
        "## T4 — Safety & Security\n" + state["safety_security_report"] + "\n\n"
        "## T5 — Pitch & Facility\n" + state["pitch_facility_report"] + "\n\n"
        "## T6 — Sustainability\n" + state["sustainability_report"]
    )


def create_compliance_analyst(llm):
    structured = bind_structured(llm, ComplianceMatrix, "Compliance Analyst")

    def compliance_node(state) -> dict:
        static_prefix = (
            "## FIFA reference bundle\n"
            + fetch_fifa_reference_bundle()
            + "\n\n## Domain reports\n\n"
            + _combined_reports(state)
        )
        project_line = (
            f"Project {state['project_name']} — FIFA {state['fifa_category']}, "
            f"capacity {state['capacity']:,}, country {state['location_country']}."
        )
        fresh = (
            project_line
            + "\n\nProduce the compliance matrix now. Use the schema fields exactly."
        )
        provider = getattr(llm, "_llm_provider", "anthropic")
        messages = build_cached_messages(
            system_text=_SYSTEM,
            static_prefix=static_prefix,
            fresh_text=fresh,
            provider=provider,
        )
        rendered = invoke_structured_or_freetext(
            structured, llm, messages, render_compliance, "Compliance Analyst"
        )
        return {"standards_matrix": rendered}

    return compliance_node
