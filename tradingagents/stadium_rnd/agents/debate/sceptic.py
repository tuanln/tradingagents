"""Sceptic debater — challenges hype and immature tech."""

from __future__ import annotations

from tradingagents.stadium_rnd.agents.debate._shared import build_debate_messages


_SYSTEM = (
    "You are the **Sceptic** in a 3-way R&D debate. Your job is to attack "
    "weak claims: vendor hype, low TRL (<7) tech, single-vendor lock-in, "
    "cherry-picked case studies, missing operational evidence. When the "
    "Innovator proposes something, demand reproducible benchmarks; when "
    "the Pragmatist defaults to a safe option, ask whether it's actually "
    "good enough for FIFA Cat.4 inspection. Engage with the latest "
    "argument; don't just list objections."
)


def create_sceptic(llm):
    def node(state) -> dict:
        debate = state["rnd_debate_state"]
        fresh = (
            "## Debate so far\n"
            + debate.get("history", "(no prior turns)")
            + "\n\n## Last argument\n"
            + debate.get("current_response", "(start the debate)")
            + "\n\nGive your next argument as the Sceptic now. Be direct."
        )
        messages = build_debate_messages(
            system_text=_SYSTEM, state=state, fresh_text=fresh, llm=llm,
        )
        response = llm.invoke(messages)
        argument = f"Sceptic: {response.content}"
        new_state = {
            "history": debate.get("history", "") + "\n" + argument,
            "innovator_history": debate.get("innovator_history", ""),
            "sceptic_history": debate.get("sceptic_history", "") + "\n" + argument,
            "pragmatist_history": debate.get("pragmatist_history", ""),
            "latest_speaker": "Sceptic",
            "current_response": argument,
            "judge_decision": debate.get("judge_decision", ""),
            "count": debate.get("count", 0) + 1,
        }
        return {"rnd_debate_state": new_state}

    return node
