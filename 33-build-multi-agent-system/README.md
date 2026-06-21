# The Automated Newsroom — a multi-agent system in Python (neurals.ca #33)

The smallest real multi-agent system: a **Researcher** agent gathers facts and files them to a shared
**desk** (state), a **Writer** agent shapes the story, an **Editor** approves or asks for one revision,
and a tiny **orchestrator** runs a bounded loop and calls **PUBLISH**. Two specialized agents, one shared
state, no framework — local-first on [Ollama](https://ollama.com).

## Run
```bash
ollama serve            # in another terminal
ollama pull llama3.1
python3 demo_public.py          # live
python3 demo_public.py --mock   # canned, offline (deterministic)
```
`demo_public.py` is self-contained (standard library only). `demo.py` is the same demo on the shared
`neurals_demo` helpers (`export PYTHONPATH=../../_shared-demos:$PYTHONPATH`).

## What you should see
RESEARCHER → 4 facts → HANDOFF to the desk → WRITER → a 3-sentence briefing → EDITOR APPROVE → PUBLISH.

Companion to the video. Part of **neurals.ca · Visualizing Agentic AI** — https://neurals.ca
