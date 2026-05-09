"""Stadium R&D agent team.

A multi-agent system mirroring the TradingAgents pattern for researching
FIFA-standard smart-stadium solutions: domain analysts, standards
compliance, 3-way R&D debate (Innovator/Sceptic/Pragmatist), vendor
mapping, 4-way risk debate, budget/roadmap manager, executive editor,
and an incremental "delta" sub-graph that analyses each new partner
solution against the cached project state.
"""

from tradingagents.stadium_rnd.graph.delta_graph import StadiumDeltaGraph
from tradingagents.stadium_rnd.graph.stadium_graph import StadiumRnDGraph

__all__ = ["StadiumRnDGraph", "StadiumDeltaGraph"]
