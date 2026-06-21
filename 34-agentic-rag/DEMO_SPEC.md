# DEMO_SPEC · Episode #34 · Agentic RAG (local Ollama)

> What the code-walk part (P2) shows, the narration beats it is cut against (the
> ReframeZoom cue words), and the real on-screen output. This is the spec the
> cinematic's code segment is edited to.

## One-line promise
"Watch the agent answer one question WITHOUT searching, then dive, grade the haul, and throw
back the junk, live."

## On-camera artifact
A single terminal running `demo.py` (brand violet/teal) against a LOCAL model (Ollama, no API
key). Hero visual: the GRADE lines, teal **RELEVANT** vs red **JUNK**, and the captain's log
(`no-dive answers 1/3`, `junk thrown back 2`).

## Beats + ReframeZoom cue words (P2 narration is timed to these)
1. **Cold tie-in** — the banner + the 6-chunk "private seabed" is indexed.
2. **DECIDE (cue: DECIDE)** — Q1 "what is RAG?" routes to **ANSWER**: `DECIDE -> ANSWER`,
   "shallow: the model already knows this. No dive." The agent answers from its own memory.
3. **RETRIEVE (cue: RETRIEVE)** — Q2 "Kestrel-7 orbit" routes to RETRIEVE; `DIVE 1: RETRIEVE top-2`.
4. **GRADE / JUNK (cues: GRADE, JUNK)** — each chunk scored: `GRADE RELEVANT (0.87)` teal vs
   `GRADE JUNK (0.71)` red. Junk is thrown back before the answer.
5. **ANSWER (cue: ANSWER)** — `ANSWER (grounded): The Kestrel-7 satellite flies in a
   sun-synchronous orbit.` One clean artifact, cited to the kept chunk.
6. **REFINE (cue: REFINE)** — (when a haul is all junk) `REFINE: rewrite + re-dive`, capped at 3.
7. **Payoff** — the captain's log: `no-dive answers 1/3`, `total dives 2`, `junk thrown back 2`.
   Close: "a good agent knows when NOT to search."

ReframeZoom cue tokens (printed in the demo output, said aloud in P2): **DECIDE · RETRIEVE ·
GRADE · JUNK · REFINE · ANSWER**.

## Real run (validation, local llama3.1 + nomic-embed-text)
Q1 -> DECIDE ANSWER (no dive). Q2 -> 1 dive, 1 relevant / 1 junk, grounded orbit answer.
Q3 -> 1 dive, 1 relevant / 1 junk, grounded ground-station answer. Log: no-dive 1/3, 2 dives,
4 chunks graded, 2 junk thrown back. Runs in well under 90s. Exit 0; graceful one-liner if
Ollama is down.

## Honesty notes (say on camera / in the description)
Real local calls + embeddings + LLM grading. On a small model the router/grader are imperfect,
which is exactly why the loop grades and the dive cap exists. A bigger model sharpens routing.

## Run
```bash
cd ideation-playlist1/34-agentic-rag/code
export PYTHONPATH="$PWD/../../_shared-demos:$PYTHONPATH"
ollama serve   # once: ollama pull llama3.1 && ollama pull nomic-embed-text
python3 demo.py
```

## Belief hooks (continuity)
Opens with one callback to similarity search finding the closest chunks (embeddings, #25);
closes on the thesis "the best agent searches less" and the long-context-and-RAG-are-partners
note. Forward hook generic.
