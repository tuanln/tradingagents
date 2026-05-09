from tradingagents.stadium_rnd.agents.risk._shared import (
    OPERATIONAL_ROLE,
    create_risk_node,
)


def create_operational_risk_analyst(llm):
    return create_risk_node(llm, OPERATIONAL_ROLE)
