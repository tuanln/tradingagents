"""Agent factories for the stadium R&D pipeline."""

from tradingagents.stadium_rnd.agents.domain.factory import create_domain_analyst, DOMAIN_AXES
from tradingagents.stadium_rnd.agents.compliance import create_compliance_analyst
from tradingagents.stadium_rnd.agents.debate.innovator import create_innovator
from tradingagents.stadium_rnd.agents.debate.sceptic import create_sceptic
from tradingagents.stadium_rnd.agents.debate.pragmatist import create_pragmatist
from tradingagents.stadium_rnd.agents.vendor_mapping import create_vendor_mapping_analyst
from tradingagents.stadium_rnd.agents.risk.tech import create_tech_risk_analyst
from tradingagents.stadium_rnd.agents.risk.financial import create_financial_risk_analyst
from tradingagents.stadium_rnd.agents.risk.operational import create_operational_risk_analyst
from tradingagents.stadium_rnd.agents.risk.geopolitical import create_geopolitical_risk_analyst
from tradingagents.stadium_rnd.agents.managers.budget_roadmap import create_budget_roadmap_manager
from tradingagents.stadium_rnd.agents.managers.executive_editor import create_executive_editor

__all__ = [
    "DOMAIN_AXES",
    "create_domain_analyst",
    "create_compliance_analyst",
    "create_innovator",
    "create_sceptic",
    "create_pragmatist",
    "create_vendor_mapping_analyst",
    "create_tech_risk_analyst",
    "create_financial_risk_analyst",
    "create_operational_risk_analyst",
    "create_geopolitical_risk_analyst",
    "create_budget_roadmap_manager",
    "create_executive_editor",
]
