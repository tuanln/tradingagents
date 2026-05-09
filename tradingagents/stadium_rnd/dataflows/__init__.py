"""Reference data accessors for the stadium R&D pipeline.

In a production deployment these functions would back onto:
  - A vector store (Chroma/Qdrant/PGVector) holding chunked FIFA
    Stadium Guidelines, FIFA Quality Programme, IEC/ISO/EN docs.
  - A vendor catalog DB (curated spec sheets + pricing references).
  - A web-search adapter for fresh case studies.

The skeletons here return placeholder content so the graph compiles and
runs end-to-end against a real LLM; swap them for real implementations
when wiring up data sources.
"""

from tradingagents.stadium_rnd.dataflows.reference import (
    fetch_fifa_reference_bundle,
    fetch_axis_reference,
    fetch_vendor_catalog_chunk,
)

__all__ = [
    "fetch_fifa_reference_bundle",
    "fetch_axis_reference",
    "fetch_vendor_catalog_chunk",
]
