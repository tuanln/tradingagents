"""Vendor Mapping Analyst.

Maps the requirements that came out of the R&D debate to real-world
vendors, with pros / cons / indicative pricing / recent case studies /
vendor lock-in level.
"""

from __future__ import annotations

from tradingagents.stadium_rnd.agents.prompt_utils import build_cached_messages
from tradingagents.stadium_rnd.dataflows import fetch_vendor_catalog_chunk


_SYSTEM = (
    "You are the Vendor Mapping Analyst. Given the synthesised research output "
    "and the standards matrix, map the recommended capabilities to real-world "
    "vendors in each technology axis. For every shortlist entry produce: "
    "vendor name, axes covered, pros, cons, indicative price tier, recent "
    "case study, level of vendor lock-in (low/medium/high), and any "
    "geopolitical caveat. Output as a markdown table followed by a short "
    "shortlist recommendation per axis."
)


def create_vendor_mapping_analyst(llm):
    def vendor_node(state) -> dict:
        static_prefix = (
            "## Standards matrix\n"
            + state["standards_matrix"]
            + "\n\n## Research synthesis\n"
            + state["research_synthesis"]
            + "\n\n## Vendor catalog reference\n"
            + fetch_vendor_catalog_chunk("stadium core systems")
        )
        fresh = (
            f"Project {state['project_name']}: produce the vendor mapping now. "
            "Use markdown tables; flag any vendor with sanction or data-sovereignty "
            "exposure for country "
            f"{state['location_country']}."
        )
        provider = getattr(llm, "_llm_provider", "anthropic")
        messages = build_cached_messages(
            system_text=_SYSTEM,
            static_prefix=static_prefix,
            fresh_text=fresh,
            provider=provider,
        )
        response = llm.invoke(messages)
        return {"vendor_matrix": response.content}

    return vendor_node
