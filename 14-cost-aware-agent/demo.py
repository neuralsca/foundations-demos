#!/usr/bin/env python3
"""The Cost-Aware Agent — cut your Claude bill, live.

neurals.ca · The Foundations Series · Episode #14
Video: https://neurals.ca

Answer the same questions twice against the real Claude API:

    PASS 1 — naive:  every query goes to the expensive-but-capable model
             (Claude Opus 4.8) and re-sends the whole knowledge base at full price.
    PASS 2 — cost-aware:  three Claude-native levers on the same agent
             1. ROUTING        - easy queries drop to Claude Haiku 4.5 (5x cheaper).
             2. PROMPT CACHING  - the shared knowledge base is cached
                (cache_control: ephemeral), so repeats bill at ~10% of input price.
             3. REPEAT CACHE    - an exact repeat is answered locally for $0.

Cost is computed from the REAL token counts Claude returns (input / output /
cache-write / cache-read) against the published per-million-token price card, so
the savings are honest. Pricing (per 1M tokens, 2026):
    Claude Haiku 4.5  $1 in / $5 out      (cheap tier)
    Claude Opus 4.8   $5 in / $25 out     (capable tier)  -> 5x the price
    cache write = 1.25x input · cache read = 0.10x input

Run:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...      # get one at console.anthropic.com
    python3 demo.py
"""
from __future__ import annotations

import os
import re
import sys

# the shared neurals_demo helpers live at the repo root
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from neurals_demo import term  # noqa: E402

import anthropic  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# --- models + real per-MTok price card -------------------------------------- #
CHEAP = os.environ.get("NEURALS_CHEAP_MODEL", "claude-haiku-4-5")        # $1 / $5
EXPENSIVE = os.environ.get("NEURALS_EXPENSIVE_MODEL", "claude-opus-4-8")  # $5 / $25
PRICE = {  # per 1M tokens
    CHEAP:     {"in": 1.00, "out": 5.00},
    EXPENSIVE: {"in": 5.00, "out": 25.00},
}
MAX_TOKENS = 200  # cap output (truncation is itself a cost lever; keeps the demo snappy)


def load_kb() -> str:
    """The shared context the agent grounds on. Prompt caching needs a sizable,
    stable prefix (the cache minimum is ~4k tokens), so a short file is repeated
    until it clears that bar — the point of the demo is the caching behaviour."""
    p = os.path.join(HERE, "knowledge_base.md")
    base = open(p, encoding="utf-8").read() if os.path.exists(p) else "Agent cost notes."
    kb = base
    while len(kb) < 24000:
        kb += "\n\n" + base
    return kb


KB = load_kb()
SYS_INSTRUCTION = ("You are a concise assistant for AI engineers. Answer in at most two "
                   "sentences, grounded in the knowledge base provided.")

# The day's traffic: easy lookups, two exact repeats (FAQ), one genuinely hard design ask.
QUERIES = [
    "What is prompt caching, in one line?",
    "How does model routing reduce cost?",
    "What is prompt caching, in one line?",                      # exact repeat -> local cache
    "What is semantic caching?",
    "Design a full cost-optimization architecture for a 5-agent system handling a million "
    "requests a day: caching, routing, pruning, budgets, and failure handling.",  # hard -> Opus
    "How does model routing reduce cost?",                       # exact repeat -> local cache
    "Name the main levers to cut agent token cost.",
]
HARD_HINTS = ("design", "architecture", "step by step", "strategy", "trade-off")


def client() -> anthropic.Anthropic:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        term.fail("Set ANTHROPIC_API_KEY. Get a key at https://console.anthropic.com")
        raise SystemExit(1)
    return anthropic.Anthropic()


def is_hard(q: str) -> bool:
    return len(q) > 160 or any(h in q.lower() for h in HARD_HINTS)


def norm(q: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", q.lower()).strip()


def dollars(model: str, u) -> float:
    p = PRICE[model]
    cw = getattr(u, "cache_creation_input_tokens", 0) or 0
    cr = getattr(u, "cache_read_input_tokens", 0) or 0
    # cache write = 1.25x input, cache read = 0.10x input
    return (u.input_tokens * p["in"] + cw * p["in"] * 1.25
            + cr * p["in"] * 0.10 + u.output_tokens * p["out"]) / 1e6


def ask(cl, model: str, q: str, cache: bool):
    """One Claude call. cache=True puts cache_control on the KB system block."""
    kb_block = {"type": "text", "text": KB}
    if cache:
        kb_block["cache_control"] = {"type": "ephemeral"}
    return cl.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=[{"type": "text", "text": SYS_INSTRUCTION}, kb_block],
        messages=[{"role": "user", "content": q}],
    )


def pass_naive(cl) -> float:
    term.rule("PASS 1 · naive (every query to Claude Opus, no cache)")
    spend = 0.0
    for i, q in enumerate(QUERIES, 1):
        r = ask(cl, EXPENSIVE, q, cache=False)
        c = dollars(EXPENSIVE, r.usage)
        spend += c
        term.step(f"{q[:52]}…" if len(q) > 52 else q, reset=(i == 1))
        term.info(f"opus · in {r.usage.input_tokens} + out {r.usage.output_tokens} tok · ${c:.5f}")
    term.kv("PASS 1 total", f"${spend:.5f}", accent="red")
    return spend


def pass_cost_aware(cl) -> tuple[float, int, int, int]:
    term.rule("PASS 2 · cost-aware (route to Haiku · cache the KB · skip repeats)")
    spend = 0.0
    seen: dict[str, str] = {}
    hits = cheap = esc = 0
    for i, q in enumerate(QUERIES, 1):
        term.step(f"{q[:52]}…" if len(q) > 52 else q, reset=(i == 1))
        key = norm(q)
        if key in seen:                                   # lever 3: repeat cache
            hits += 1
            term.info(term.teal("repeat cache HIT · 0 tok · $0.00000"))
            continue
        model = EXPENSIVE if is_hard(q) else CHEAP        # lever 1: routing
        if model == EXPENSIVE:
            esc += 1
        else:
            cheap += 1
        r = ask(cl, model, q, cache=True)                 # lever 2: prompt caching
        c = dollars(model, r.usage)
        spend += c
        seen[key] = r.content[0].text if r.content else ""
        u = r.usage
        cr = getattr(u, "cache_read_input_tokens", 0) or 0
        cw = getattr(u, "cache_creation_input_tokens", 0) or 0
        tier = "opus " if model == EXPENSIVE else "haiku"
        col = term.amber if model == EXPENSIVE else term.green
        cache_note = (f" · cache-read {cr}" if cr else (f" · cache-write {cw}" if cw else ""))
        term.info(col(f"route {tier} · in {u.input_tokens} + out {u.output_tokens} tok{cache_note} · ${c:.5f}"
                      + ("  (escalated: hard query)" if model == EXPENSIVE else "")))
    term.kv("PASS 2 total", f"${spend:.5f}", accent="green")
    return spend, hits, cheap, esc


def main() -> int:
    term.banner("The Cost-Aware Agent", "Episode #14 · cut your Claude bill, live")
    term.kv("cheap model", CHEAP)
    term.kv("capable model", EXPENSIVE, accent="amber")
    term.kv("knowledge base", f"{len(KB):,} chars (cached prefix)")
    term.kv("queries", f"{len(QUERIES)} (2 exact repeats + 1 hard design ask)")
    try:
        cl = client()
        naive = pass_naive(cl)
        aware, hits, cheap, esc = pass_cost_aware(cl)
    except anthropic.AuthenticationError:
        term.fail("Claude auth failed. Check ANTHROPIC_API_KEY.")
        return 1
    except anthropic.APIError as e:
        term.fail(f"Claude API error: {e}")
        return 1

    term.rule("the bill, side by side")
    biggest = max(naive, aware, 1e-9)
    term.meter("naive (all Opus)", naive, biggest, accent="red", suffix=f"${naive:.5f}")
    term.meter("cost-aware", aware, biggest, accent="green", suffix=f"${aware:.5f}")
    saved = 0.0 if naive == 0 else (naive - aware) / naive * 100
    term.kv("routed to Haiku", f"{cheap}/{len(QUERIES)}", accent="green")
    term.kv("escalated to Opus", f"{esc}/{len(QUERIES)}", accent="amber")
    term.kv("repeat-cache hits", f"{hits}/{len(QUERIES)}", accent="teal")
    term.kv("SAVED", f"{saved:.1f}%", accent="green" if saved > 0 else "red")
    print()
    term.info("same answers, a fraction of the bill: route to Haiku, cache the context, "
              "and pay the Opus premium only where it earns its keep.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
