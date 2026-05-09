"""Delta-analysis sub-graph for incremental partner-solution evaluation.

Reuses cached PROJECT_STATE artefacts (standards_matrix, vendor_matrix,
rolling_summary) and runs an 8-step pipeline producing a DeltaVerdict
without re-executing the full project pipeline. See ``docs/architecture.md``
Phần V §4 for cost analysis.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from langgraph.graph import END, START, StateGraph

from tradingagents.dataflows.config import set_config
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.llm_clients import create_llm_client
from tradingagents.stadium_rnd.agents.delta.nodes import (
    create_budget_delta,
    create_classifier,
    create_compliance_delta,
    create_delta_executive,
    create_focused_debate,
    create_future_proof,
    create_integration_risk,
    create_spec_extractor,
)
from tradingagents.stadium_rnd.agents.states import DeltaState

logger = logging.getLogger(__name__)


class StadiumDeltaGraph:
    """Run the incremental delta-analysis sub-graph for one partner solution.

    Typical usage::

        delta = StadiumDeltaGraph(config=cfg).analyse(
            project_state=cached_project_state,
            partner_id="cisco-2026-q1",
            partner_name="Cisco",
            solution_doc=submitted_text,
        )
        print(delta["delta_executive_update"])
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or DEFAULT_CONFIG.copy()
        set_config(self.config)

        provider = self.config.get("llm_provider", "anthropic")
        cheap_model = self.config.get("stadium_rnd.cheap_llm", "claude-haiku-4-5")
        mid_model = self.config.get("stadium_rnd.mid_llm", "claude-sonnet-4-6")
        deep_model = self.config.get("stadium_rnd.deep_llm", "claude-opus-4-7")

        self.cheap_llm = create_llm_client(
            provider=provider, model=cheap_model,
            base_url=self.config.get("backend_url"),
        ).get_llm()
        self.mid_llm = create_llm_client(
            provider=provider, model=mid_model,
            base_url=self.config.get("backend_url"),
        ).get_llm()
        self.deep_llm = create_llm_client(
            provider=provider, model=deep_model,
            base_url=self.config.get("backend_url"),
        ).get_llm()

        for llm in (self.cheap_llm, self.mid_llm, self.deep_llm):
            try:
                setattr(llm, "_llm_provider", provider)
            except Exception:
                pass

        self.graph = self._build().compile()

    def _build(self) -> StateGraph:
        wf = StateGraph(DeltaState)
        wf.add_node("Classifier", create_classifier(self.cheap_llm))
        wf.add_node("Spec Extractor", create_spec_extractor(self.cheap_llm))
        wf.add_node("Compliance Delta", create_compliance_delta(self.mid_llm))
        wf.add_node("Focused Debate", create_focused_debate(self.mid_llm))
        wf.add_node("Integration Risk", create_integration_risk(self.mid_llm))
        wf.add_node("Budget Delta", create_budget_delta(self.mid_llm))
        wf.add_node("Future-proof", create_future_proof(self.mid_llm))
        wf.add_node("Delta Executive", create_delta_executive(self.deep_llm))

        wf.add_edge(START, "Classifier")
        wf.add_edge("Classifier", "Spec Extractor")
        wf.add_edge("Spec Extractor", "Compliance Delta")
        wf.add_edge("Compliance Delta", "Focused Debate")
        wf.add_edge("Focused Debate", "Integration Risk")
        wf.add_edge("Integration Risk", "Budget Delta")
        wf.add_edge("Budget Delta", "Future-proof")
        wf.add_edge("Future-proof", "Delta Executive")
        wf.add_edge("Delta Executive", END)
        return wf

    def analyse(
        self,
        project_state: dict[str, Any],
        partner_id: str,
        partner_name: str,
        solution_doc: str,
        rolling_summary: str = "",
    ) -> dict[str, Any]:
        init: dict[str, Any] = {
            "partner_id": partner_id,
            "partner_name": partner_name,
            "solution_doc": solution_doc,
            "project_name": project_state.get("project_name", ""),
            "fifa_category": project_state.get("fifa_category", ""),
            "standards_matrix": project_state.get("standards_matrix", ""),
            "vendor_matrix": project_state.get("vendor_matrix", ""),
            "rolling_summary": rolling_summary or project_state.get("executive_report", ""),
        }
        final = self.graph.invoke(init)
        self._dump(project_state.get("project_name", "unknown"), partner_id, final)
        return final

    def _dump(self, project_name: str, partner_id: str, state: dict[str, Any]) -> None:
        out = (
            Path(self.config["results_dir"])
            / "stadium_rnd" / project_name / "deltas" / partner_id
        )
        out.mkdir(parents=True, exist_ok=True)
        with (out / "delta.json").open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        with (out / "verdict.md").open("w", encoding="utf-8") as f:
            f.write(state.get("delta_executive_update", ""))
        logger.info("Wrote delta-analysis to %s", out)
