from tradingagents.stadium_rnd.agents.risk._shared import (
    FINANCIAL_ROLE,
    create_risk_node,
)


def create_financial_risk_analyst(llm):
    return create_risk_node(llm, FINANCIAL_ROLE)
