from tradingagents.stadium_rnd.agents.risk._shared import TECH_ROLE, create_risk_node


def create_tech_risk_analyst(llm):
    return create_risk_node(llm, TECH_ROLE)
