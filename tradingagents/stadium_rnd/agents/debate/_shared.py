"""Shared helpers for the 3-way R&D debate (Innovator / Sceptic / Pragmatist).

Each debate node consumes the cached domain reports + standards matrix as
the static prefix, and only the fresh debate history + last argument as
the uncached fresh chunk — this is the key cost-saver per Phần V of the
architecture doc.
"""

from __future__ import annotations

from tradingagents.stadium_rnd.agents.prompt_utils import build_cached_messages


def static_research_prefix(state) -> str:
    """The cache-eligible prefix used by every debate turn."""
    return (
        "## Project\n"
        f"- Name: {state['project_name']}\n"
        f"- FIFA: {state['fifa_category']}\n"
        f"- Capacity: {state['capacity']:,}\n"
        f"- Country: {state['location_country']}\n\n"
        "## Standards matrix\n"
        + state["standards_matrix"]
        + "\n\n## Domain report summaries\n"
        + "### T1 Connectivity\n" + _truncate(state["connectivity_report"]) + "\n\n"
        + "### T2 Broadcast\n" + _truncate(state["broadcast_report"]) + "\n\n"
        + "### T3 Fan Experience\n" + _truncate(state["fan_experience_report"]) + "\n\n"
        + "### T4 Safety & Security\n" + _truncate(state["safety_security_report"]) + "\n\n"
        + "### T5 Pitch & Facility\n" + _truncate(state["pitch_facility_report"]) + "\n\n"
        + "### T6 Sustainability\n" + _truncate(state["sustainability_report"])
    )


def _truncate(report: str, max_chars: int = 2500) -> str:
    """Trim a single domain report; fulltext stays in state for retrieval."""
    if len(report) <= max_chars:
        return report
    return report[:max_chars] + "\n…[truncated; call fetch_full_report for details]"


def build_debate_messages(*, system_text: str, state, fresh_text: str, llm):
    static_prefix = static_research_prefix(state)
    provider = getattr(llm, "_llm_provider", "anthropic")
    return build_cached_messages(
        system_text=system_text,
        static_prefix=static_prefix,
        fresh_text=fresh_text,
        provider=provider,
    )
