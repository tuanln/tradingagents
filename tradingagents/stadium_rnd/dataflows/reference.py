"""Stub reference-data accessors.

These return short placeholders so a developer can run the graph
end-to-end without yet wiring a vector store. Replace with real
retrieval calls (Chroma / Qdrant / PGVector) for production use.
"""

from __future__ import annotations


_FIFA_BUNDLE = """\
[FIFA Reference Bundle — placeholder]

Key sections (excerpts):
- FIFA Stadium Guidelines (current edition): pitch dimensions 105×68m;
  minimum lighting 2,000 lux Class A horizontal illuminance for HD,
  3,500 lux vertical for HDR/4K broadcast (Class B/C/D tiers below).
- FIFA Quality Programme: turf, ball and goal-line technology certification.
- FIFA Safety & Security Guidelines: minimum CCTV coverage with retention,
  segregation provisions, alcohol policy, accessibility (1% of capacity).
- FIFA Sustainability requirements (since 2023): scope 1+2 measurement,
  waste & water management, accessibility for impaired spectators.

Compliance touchpoints:
- IEC 60364 (electrical), IEC 62305 (lightning), EN 50132 / IEC 62676 (CCTV),
  ISO 14001 (env), ISO 27001 (info-sec), ISO 20121 (sustainable events),
  IBC/IFC (fire), local building code.
"""


def fetch_fifa_reference_bundle() -> str:
    """Return the canonical FIFA reference text (cached at the system prompt)."""
    return _FIFA_BUNDLE


_AXIS_REFERENCE = {
    "T1_Connectivity": (
        "T1 — Connectivity & Network. Wi-Fi 6/6E/7 (IEEE 802.11ax/be), "
        "neutral-host DAS for cellular, 5G in-stadium (3.5 GHz / mmWave), "
        "fiber backbone with 100/400 GbE spine, ≥99.99% match-day uptime."
    ),
    "T2_Broadcast": (
        "T2 — Broadcast & Media. SMPTE 2110 IP production, 4K/8K HDR cameras, "
        "20+ cabled positions, dedicated VAR room, EVS replay, FIFA Cat.4 broadcast cabling."
    ),
    "T3_FanExperience": (
        "T3 — Fan Experience. Mobile app (ticketing, wayfinding, F&B order-ahead), "
        "AR overlays, second-screen replays, NFC ticketing, cashless concessions."
    ),
    "T4_SafetySecurity": (
        "T4 — Safety & Security. CCTV with crowd analytics, biometric or NFC access, "
        "BMS integrated with PCCC/fire, drone defence (RF detection), "
        "VOC for security ops with FIFA-grade logs."
    ),
    "T5_PitchFacility": (
        "T5 — Pitch & Facility. Hybrid grass (SISGrass / Desso GrassMaster), "
        "subsurface heating + irrigation IoT, LED FIFA Quality Pro lighting, "
        "field tunnel with TV-graphic lighting."
    ),
    "T6_Sustainability": (
        "T6 — Sustainability & Energy. Solar canopy (kWp sized ~25-50% of OpEx peak), "
        "BESS for match-day peak shaving, water reuse for irrigation, "
        "BREEAM Excellent or LEED Gold target, scope 1+2 carbon accounting."
    ),
}


def fetch_axis_reference(axis_key: str) -> str:
    """Return a short reference paragraph for a domain axis."""
    return _AXIS_REFERENCE.get(axis_key, f"[No reference data for {axis_key}]")


def fetch_vendor_catalog_chunk(query: str) -> str:
    """Return a placeholder vendor-catalog chunk for the given query."""
    return (
        f"[Vendor catalog excerpt for '{query}' — placeholder]\n"
        "Connectivity: Cisco, HPE Aruba, Extreme Networks, Huawei, Boldyn (DAS).\n"
        "Broadcast: Sony, Grass Valley, EVS, Hawk-Eye, Riedel.\n"
        "Fan-app: VenueNext, SeatGeek, Tappit.\n"
        "Security AI: Genetec, Avigilon, Bosch, Hikvision (geopolitical caveat).\n"
        "Pitch: SISGrass, Desso, Hellas, Mondo (LED).\n"
        "Sustainability: Schneider Electric, Siemens, ABB, Tesla Megapack."
    )
