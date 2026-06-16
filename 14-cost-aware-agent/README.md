# The Cost-Aware Agent

Companion code for the neurals.ca video **"Cut Your Claude API Bill in Half (Live Code Demo)"** (The Foundations Series, Episode #14).

It answers the same questions twice against the **real Claude API** and prints the bill side by side:

- **PASS 1 — naive:** every query goes to **Claude Opus 4.8** and re-sends the whole knowledge base at full price.
- **PASS 2 — cost-aware:** three Claude-native levers on the same agent:
  1. **Routing** — easy queries drop to **Claude Haiku 4.5** (about 5x cheaper).
  2. **Prompt caching** — the shared knowledge base is cached (`cache_control: ephemeral`), so repeats bill at roughly 10% of the input price.
  3. **Repeat cache** — an exact repeat is answered locally for $0.

Cost is computed from the **real token counts** Claude returns (input / output / cache-write / cache-read) against the published price card, so the savings are honest.

## Run

```bash
pip install -r requirements.txt          # just `anthropic`
export ANTHROPIC_API_KEY=sk-ant-...      # get a key at https://console.anthropic.com
python3 demo.py
```

A full run costs well under a dollar. You will see each query's tier (`route haiku` / `route opus`), the cache-write then cache-read tokens, the repeat-cache hits, and a two-bar meter with the percentage saved.

## Pricing used (per 1M tokens, 2026)

| Model | Input | Output | Role |
|---|---|---|---|
| Claude Haiku 4.5 | $1 | $5 | cheap tier |
| Claude Opus 4.8 | $5 | $25 | capable tier (5x) |

Cache write ≈ 1.25x input · cache read ≈ 0.10x input.

## Notes

- The knowledge base in `knowledge_base.md` is the shared, stable context. Prompt caching needs a sizable prefix (the cache minimum is a few thousand tokens), so `demo.py` repeats the file until it clears that bar — the point here is the caching behaviour.
- The headline percentage varies with your traffic shape (how repetitive, how large the context, how many requests are genuinely hard). Opus still earns its keep on the hard request; the goal is to stop paying its price for work the cheap model and the cache can do.
- Knobs: `NEURALS_CHEAP_MODEL`, `NEURALS_EXPENSIVE_MODEL`.

Built by neurals.ca · Visualizing Agentic AI · https://neurals.ca
