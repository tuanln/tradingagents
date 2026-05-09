"""Pydantic schemas for structured-output agents in the stadium R&D pipeline.

Mirrors ``tradingagents/agents/schemas.py``: schema field descriptions
double as the model's output instructions, and a ``render_*`` helper
turns the parsed instance back into the markdown shape consumed
downstream (state, audit log, executive report).
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared enums
# ---------------------------------------------------------------------------


class AdoptionRating(str, Enum):
    """5-tier rating for stadium-tech adoption decisions."""

    ADOPT = "Adopt"
    PILOT = "Pilot"
    HOLD = "Hold"
    DEFER = "Defer"
    REJECT = "Reject"


class DomainAxis(str, Enum):
    T1_CONNECTIVITY = "T1_Connectivity"
    T2_BROADCAST = "T2_Broadcast"
    T3_FAN_EXPERIENCE = "T3_FanExperience"
    T4_SAFETY_SECURITY = "T4_SafetySecurity"
    T5_PITCH_FACILITY = "T5_PitchFacility"
    T6_SUSTAINABILITY = "T6_Sustainability"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ---------------------------------------------------------------------------
# Compliance
# ---------------------------------------------------------------------------


class ComplianceMatrix(BaseModel):
    """Standards × solutions compliance assessment."""

    summary: str = Field(
        description="One-paragraph executive summary of the project's overall standards posture.",
    )
    matrix_markdown: str = Field(
        description=(
            "Markdown table with columns: Standard | Section | T-axis | Solution | "
            "Status (Pass/Fail/Gap/Unknown) | Notes. Cover FIFA Stadium Guidelines, "
            "FIFA Quality Programme, IEC 60364, EN 50132, ISO 14001, ISO 27001, ISO 20121, "
            "and any local building/fire codes flagged in the project context."
        ),
    )
    open_gaps: list[str] = Field(
        description="Bulletised list of unresolved gaps that must be closed before FIFA inspection.",
    )


def render_compliance(c: ComplianceMatrix) -> str:
    parts = [f"**Summary**: {c.summary}", "", c.matrix_markdown]
    if c.open_gaps:
        parts.extend(["", "**Open Gaps**:"])
        parts.extend(f"- {g}" for g in c.open_gaps)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# R&D synthesis (moderator output of the 3-way debate)
# ---------------------------------------------------------------------------


class ResearchSynthesis(BaseModel):
    """Moderator's synthesis of the Innovator/Sceptic/Pragmatist debate."""

    headline_recommendation: str = Field(
        description="Single-sentence recommendation that tells the budget manager what to plan for.",
    )
    convergence_points: list[str] = Field(
        description="Items where all three debaters agreed.",
    )
    open_disagreements: list[str] = Field(
        description="Material disagreements that remain unresolved; flag for human review.",
    )
    rationale: str = Field(
        description=(
            "Conversational summary referencing which side of the debate carried "
            "each major question. Speak naturally."
        ),
    )


def render_research_synthesis(r: ResearchSynthesis) -> str:
    parts = [
        f"**Headline**: {r.headline_recommendation}",
        "",
        f"**Rationale**: {r.rationale}",
    ]
    if r.convergence_points:
        parts.extend(["", "**Convergence**:"])
        parts.extend(f"- {x}" for x in r.convergence_points)
    if r.open_disagreements:
        parts.extend(["", "**Open Disagreements**:"])
        parts.extend(f"- {x}" for x in r.open_disagreements)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Risk synthesis
# ---------------------------------------------------------------------------


class RiskAssessment(BaseModel):
    """Synthesised risk assessment after the 4-way debate."""

    top_risks: list[str] = Field(
        description="Up to 8 most material risks across tech / financial / operational / geopolitical.",
    )
    mitigations: list[str] = Field(
        description="One-line mitigation per top risk, in the same order.",
    )
    residual_risk: str = Field(
        description="One-paragraph summary of residual risk after mitigations.",
    )
    overall_risk_level: ConfidenceLevel = Field(
        description="Overall residual-risk level after mitigations.",
    )


def render_risk(r: RiskAssessment) -> str:
    parts = ["**Top Risks** (with mitigation):"]
    for risk, mit in zip(r.top_risks, r.mitigations):
        parts.append(f"- {risk}\n  - *Mitigation*: {mit}")
    parts.extend([
        "",
        f"**Residual**: {r.residual_risk}",
        f"**Overall Risk Level**: {r.overall_risk_level.value}",
    ])
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Budget & roadmap
# ---------------------------------------------------------------------------


class RoadmapPhase(BaseModel):
    name: str = Field(description="Phase name, e.g. 'Phase 1 — connectivity backbone'.")
    duration_months: int = Field(description="Expected duration in months.")
    capex_usd: float = Field(description="CapEx for this phase in USD.")
    gating_criteria: str = Field(description="What must be true to exit this phase.")


class StadiumBudgetPlan(BaseModel):
    """Structured budget + roadmap output."""

    capex_breakdown_usd: dict[str, float] = Field(
        description=(
            "Mapping of T-axis (T1..T6) to CapEx in USD. Use the project's "
            "category and capacity to size the figures."
        ),
    )
    opex_yearly_usd: dict[str, float] = Field(
        description="Mapping of category (e.g. 'broadcast', 'security') to annual OpEx in USD.",
    )
    capex_total_low: float = Field(description="Lower bound of CapEx range, USD.")
    capex_total_high: float = Field(description="Upper bound of CapEx range, USD.")
    payback_years: Optional[float] = Field(
        default=None,
        description="Payback period in years; null if not applicable.",
    )
    roadmap_phases: list[RoadmapPhase] = Field(
        description="Ordered phases, ideally 3-5, each with gating criteria.",
    )
    scaling_5y: str = Field(description="Expected scaling and refresh in 5 years.")
    scaling_10y: str = Field(description="Expected scaling and refresh in 10 years.")
    confidence: ConfidenceLevel = Field(description="Confidence in these figures.")


def render_budget(b: StadiumBudgetPlan) -> str:
    parts = ["**CapEx breakdown (USD)**:"]
    parts.extend(f"- {k}: {v:,.0f}" for k, v in b.capex_breakdown_usd.items())
    parts.append(
        f"**CapEx range**: {b.capex_total_low:,.0f} – {b.capex_total_high:,.0f} USD"
    )
    parts.append("")
    parts.append("**OpEx / year (USD)**:")
    parts.extend(f"- {k}: {v:,.0f}" for k, v in b.opex_yearly_usd.items())
    if b.payback_years is not None:
        parts.append(f"**Payback**: {b.payback_years:.1f} years")
    parts.append("")
    parts.append("**Roadmap phases**:")
    for p in b.roadmap_phases:
        parts.append(
            f"- *{p.name}* — {p.duration_months} months, "
            f"{p.capex_usd:,.0f} USD; gate: {p.gating_criteria}"
        )
    parts.extend([
        "",
        f"**Scaling 5y**: {b.scaling_5y}",
        f"**Scaling 10y**: {b.scaling_10y}",
        f"**Confidence**: {b.confidence.value}",
    ])
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Executive report
# ---------------------------------------------------------------------------


class AxisVerdict(BaseModel):
    axis: DomainAxis = Field(description="Which technology axis this verdict is for.")
    rating: AdoptionRating = Field(description="Adopt / Pilot / Hold / Defer / Reject.")
    headline: str = Field(description="One-sentence headline for the axis.")
    dependencies: list[DomainAxis] = Field(
        default_factory=list,
        description="Other axes this verdict depends on.",
    )


class ExecutiveReport(BaseModel):
    """Final consolidated white-paper output."""

    executive_summary: str = Field(description="2-4 sentence executive summary.")
    axis_verdicts: list[AxisVerdict] = Field(
        description="One verdict per T1..T6, even if Defer/Reject.",
    )
    investment_thesis: str = Field(
        description="Detailed reasoning anchored in the debate + risk + budget outputs.",
    )
    open_questions_for_steering_committee: list[str] = Field(
        description="Questions the steering committee must resolve before signoff.",
    )


def render_executive(e: ExecutiveReport) -> str:
    parts = [f"**Executive Summary**: {e.executive_summary}", "", "**Per-axis verdicts**:"]
    for v in e.axis_verdicts:
        deps = (
            f" (depends on: {', '.join(d.value for d in v.dependencies)})"
            if v.dependencies else ""
        )
        parts.append(f"- **{v.axis.value}** — *{v.rating.value}*: {v.headline}{deps}")
    parts.extend(["", f"**Investment Thesis**: {e.investment_thesis}"])
    if e.open_questions_for_steering_committee:
        parts.extend(["", "**Open questions for steering committee**:"])
        parts.extend(f"- {q}" for q in e.open_questions_for_steering_committee)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Delta-analysis schemas (per partner solution)
# ---------------------------------------------------------------------------


class SolutionClassification(BaseModel):
    primary_axes: list[DomainAxis] = Field(
        description="Axes the solution primarily targets.",
    )
    related_axes: list[DomainAxis] = Field(
        default_factory=list,
        description="Axes the solution materially impacts but does not target.",
    )
    one_line: str = Field(description="One-line summary of what the solution does.")


class DeltaVerdict(BaseModel):
    rating: AdoptionRating = Field(description="Adopt / Pilot / Hold / Defer / Reject.")
    headline: str = Field(description="One-sentence verdict headline.")
    capex_delta_usd: float = Field(
        description="CapEx delta versus the current baseline plan (USD; negative = savings)."
    )
    opex_delta_usd_per_year: float = Field(
        description="OpEx-per-year delta versus baseline (USD)."
    )
    integration_risk: ConfidenceLevel = Field(
        description="Integration risk level given the existing architecture."
    )
    future_proof_5y: ConfidenceLevel = Field(
        description="How well the solution holds up over a 5-year horizon."
    )
    rationale: str = Field(description="2-4 sentence rationale.")
    must_resolve: list[str] = Field(
        default_factory=list,
        description="Open issues that must be resolved before adoption.",
    )


def render_delta_verdict(d: DeltaVerdict) -> str:
    parts = [
        f"**Verdict**: {d.rating.value} — {d.headline}",
        "",
        f"**CapEx delta**: {d.capex_delta_usd:+,.0f} USD",
        f"**OpEx Δ/year**: {d.opex_delta_usd_per_year:+,.0f} USD",
        f"**Integration risk**: {d.integration_risk.value}",
        f"**5-year future-proof**: {d.future_proof_5y.value}",
        "",
        f"**Rationale**: {d.rationale}",
    ]
    if d.must_resolve:
        parts.extend(["", "**Must resolve**:"])
        parts.extend(f"- {x}" for x in d.must_resolve)
    return "\n".join(parts)
