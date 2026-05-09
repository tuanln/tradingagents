"""LangGraph state definitions for the stadium R&D pipeline.

Two graphs share state shapes:

* ``StadiumState``  — full project pipeline (one-time per project).
* ``DeltaState``    — incremental analysis when a partner submits a new
  solution; reuses cached project artefacts and produces a delta report.
"""

from __future__ import annotations

from typing import Annotated, Optional

from langgraph.graph import MessagesState
from typing_extensions import TypedDict


# ---------------------------------------------------------------------------
# Debate states (mirror TradingAgents' InvestDebateState / RiskDebateState)
# ---------------------------------------------------------------------------


class RnDDebateState(TypedDict):
    """3-way debate between Innovator, Sceptic, Pragmatist."""

    history: Annotated[str, "Combined debate history"]
    innovator_history: Annotated[str, "Innovator's lines"]
    sceptic_history: Annotated[str, "Sceptic's lines"]
    pragmatist_history: Annotated[str, "Pragmatist's lines"]
    latest_speaker: Annotated[str, "Last speaker label (Innovator/Sceptic/Pragmatist)"]
    current_response: Annotated[str, "Most recent argument"]
    judge_decision: Annotated[str, "Final synthesis from the moderator"]
    count: Annotated[int, "Total debate turns so far"]


class RiskDebateState(TypedDict):
    """4-way risk debate: Tech / Financial / Operational / Geopolitical."""

    history: Annotated[str, "Combined risk debate history"]
    tech_history: Annotated[str, "Tech-risk lines"]
    financial_history: Annotated[str, "Financial-risk lines"]
    operational_history: Annotated[str, "Operational-risk lines"]
    geopolitical_history: Annotated[str, "Geopolitical-risk lines"]
    latest_speaker: Annotated[str, "Last speaker label"]
    current_response: Annotated[str, "Most recent risk argument"]
    judge_decision: Annotated[str, "Final risk synthesis"]
    count: Annotated[int, "Total turns so far"]


# ---------------------------------------------------------------------------
# Project-level state
# ---------------------------------------------------------------------------


class StadiumState(MessagesState):
    """Full state for the project-level analysis graph."""

    # Project context
    project_name: Annotated[str, "Stadium project codename"]
    capacity: Annotated[int, "Target seating capacity"]
    fifa_category: Annotated[str, "Target FIFA category, e.g. 'Cat.4'"]
    location_country: Annotated[str, "Country (used for geopolitical/regulatory lens)"]

    # Domain reports (T1..T6)
    connectivity_report: Annotated[str, "T1 — Connectivity & Network"]
    broadcast_report: Annotated[str, "T2 — Broadcast & Media"]
    fan_experience_report: Annotated[str, "T3 — Fan Experience"]
    safety_security_report: Annotated[str, "T4 — Safety & Security"]
    pitch_facility_report: Annotated[str, "T5 — Pitch & Facility"]
    sustainability_report: Annotated[str, "T6 — Sustainability & Energy"]

    # Compliance
    standards_matrix: Annotated[str, "Standards × solutions compliance matrix"]

    # R&D debate
    rnd_debate_state: Annotated[RnDDebateState, "Innovator/Sceptic/Pragmatist debate"]
    research_synthesis: Annotated[str, "Moderator synthesis of the R&D debate"]

    # Vendor mapping
    vendor_matrix: Annotated[str, "Requirements × vendor solutions matrix"]

    # Risk
    risk_debate_state: Annotated[RiskDebateState, "4-way risk debate"]
    risk_assessment: Annotated[str, "Synthesised risk assessment"]

    # Final outputs
    budget_roadmap: Annotated[str, "Structured budget + 5/10y roadmap"]
    executive_report: Annotated[str, "Final white paper + per-axis ratings"]


# ---------------------------------------------------------------------------
# Delta state (per-partner-solution incremental analysis)
# ---------------------------------------------------------------------------


class DeltaState(TypedDict, total=False):
    """State for a single delta-analysis run.

    The PROJECT_STATE artefacts (``standards_matrix``, ``vendor_matrix``,
    rolling executive summary) are passed in as cached references; this
    state holds only the transient delta artefacts.
    """

    # Inputs
    partner_id: str
    partner_name: str
    solution_doc: str  # raw text/markdown of the partner's submission

    # Cached project context (passed in by reference)
    project_name: str
    fifa_category: str
    standards_matrix: str
    vendor_matrix: str
    rolling_summary: str

    # Delta artefacts produced by the sub-graph
    classified_axes: list[str]                # which T1..T6 the solution touches
    extracted_spec: str                        # KPIs, scope, indicative price
    compliance_delta: str                      # pass/fail/unknown vs FIFA/IEC/ISO
    focused_debate_log: str                    # 1-round 3-way map-reduce result
    integration_risk: str                      # vendor lock-in, cyber, compat
    budget_delta: str                          # CapEx/OpEx delta + sensitivity
    future_proof_score: str                    # 5y/10y compatibility
    delta_executive_update: str                # final delta verdict + rating
