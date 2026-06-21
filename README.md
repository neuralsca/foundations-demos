# neurals.ca — Foundations Series demos

Runnable companion code for **The Foundations Series: Understanding Agentic AI** on the [neurals.ca](https://neurals.ca) YouTube channel. Each episode that includes a live code demo gets its own folder here; the shared helpers live in `neurals_demo/`.

## Episodes

| # | Folder | Video |
|---|---|---|
| 14 | [`14-cost-aware-agent/`](14-cost-aware-agent/) | Cut Your Claude API Bill in Half (Live Code Demo) |
| 33 | [`33-build-multi-agent-system/`](33-build-multi-agent-system/) | Build a Multi-Agent System in 10 Minutes (Python) _(video coming soon)_ |

## Shared library — `neurals_demo/`

A small, dependency-light helper package the demos import:

- `term.py` — brand-styled terminal output (the neurals.ca violet/teal palette): banners, steps, meters, tables, diffs.
- `llm.py` — local-first model access over the Ollama HTTP API (standard library only), for demos that run offline.
- `react.py` — a tiny, framework-free ReAct agent loop.

Each demo folder has its own `README.md` with run instructions and a `requirements.txt`.

## Quick start

```bash
git clone https://github.com/neuralsca/foundations-demos
cd foundations-demos/14-cost-aware-agent
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # for the Claude demos
python3 demo.py
```

## Links

- Channel / site: https://neurals.ca
- X / Twitter: https://x.com/neurals_ca

## License

MIT — see [LICENSE](LICENSE).
