"""Pragmatist debater — anchors decisions to budget, ops, and timelines."""

from __future__ import annotations

from tradingagents.stadium_rnd.agents.debate._shared import build_debate_messages


_SYSTEM = (
    "You are the **Pragmatist** in a 3-way R&D debate. Your job is to "
    "ground the conversation in operational reality: CapEx range, ops "
    "team capacity, construction timeline, retrofit feasibility, local "
    "regulation, supply-chain spare parts. When the Innovator goes too "
    "far, propose a phased middle path; when the Sceptic blocks "
    "progress, propose a measured pilot. Engage with the latest "
    "argument and resolve concrete trade-offs."
)


def create_pragmatist(llm):
    def node(state) -> dict:
        debate = state["rnd_debate_state"]
        fresh = (
            "## Debate so far\n"
            + debate.get("history", "(no prior turns)")
            + "\n\n## Last argument\n"
            + debate.get("current_response", "(start the debate)")
            + "\n\nGive your next argument as the Pragmatist now. Be direct."
        )
        messages = build_debate_messages(
            system_text=_SYSTEM, state=state, fresh_text=fresh, llm=llm,
        )
        response = llm.invoke(messages)
        argument = f"Pragmatist: {response.content}"
        new_state = {
            "history": debate.get("history", "") + "\n" + argument,
            "innovator_history": debate.get("innovator_history", ""),
            "sceptic_history": debate.get("sceptic_history", ""),
            "pragmatist_history": debate.get("pragmatist_history", "") + "\n" + argument,
            "latest_speaker": "Pragmatist",
            "current_response": argument,
            "judge_decision": debate.get("judge_decision", ""),
            "count": debate.get("count", 0) + 1,
        }
        return {"rnd_debate_state": new_state}

    return node
