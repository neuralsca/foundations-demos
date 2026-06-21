# DEMO_SPEC — #33 The Automated Newsroom (multi-agent build)

What the camera shows for the code-walk part (PiP via ReframeZoom over the Part-1 SEGMENT 3 build),
and the narration beats. The demo IS the newsroom: two specialized agents, one shared desk, a bounded
orchestrator loop, a publish gate.

## What runs
`demo.py` (shared-package) or `demo_public.py` (self-contained, in the public repo). One query —
"Why do AI agents need long-term memory?" — flows: RESEARCHER gathers 4 facts → HANDOFF to the shared
desk (state) → WRITER drafts a 3-sentence briefing from the desk → EDITOR approves or asks one revision
→ orchestrator calls PUBLISH. `--mock` gives a deterministic offline take for a clean recording.

## On-screen output (expected)
- Brand banner "The Automated Newsroom · Episode #33".
- `[RESEARCHER] gathers the facts` → 4 bullet facts print.
- `✓ HANDOFF  facts filed to the shared desk (state)`.
- `[WRITER] drafts the briefing from the desk` → the 3-sentence draft.
- `[EDITOR] checks the copy` → `✓ APPROVE`.
- `✓ PUBLISH approved in 1 iteration(s)` → FINAL STORY.

## ReframeZoom cue words (narration says them aloud; zoom-in lands on each)
- **RESEARCHER** — zoom the researcher step + the facts (agent 1, scoped to gathering).
- **HANDOFF** — zoom the desk line (the shared state object every agent reads/writes).
- **WRITER** — zoom the writer step + the draft (agent 2, scoped to crafting).
- **PUBLISH** — zoom the publish/termination line + the final story.
(EDITOR / the bounded loop is the guardrail beat — covered in Part 2.)

## Narration beats (Part 1, SEGMENT 3, ~80s)
1. "Two functions and one shared object — that is the whole system." (point at researcher + writer + state)
2. "The RESEARCHER has one job: gather facts. It files them to the desk." (RESEARCHER → HANDOFF)
3. "The WRITER never searches. It only shapes what is on the desk." (WRITER)
4. "An orchestrator runs them in a bounded loop and calls PUBLISH when the editor approves." (PUBLISH)

## Run
```
export PYTHONPATH=../../_shared-demos:$PYTHONPATH
python3 demo.py            # live (needs `ollama serve` + `ollama pull llama3.1`)
python3 demo.py --mock     # deterministic offline take (used by the VHS tape)
```
Runs in well under 90s. Fails cleanly (no traceback) if Ollama is down.
