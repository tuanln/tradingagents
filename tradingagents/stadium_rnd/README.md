# stadium_rnd — Smart-Stadium R&D Agent Team

A LangGraph multi-agent skeleton for researching FIFA-standard
smart-stadium solutions, mirroring the TradingAgents pattern
(specialised analysts → cross-debate → trader/manager → final
decision) but tuned for stadium technology R&D.

See `docs/architecture.md` for the full design rationale.

## What's implemented

```
StadiumRnDGraph (project pipeline)
  ├─ 6 Domain Analysts (T1..T6)        — cheap LLM
  ├─ Standards Compliance Analyst       — mid LLM
  ├─ R&D Debate (Innovator ↔ Sceptic ↔ Pragmatist) — mid LLM
  ├─ R&D Moderator                      — deep LLM (structured output)
  ├─ Vendor Mapping                     — mid LLM
  ├─ Risk Debate (Tech ↔ Financial ↔ Operational ↔ Geopolitical) — mid LLM
  ├─ Risk Synthesizer                   — deep LLM (structured)
  ├─ Budget & Roadmap Manager           — deep LLM (structured)
  └─ Executive Editor                   — deep LLM (structured)

StadiumDeltaGraph (per-partner-solution incremental sub-graph)
  Classifier → Spec Extractor → Compliance Δ → Focused Debate (map-reduce)
   → Integration Risk → Budget Δ → Future-proof → Delta Executive Verdict
```

Three model tiers (`cheap` / `mid` / `deep`) — see Phần V §3.4 of the
architecture doc; defaults map to Haiku 4.5 / Sonnet 4.6 / Opus 4.7.

Anthropic prompt caching is wired in `agents/prompt_utils.py` with
`cache_control` breakpoints on the static prefix (FIFA reference,
analyst reports), which is the largest single token-cost saver.

## Where the data sources are stubbed

`tradingagents/stadium_rnd/dataflows/reference.py` returns short
placeholder text for the FIFA reference bundle, axis references, and
the vendor catalog. Replace these with real retrieval calls (Chroma /
Qdrant / PGVector backed by FIFA Stadium Guidelines, IEC/ISO/EN docs,
and a curated vendor catalogue) for production use.

## Running the example

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python -m tradingagents.stadium_rnd.example
```

This runs the full pipeline once, then a delta analysis against a mock
partner submission. Outputs land in `<results_dir>/stadium_rnd/<project>/`.

## Adding a new partner solution

```python
from tradingagents.stadium_rnd import StadiumDeltaGraph

delta = StadiumDeltaGraph(config=cfg).analyse(
    project_state=cached_project_state,        # from a prior StadiumRnDGraph.analyse()
    partner_id="vendor-x-2026-q2",
    partner_name="Vendor X",
    solution_doc=submitted_text,
)
print(delta["delta_executive_update"])
```

The delta graph reuses `standards_matrix`, `vendor_matrix`, and the
rolling executive summary from `project_state` — no full rerun.
