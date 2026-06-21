# Agentic RAG — decide when to retrieve (demo)

Companion code for the neurals.ca video **"Agentic RAG: How Agents Decide When to Retrieve"**
(Foundations series · episode #34). YouTube: <!-- VIDEO_LINK -->

A tiny, runnable agentic-RAG loop you can read top to bottom. It shows the part most RAG
tutorials skip: the agent does not retrieve on every question. It **decides**, **grades**
what it hauls up, and **re-dives** when the haul is junk, capped so it never loops forever.

The spine (from the video): a deep-sea salvage crew. The captain decides when to send the
ROV down, grades every sample, and throws back the junk.

## What it does
Three questions against a local model, over a 6-chunk private knowledge base it has never seen:

| Question | What the agent does |
|---|---|
| "What is retrieval-augmented generation?" | **DECIDE → ANSWER** (general knowledge, no dive) |
| "What orbit does the Kestrel-7 fly in?" | **RETRIEVE → GRADE → ANSWER** (junk thrown back) |
| "Who operates the Kestrel-7 ground station?" | **RETRIEVE → GRADE → ANSWER** (grounded) |

- **DECIDE** — a router (Self-RAG's "retrieve?" reflection) chooses retrieve vs. answer.
- **GRADE** — each retrieved chunk is checked for relevance (Self-RAG `ISREL` / Corrective-RAG
  evaluator); **JUNK never reaches the answer**.
- **REFINE** — if the whole haul is junk, rewrite the query and re-dive (capped at 3).

## Run it (local-first, no API key)
```bash
# 1) install + start Ollama  (https://ollama.com)
ollama serve
# 2) once, pull the two small models
ollama pull llama3.1
ollama pull nomic-embed-text
# 3) run
export PYTHONPATH=../../_shared-demos:$PYTHONPATH   # in this monorepo
python3 demo.py
```
In the public repo (`foundations-demos`), `demo_public.py` imports the helpers from the
vendored `_shared/` folder, so `python3 demo_public.py` works after a plain clone.

It fails cleanly if Ollama is not running (a one-line hint, no traceback).

## Honesty notes
Real local model calls, real embeddings, real grading. The grader and router are an LLM, so on
a tiny model they are not perfect; that is the point of the loop and the dive cap. Swap
`NEURALS_OLLAMA_MODEL` for a bigger model for sharper routing.

MIT licensed. Part of github.com/neuralsca/foundations-demos.
