from tradingagents.stadium_rnd.agents.risk._shared import (
    GEOPOLITICAL_ROLE,
    create_risk_node,
)


def create_geopolitical_risk_analyst(llm):
    return create_risk_node(llm, GEOPOLITICAL_ROLE)
