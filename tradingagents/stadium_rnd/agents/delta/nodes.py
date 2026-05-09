"""Delta-analysis nodes for the per-partner-solution sub-graph.

Eight steps mirror Phần V §4.2 of the architecture doc:

    1. Solution Classifier       (cheap)
    2. Spec Extractor            (cheap, tool-style)
    3. Compliance Delta          (mid, cached prefix)
    4. Focused R&D Debate        (mid, map-reduce single round)
    5. Integration Risk          (mid)
    6. Budget Delta              (mid)
    7. Future-proof Score        (mid)
    8. Executive Update          (deep, structured DeltaVerdict)
"""

from __future__ import annotations

from tradingagents.agents.utils.structured import (
    bind_structured,
    invoke_structured_or_freetext,
)
from tradingagents.stadium_rnd.agents.prompt_utils import (
    build_cached_messages,
    build_simple_messages,
)
from tradingagents.stadium_rnd.agents.schemas import (
    DeltaVerdict,
    SolutionClassification,
    render_delta_verdict,
)
from tradingagents.stadium_rnd.dataflows import fetch_fifa_reference_bundle


# ---------------------------------------------------------------------------
# 1. Classifier (cheap LLM, structured output)
# ---------------------------------------------------------------------------


def create_classifier(llm):
    structured = bind_structured(llm, SolutionClassification, "Delta Classifier")

    def node(state) -> dict:
        user = (
            f"## Partner solution from {state['partner_name']}\n"
            + state["solution_doc"]
            + "\n\nClassify the solution: which T1..T6 axes does it primarily "
              "target, which axes does it materially impact, and a one-line summary."
        )
        messages = build_simple_messages(
            "You classify partner stadium-tech solutions onto the T1..T6 axes.",
            user,
        )
        if structured is not None:
            try:
                result = structured.invoke(messages)
                return {
                    "classified_axes": [a.value for a in result.primary_axes]
                                      + [a.value for a in result.related_axes],
                    "extracted_spec": result.one_line,
                }
            except Exception:
                pass
        # Free-text fallback
        response = llm.invoke(messages)
        return {"classified_axes": [], "extracted_spec": response.content}

    return node


# ---------------------------------------------------------------------------
# 2. Spec Extractor (cheap, free-text)
# ---------------------------------------------------------------------------


def create_spec_extractor(llm):
    def node(state) -> dict:
        user = (
            "Extract the structured specification from the partner submission "
            "below. Output: KPIs, scope of work, indicative price tier (if "
            "stated), required integrations, certifications claimed.\n\n"
            f"## Partner: {state['partner_name']}\n\n"
            + state["solution_doc"]
        )
        messages = build_simple_messages(
            "You are a technical spec extractor for stadium-tech submissions.",
            user,
        )
        response = llm.invoke(messages)
        return {"extracted_spec": response.content}

    return node


# ---------------------------------------------------------------------------
# 3. Compliance Delta (mid, with cached FIFA + standards_matrix prefix)
# ---------------------------------------------------------------------------


def create_compliance_delta(llm):
    def node(state) -> dict:
        static_prefix = (
            "## FIFA reference bundle\n"
            + fetch_fifa_reference_bundle()
            + "\n\n## Existing project standards matrix\n"
            + state["standards_matrix"]
        )
        fresh = (
            f"## New solution from {state['partner_name']}\n"
            + state["extracted_spec"]
            + "\n\nReturn a delta block listing every clause this solution "
              "newly satisfies, every clause it leaves unsatisfied, and any "
              "regression vs the existing baseline."
        )
        provider = getattr(llm, "_llm_provider", "anthropic")
        messages = build_cached_messages(
            system_text="You produce compliance-delta reports for new partner solutions.",
            static_prefix=static_prefix,
            fresh_text=fresh,
            provider=provider,
        )
        response = llm.invoke(messages)
        return {"compliance_delta": response.content}

    return node


# ---------------------------------------------------------------------------
# 4. Focused R&D Debate (single map-reduce round, mid LLM)
# ---------------------------------------------------------------------------


def create_focused_debate(llm):
    """Map-reduce variant: 3 parallel positions then a 1-paragraph reduce."""

    def node(state) -> dict:
        spec_block = (
            "## Partner: " + state["partner_name"] + "\n"
            + state["extracted_spec"] + "\n\n"
            "## Compliance delta\n" + state["compliance_delta"] + "\n\n"
            "## Existing rolling summary\n" + state.get("rolling_summary", "(none)")
        )

        positions = []
        for role, system in [
            ("Innovator",
             "You are the Innovator. State why adopting this solution accelerates the project."),
            ("Sceptic",
             "You are the Sceptic. State the strongest objections to adopting it."),
            ("Pragmatist",
             "You are the Pragmatist. State what would have to be true for a phased pilot."),
        ]:
            messages = build_simple_messages(system, spec_block)
            resp = llm.invoke(messages)
            positions.append(f"### {role}\n{resp.content}")

        positions_block = "\n\n".join(positions)

        reduce_messages = build_simple_messages(
            "You are the moderator of a partner-solution evaluation. Read the "
            "three independent positions and produce a 1-2 paragraph synthesis "
            "naming convergence and the single most important open question.",
            positions_block,
        )
        synthesis = llm.invoke(reduce_messages).content

        return {
            "focused_debate_log": positions_block + "\n\n## Synthesis\n" + synthesis,
        }

    return node


# ---------------------------------------------------------------------------
# 5. Integration Risk (mid)
# ---------------------------------------------------------------------------


def create_integration_risk(llm):
    def node(state) -> dict:
        static_prefix = (
            "## Existing vendor matrix\n"
            + state["vendor_matrix"]
            + "\n\n## Existing standards matrix\n"
            + state["standards_matrix"]
        )
        fresh = (
            f"## New solution from {state['partner_name']}\n"
            + state["extracted_spec"]
            + "\n\nAssess integration risk versus the existing architecture: "
              "vendor lock-in delta, cyber attack surface delta, "
              "compatibility with adjacent T-axes, retrofit complexity, "
              "and SLA exposure."
        )
        provider = getattr(llm, "_llm_provider", "anthropic")
        messages = build_cached_messages(
            system_text="You assess integration risk for new partner stadium solutions.",
            static_prefix=static_prefix,
            fresh_text=fresh,
            provider=provider,
        )
        response = llm.invoke(messages)
        return {"integration_risk": response.content}

    return node


# ---------------------------------------------------------------------------
# 6. Budget Delta (mid)
# ---------------------------------------------------------------------------


def create_budget_delta(llm):
    def node(state) -> dict:
        user = (
            f"## Partner: {state['partner_name']}\n"
            + state["extracted_spec"]
            + "\n\nProject FIFA category: " + state["fifa_category"] + "\n"
            + "Provide the CapEx delta and OpEx-per-year delta versus the "
              "current baseline (USD), ±20% sensitivity. Cite reasoning briefly."
        )
        messages = build_simple_messages(
            "You produce budget-delta estimates for new partner solutions.",
            user,
        )
        response = llm.invoke(messages)
        return {"budget_delta": response.content}

    return node


# ---------------------------------------------------------------------------
# 7. Future-proof Score (mid)
# ---------------------------------------------------------------------------


def create_future_proof(llm):
    def node(state) -> dict:
        user = (
            f"## Partner: {state['partner_name']}\n"
            + state["extracted_spec"]
            + "\n\nScore the 5-year and 10-year future-proofness of this "
              "solution: open-standard adherence, modularity, refresh cadence, "
              "sunset risk, ability to scale to higher FIFA categories. "
              "Use Low / Medium / High and justify briefly."
        )
        messages = build_simple_messages(
            "You score the future-proofness of stadium tech solutions.",
            user,
        )
        response = llm.invoke(messages)
        return {"future_proof_score": response.content}

    return node


# ---------------------------------------------------------------------------
# 8. Executive Update (deep, structured DeltaVerdict)
# ---------------------------------------------------------------------------


def create_delta_executive(llm):
    structured = bind_structured(llm, DeltaVerdict, "Delta Executive")

    def node(state) -> dict:
        user = (
            f"## Project {state['project_name']} — partner {state['partner_name']}\n\n"
            f"## Spec\n{state['extracted_spec']}\n\n"
            f"## Compliance delta\n{state['compliance_delta']}\n\n"
            f"## Focused debate\n{state['focused_debate_log']}\n\n"
            f"## Integration risk\n{state['integration_risk']}\n\n"
            f"## Budget delta\n{state['budget_delta']}\n\n"
            f"## Future-proof\n{state['future_proof_score']}\n\n"
            "Produce the structured DeltaVerdict now."
        )
        messages = build_simple_messages(
            "You consolidate partner-solution delta analyses into a single "
            "Adopt / Pilot / Hold / Defer / Reject verdict with capex/opex deltas.",
            user,
        )
        rendered = invoke_structured_or_freetext(
            structured, llm, messages, render_delta_verdict, "Delta Executive"
        )
        return {"delta_executive_update": rendered}

    return node
