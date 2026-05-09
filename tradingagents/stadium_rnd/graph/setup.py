"""LangGraph setup for the stadium R&D pipeline.

Topology:

  START
    └─ Domain Analysts (T1..T6 in sequence — could be parallel via fan-out)
       └─ Compliance Analyst
          └─ R&D Debate (Innovator ↔ Sceptic ↔ Pragmatist, rotating)
             └─ R&D Moderator
                └─ Vendor Mapping
                   └─ Risk Debate (Tech ↔ Financial ↔ Operational ↔ Geopolitical)
                      └─ Risk Synthesizer
                         └─ Budget & Roadmap Manager
                            └─ Executive Editor
                               └─ END
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from tradingagents.stadium_rnd.agents import (
    create_compliance_analyst,
    create_innovator,
    create_sceptic,
    create_pragmatist,
    create_vendor_mapping_analyst,
    create_tech_risk_analyst,
    create_financial_risk_analyst,
    create_operational_risk_analyst,
    create_geopolitical_risk_analyst,
    create_budget_roadmap_manager,
    create_executive_editor,
    DOMAIN_AXES,
    create_domain_analyst,
)
from tradingagents.stadium_rnd.agents.debate.moderator import create_rnd_moderator
from tradingagents.stadium_rnd.agents.risk.synthesizer import create_risk_synthesizer
from tradingagents.stadium_rnd.agents.states import StadiumState
from tradingagents.stadium_rnd.graph.conditional_logic import ConditionalLogic


class GraphSetup:
    def __init__(
        self,
        cheap_llm: Any,
        mid_llm: Any,
        deep_llm: Any,
        conditional_logic: ConditionalLogic,
    ):
        self.cheap_llm = cheap_llm   # domain analysts, summarisation
        self.mid_llm = mid_llm       # compliance, debate, vendor, risk
        self.deep_llm = deep_llm     # synthesizers, managers, editor
        self.cl = conditional_logic

    def build(self) -> StateGraph:
        wf = StateGraph(StadiumState)

        # ---- Domain analysts (T1..T6)
        for axis in DOMAIN_AXES:
            wf.add_node(
                f"{axis.label} Analyst",
                create_domain_analyst(self.cheap_llm, axis),
            )

        wf.add_node("Compliance Analyst", create_compliance_analyst(self.mid_llm))

        # ---- R&D debate
        wf.add_node("Innovator", create_innovator(self.mid_llm))
        wf.add_node("Sceptic", create_sceptic(self.mid_llm))
        wf.add_node("Pragmatist", create_pragmatist(self.mid_llm))
        wf.add_node("R&D Moderator", create_rnd_moderator(self.deep_llm))

        # ---- Vendor + risk
        wf.add_node("Vendor Mapping", create_vendor_mapping_analyst(self.mid_llm))
        wf.add_node("Tech-Risk Analyst", create_tech_risk_analyst(self.mid_llm))
        wf.add_node("Financial-Risk Analyst", create_financial_risk_analyst(self.mid_llm))
        wf.add_node("Operational-Risk Analyst", create_operational_risk_analyst(self.mid_llm))
        wf.add_node("Geopolitical-Risk Analyst", create_geopolitical_risk_analyst(self.mid_llm))
        wf.add_node("Risk Synthesizer", create_risk_synthesizer(self.deep_llm))

        # ---- Final managers
        wf.add_node("Budget & Roadmap Manager", create_budget_roadmap_manager(self.deep_llm))
        wf.add_node("Executive Editor", create_executive_editor(self.deep_llm))

        # -------------------- edges --------------------
        # START → domain analysts in sequence (sequential is simplest;
        # they could be fanned out in parallel later for latency).
        wf.add_edge(START, f"{DOMAIN_AXES[0].label} Analyst")
        for i, axis in enumerate(DOMAIN_AXES[:-1]):
            nxt = DOMAIN_AXES[i + 1]
            wf.add_edge(f"{axis.label} Analyst", f"{nxt.label} Analyst")
        wf.add_edge(f"{DOMAIN_AXES[-1].label} Analyst", "Compliance Analyst")

        # Compliance → R&D debate (start with Innovator)
        wf.add_edge("Compliance Analyst", "Innovator")

        # R&D debate rotation
        wf.add_conditional_edges(
            "Innovator", self.cl.should_continue_rnd,
            {"Sceptic": "Sceptic", "R&D Moderator": "R&D Moderator"},
        )
        wf.add_conditional_edges(
            "Sceptic", self.cl.should_continue_rnd,
            {"Pragmatist": "Pragmatist", "R&D Moderator": "R&D Moderator"},
        )
        wf.add_conditional_edges(
            "Pragmatist", self.cl.should_continue_rnd,
            {"Innovator": "Innovator", "R&D Moderator": "R&D Moderator"},
        )

        # Moderator → vendor → risk debate
        wf.add_edge("R&D Moderator", "Vendor Mapping")
        wf.add_edge("Vendor Mapping", "Tech-Risk Analyst")

        # Risk debate rotation
        wf.add_conditional_edges(
            "Tech-Risk Analyst", self.cl.should_continue_risk,
            {
                "Financial-Risk Analyst": "Financial-Risk Analyst",
                "Risk Synthesizer": "Risk Synthesizer",
            },
        )
        wf.add_conditional_edges(
            "Financial-Risk Analyst", self.cl.should_continue_risk,
            {
                "Operational-Risk Analyst": "Operational-Risk Analyst",
                "Risk Synthesizer": "Risk Synthesizer",
            },
        )
        wf.add_conditional_edges(
            "Operational-Risk Analyst", self.cl.should_continue_risk,
            {
                "Geopolitical-Risk Analyst": "Geopolitical-Risk Analyst",
                "Risk Synthesizer": "Risk Synthesizer",
            },
        )
        wf.add_conditional_edges(
            "Geopolitical-Risk Analyst", self.cl.should_continue_risk,
            {
                "Tech-Risk Analyst": "Tech-Risk Analyst",
                "Risk Synthesizer": "Risk Synthesizer",
            },
        )

        # Risk synth → budget → editor → end
        wf.add_edge("Risk Synthesizer", "Budget & Roadmap Manager")
        wf.add_edge("Budget & Roadmap Manager", "Executive Editor")
        wf.add_edge("Executive Editor", END)

        return wf
