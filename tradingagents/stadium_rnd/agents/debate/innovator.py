"""Innovator debater — champions the state-of-the-art."""

from __future__ import annotations

from tradingagents.stadium_rnd.agents.debate._shared import build_debate_messages


_SYSTEM = (
    "You are the **Innovator** in a 3-way R&D debate about a FIFA-grade "
    "smart stadium. Your job is to push the state of the art: argue for "
    "the most ambitious technologies that maximise fan experience, "
    "broadcast quality, and global brand recognition. Counter the "
    "Sceptic's caution and the Pragmatist's safe choices with concrete "
    "evidence: case studies, vendor track records, measurable upside. "
    "Engage with the latest argument directly; don't just list features."
)


def create_innovator(llm):
    def node(state) -> dict:
        debate = state["rnd_debate_state"]
        fresh = (
            "## Debate so far\n"
            + debate.get("history", "(no prior turns)")
            + "\n\n## Last argument\n"
            + debate.get("current_response", "(start the debate)")
            + "\n\nGive your next argument as the Innovator now. Be direct."
        )
        messages = build_debate_messages(
            system_text=_SYSTEM, state=state, fresh_text=fresh, llm=llm,
        )
        response = llm.invoke(messages)
        argument = f"Innovator: {response.content}"
        new_state = {
            "history": debate.get("history", "") + "\n" + argument,
            "innovator_history": debate.get("innovator_history", "") + "\n" + argument,
            "sceptic_history": debate.get("sceptic_history", ""),
            "pragmatist_history": debate.get("pragmatist_history", ""),
            "latest_speaker": "Innovator",
            "current_response": argument,
            "judge_decision": debate.get("judge_decision", ""),
            "count": debate.get("count", 0) + 1,
        }
        return {"rnd_debate_state": new_state}

    return node
