# Testing AI Agents — the flight simulator (eval harness demo)

Companion code for **neurals.ca · Playlist 1 · Episode #36 — "How to Test AI Agents: Simulated
Environments and Eval Metrics."**  Part of [github.com/neuralsca/foundations-demos](https://github.com/neuralsca/foundations-demos).

You do not certify an aircraft by boarding passengers. You fly it in a simulator first. This is a tiny but
real **evaluation harness** for an AI support agent that shows the whole loop on screen:

1. **SIMULATE** — a sandboxed world: mock tools (`lookup_order`, `process_refund`) return fixtures plus one
   injected transient error. No real refunds, no real API.
2. **RUN** — the agent is run through a fixture test set, offline.
3. **SCORE** — the cockpit gauges: task success, tool-call accuracy, faithfulness, and cost (tokens).
4. **JUDGE** — a second model is the LLM-as-judge, grading faithfulness with a binary rubric that zeros any
   hallucinated step (a real local model when Ollama is up, a deterministic stub otherwise).
5. **CERTIFY** — a CI gate: the suite must clear a score floor AND `pass@k` must hold. Pass prints a green
   **AIRWORTHINESS CERTIFICATE**; fail prints a red **BLOCKED**.

The demo runs twice: a **CANDIDATE** build with two real bugs (a wrong refund amount and a hallucinated
"emailed the customer" step) **fails** the gate; the **FIXED** build earns the certificate. That is the gate
doing its job, catching a bad change before a real customer ever sees it.

## Run it

```bash
# optional, for the real LLM-as-judge (otherwise a stub judge runs):
ollama serve && ollama pull llama3.1

export PYTHONPATH=../../_shared-demos:$PYTHONPATH
python3 demo.py
```

No pip install needed; standard library only. Runs in well under a minute.

## What to look for
- The **CANDIDATE** table: `S2` tool-call is `BAD` (wrong amount) and `S4` faith is `HALLUC` (made-up step),
  so the suite scores 50% and the gate reads **BLOCKED**.
- The **FIXED** table: every row `PASS`, 100%, and the gate reads **AIRWORTHINESS CERTIFICATE**.
- `pass@5` on the flaky `S3` scenario: non-determinism is why one run is an anecdote and `pass@k` is evidence.

Files: `demo.py` (run this), `demo_public.py` (same, repo copy), `DEMO_SPEC.md` (the on-camera walk),
`recordings/` (VHS tapes that render the demo + a code cutaway).
