"""High-level orchestrator for the stadium R&D pipeline.

Mirrors ``tradingagents/graph/trading_graph.py`` but with three model
tiers (cheap / mid / deep) so domain analysts, debate, and managers
each route to the right cost/quality point. See ``docs/architecture.md``
Phần V §3.4 for the rationale.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from tradingagents.dataflows.config import set_config
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.llm_clients import create_llm_client
from tradingagents.stadium_rnd.agents.states import (
    RnDDebateState,
    RiskDebateState,
)
from tradingagents.stadium_rnd.graph.conditional_logic import ConditionalLogic
from tradingagents.stadium_rnd.graph.setup import GraphSetup

logger = logging.getLogger(__name__)


def _empty_rnd_debate() -> RnDDebateState:
    return {
        "history": "",
        "innovator_history": "",
        "sceptic_history": "",
        "pragmatist_history": "",
        "latest_speaker": "",
        "current_response": "",
        "judge_decision": "",
        "count": 0,
    }


def _empty_risk_debate() -> RiskDebateState:
    return {
        "history": "",
        "tech_history": "",
        "financial_history": "",
        "operational_history": "",
        "geopolitical_history": "",
        "latest_speaker": "",
        "current_response": "",
        "judge_decision": "",
        "count": 0,
    }


class StadiumRnDGraph:
    """Run the full project-level analysis for a stadium project.

    Tier mapping
    ------------
    - cheap:  ``stadium_rnd.cheap_llm``  (default: claude-haiku-4-5)
    - mid:    ``stadium_rnd.mid_llm``    (default: claude-sonnet-4-6)
    - deep:   ``stadium_rnd.deep_llm``   (default: claude-opus-4-7)

    Override either by setting the matching keys in ``config``.
    """

    def __init__(
        self,
        config: Optional[dict[str, Any]] = None,
        max_rnd_rounds: int = 1,
        max_risk_rounds: int = 1,
    ):
        self.config = config or DEFAULT_CONFIG.copy()
        set_config(self.config)
        os.makedirs(self.config["results_dir"], exist_ok=True)

        provider = self.config.get("llm_provider", "anthropic")
        cheap_model = self.config.get("stadium_rnd.cheap_llm", "claude-haiku-4-5")
        mid_model = self.config.get("stadium_rnd.mid_llm", "claude-sonnet-4-6")
        deep_model = self.config.get("stadium_rnd.deep_llm", "claude-opus-4-7")

        cheap_client = create_llm_client(
            provider=provider, model=cheap_model,
            base_url=self.config.get("backend_url"),
        )
        mid_client = create_llm_client(
            provider=provider, model=mid_model,
            base_url=self.config.get("backend_url"),
        )
        deep_client = create_llm_client(
            provider=provider, model=deep_model,
            base_url=self.config.get("backend_url"),
        )

        self.cheap_llm = cheap_client.get_llm()
        self.mid_llm = mid_client.get_llm()
        self.deep_llm = deep_client.get_llm()

        # Tag the LLM with its provider for prompt-cache decisions.
        for llm in (self.cheap_llm, self.mid_llm, self.deep_llm):
            try:
                setattr(llm, "_llm_provider", provider)
            except Exception:
                pass  # some wrappers reject extra attrs; cache will fall back

        self.cl = ConditionalLogic(
            max_rnd_rounds=max_rnd_rounds,
            max_risk_rounds=max_risk_rounds,
        )
        workflow = GraphSetup(
            cheap_llm=self.cheap_llm,
            mid_llm=self.mid_llm,
            deep_llm=self.deep_llm,
            conditional_logic=self.cl,
        ).build()
        self.graph = workflow.compile()

    def analyse(
        self,
        project_name: str,
        capacity: int,
        fifa_category: str,
        location_country: str,
    ) -> dict[str, Any]:
        """Run the full pipeline once for a project."""
        init_state: dict[str, Any] = {
            "messages": [],
            "project_name": project_name,
            "capacity": capacity,
            "fifa_category": fifa_category,
            "location_country": location_country,
            # Reports start empty — domain analysts fill them.
            "connectivity_report": "",
            "broadcast_report": "",
            "fan_experience_report": "",
            "safety_security_report": "",
            "pitch_facility_report": "",
            "sustainability_report": "",
            "standards_matrix": "",
            "rnd_debate_state": _empty_rnd_debate(),
            "research_synthesis": "",
            "vendor_matrix": "",
            "risk_debate_state": _empty_risk_debate(),
            "risk_assessment": "",
            "budget_roadmap": "",
            "executive_report": "",
        }
        final_state = self.graph.invoke(init_state)
        self._dump(project_name, final_state)
        return final_state

    def _dump(self, project_name: str, state: dict[str, Any]) -> None:
        out_dir = Path(self.config["results_dir"]) / "stadium_rnd" / project_name
        out_dir.mkdir(parents=True, exist_ok=True)
        slim = {
            k: state.get(k)
            for k in [
                "project_name", "capacity", "fifa_category", "location_country",
                "connectivity_report", "broadcast_report",
                "fan_experience_report", "safety_security_report",
                "pitch_facility_report", "sustainability_report",
                "standards_matrix", "research_synthesis",
                "vendor_matrix", "risk_assessment",
                "budget_roadmap", "executive_report",
            ]
        }
        slim["rnd_debate_history"] = state.get("rnd_debate_state", {}).get("history", "")
        slim["risk_debate_history"] = state.get("risk_debate_state", {}).get("history", "")
        with (out_dir / "project_state.json").open("w", encoding="utf-8") as f:
            json.dump(slim, f, indent=2, ensure_ascii=False)
        with (out_dir / "executive_report.md").open("w", encoding="utf-8") as f:
            f.write(state.get("executive_report", ""))
        logger.info("Wrote stadium R&D outputs to %s", out_dir)
