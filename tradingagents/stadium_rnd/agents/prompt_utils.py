"""Prompt construction helpers with Anthropic prompt-caching support.

Anthropic billing for prompt caching:
  cache write:  ~125% of base input price
  cache read:   ~10% of base input price

We use cache breakpoints on:
  1. The system message (project context + FIFA reference bundle).
  2. The combined static reports prefix (analyst reports), so every
     debate turn pays cache-read price for that prefix instead of
     full-priced input.
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage


_PROVIDER_SUPPORTS_CACHE = {"anthropic"}


def _cache_block(text: str, *, cache: bool) -> dict:
    """Build a content block, optionally tagged for ephemeral cache."""
    block: dict[str, Any] = {"type": "text", "text": text}
    if cache:
        block["cache_control"] = {"type": "ephemeral"}
    return block


def build_cached_messages(
    *,
    system_text: str,
    static_prefix: str,
    fresh_text: str,
    provider: str = "anthropic",
) -> list[Any]:
    """Build a 2-message prompt with up to 2 cache breakpoints.

    Args:
        system_text:    System prompt (role, project context). Cached.
        static_prefix:  Bulk static content (FIFA bundle, analyst reports). Cached.
        fresh_text:     Per-call fresh content (debate history, current question).
                        Not cached.
        provider:       LLM provider; caching is only emitted for Anthropic.
    """
    cache = provider.lower() in _PROVIDER_SUPPORTS_CACHE
    if not cache:
        return [
            SystemMessage(content=system_text),
            HumanMessage(content=f"{static_prefix}\n\n---\n\n{fresh_text}"),
        ]

    return [
        SystemMessage(content=[_cache_block(system_text, cache=True)]),
        HumanMessage(content=[
            _cache_block(static_prefix, cache=True),
            _cache_block(fresh_text, cache=False),
        ]),
    ]


def build_simple_messages(system_text: str, user_text: str) -> list[Any]:
    """Plain (uncached) two-message prompt for one-shot agents."""
    return [
        SystemMessage(content=system_text),
        HumanMessage(content=user_text),
    ]
