# DEMO_SPEC — #36 Testing AI Agents (the code walk, PiP over Part 2)

What the camera shows during the Part-2 code walk, the ReframeZoom cue words, and the ~50-60s narration
beats. The demo recording is `recordings/36-testing-agents-demo.mp4` (1920x1080, VHS-rendered); the code
cutaway is `recordings/code_scroll.mp4`. Both are PiP-overlaid on the NotebookLM cinematic (NOT insert_card,
which would kill the NB audio) and zoomed on the cue words via `make_zoom_cues.mjs`.

## The recording (what plays in the PiP)
`python3 demo.py` runs the eval harness twice:
- **CANDIDATE BUILD** -> a metrics table (scn / tool / task / faith / tok / verdict); S2 tool-call is BAD
  (wrong refund amount), S4 faith is HALLUC (made-up "emailed the customer" step); suite **50%**, gate reads
  red **BLOCKED**.
- **THE FIX** -> every row PASS, suite **100%**, `pass@5` 5/5, gate reads green **AIRWORTHINESS CERTIFICATE**.
- A side-by-side meter: candidate 50% (red) vs fixed 100% (green).

## ReframeZoom cue words (spoken in the Part-2 narration; each triggers a zoom-in)
- **SIMULATE** -> zoom the mock-tools / fixture world (the sandbox, the injected transient error).
- **RUN** -> zoom the agent running through the scenario table.
- **SCORE** -> zoom the gauges row (tool / task / faith / tok).
- **JUDGE** -> zoom the faith column flipping HALLUC red on S4.
- **CERTIFY** -> zoom the gate flipping from red BLOCKED to green AIRWORTHINESS CERTIFICATE.

## Narration beats (~55s, Part 2 SEGMENT "The Simulator / the real code")
1. "Here is the harness, the real code, on GitHub. First we SIMULATE the world." (code cutaway: the mock
   tools + fixtures; note the one injected transient error.)
2. "Then we RUN the agent through a fixture test set, offline, no real refunds." (demo PiP: the table fills.)
3. "We SCORE every flight on the gauges: did it call the right tool, succeed, stay faithful, and at what
   cost." (zoom the columns.)
4. "A second model is the JUDGE, and its binary rubric zeros any hallucinated step, so S4's made-up email
   fails." (zoom the red HALLUC.)
5. "Then the gate decides whether to CERTIFY. The candidate scores 50 percent: BLOCKED. The fix scores 100:
   airworthiness certificate." (zoom the gate flip.)
6. Punchline: "Crash in the simulator, not in production."

## Code cutaway anchors (code_scroll.mp4 stops on these headers in demo_public.py)
`THE SIMULATED ENVIRONMENT` -> `THE TEST SET` -> `LLM-AS-JUDGE` -> `THE GATE`.
