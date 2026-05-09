"""End-to-end example for the stadium R&D pipeline.

Usage::

    export ANTHROPIC_API_KEY=sk-ant-...
    python -m tradingagents.stadium_rnd.example

The example runs:
    1. Full project pipeline once (creates PROJECT_STATE).
    2. A delta analysis for a single (mock) partner solution.

Cost expectation (Claude defaults, see docs/architecture.md Phần V §5):
    - Step 1: ~$2-3 with caching, no caching ~$5-8.
    - Step 2: ~$0.6-1.2 with caching.
"""

from __future__ import annotations

import logging

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.stadium_rnd import StadiumDeltaGraph, StadiumRnDGraph

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s :: %(message)s")


MOCK_PARTNER_SUBMISSION = """\
# Cisco — Stadium Connectivity Solution v2026

Scope: Wi-Fi 7 (IEEE 802.11be) tri-band APs, 6E DAS for cellular,
400 GbE backbone, full Cat.6A horizontal. Coverage to FIFA Cat.4 with
≥99.99% match-day uptime SLA.

KPIs:
- 80,000 concurrent users at >25 Mbps median throughput per device
- <20 ms RTT at the edge
- IPv6-only management plane

Pricing tier: enterprise. Approx CapEx: $14M (excl. installation).
Operational warranty: 5y, with optional 2y extension.

Integrations: Genetec, Bosch (CCTV), VenueNext (fan app),
Schneider Electric BMS. Exposes streaming telemetry on OpenTelemetry.

Certifications claimed: FCC, ETSI EN 300 328 / 301 893, FIFA infra-ready.
"""


def main() -> None:
    cfg = DEFAULT_CONFIG.copy()
    cfg["llm_provider"] = "anthropic"
    cfg["stadium_rnd.cheap_llm"] = "claude-haiku-4-5"
    cfg["stadium_rnd.mid_llm"] = "claude-sonnet-4-6"
    cfg["stadium_rnd.deep_llm"] = "claude-opus-4-7"

    print("\n=========== STEP 1 — Full project pipeline ===========\n")
    project = StadiumRnDGraph(
        config=cfg, max_rnd_rounds=1, max_risk_rounds=1
    ).analyse(
        project_name="My-Smart-Stadium-2030",
        capacity=50_000,
        fifa_category="Cat.4",
        location_country="Vietnam",
    )
    print("\nExecutive report:\n")
    print(project["executive_report"])

    print("\n=========== STEP 2 — Delta analysis for Cisco v2026 ===========\n")
    delta = StadiumDeltaGraph(config=cfg).analyse(
        project_state=project,
        partner_id="cisco-2026-q1",
        partner_name="Cisco",
        solution_doc=MOCK_PARTNER_SUBMISSION,
    )
    print("\nDelta verdict:\n")
    print(delta["delta_executive_update"])


if __name__ == "__main__":
    main()
