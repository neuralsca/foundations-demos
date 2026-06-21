#!/usr/bin/env python3
"""Demo: Testing AI Agents — the flight simulator.

neurals.ca · Playlist 1 · Episode #36

You do not certify an aircraft by boarding passengers. You fly it in a SIMULATOR
first. This demo is an eval harness for an AI support agent:

    SIMULATE  a sandboxed world  - mock tools (lookup_order, process_refund)
              return fixtures + one injected transient error. No real refunds.
    RUN       the agent through a fixture test set, offline, many times.
    SCORE     the cockpit gauges - task success, tool-call accuracy, faithfulness
              (an LLM-as-judge), and cost in tokens.
    JUDGE     a second model grades faithfulness with a binary rubric that ZEROS
              any hallucinated step (real local model when Ollama is up; a
              deterministic stub otherwise, so the harness always runs).
    CERTIFY   a CI gate: the suite must clear a score floor AND pass@k must hold.
              Pass -> a green AIRWORTHINESS CERTIFICATE. Fail -> a red BLOCKED.

We run it twice: a CANDIDATE build with two real bugs (a wrong refund amount and
a hallucinated "emailed the customer" step) FAILS the gate. The FIXED build earns
the certificate. That is the gate doing its job: crash in the simulator, not in
production.

Setup (optional real model for the judge):
    ollama serve ; ollama pull llama3.1
    export PYTHONPATH=../../_shared-demos:$PYTHONPATH
    python3 demo.py
Runs fully offline with a stub judge if Ollama is down.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))  # neurals_demo at repo root
from neurals_demo import term, llm  # noqa: E402

# --------------------------------------------------------------------------- #
# 1. THE SIMULATED ENVIRONMENT — mock tools over a fixture world (no real API) #
# --------------------------------------------------------------------------- #
ORDERS = {
    "A100": {"status": "shipped",   "total": 20},
    "B200": {"status": "delivered", "total": 35},
    "C300": {"status": "shipped",   "total": 50},
}
_flaky = {"hits": 0}  # B200's lookup throws once, then succeeds (transient error)


def lookup_order(order_id: str) -> str:
    if order_id == "B200":
        _flaky["hits"] += 1
        if _flaky["hits"] % 2 == 1:                      # injected transient failure
            raise TimeoutError("upstream 503 (simulated)")
    o = ORDERS.get(order_id)
    return f"order {order_id}: {o['status']}, total ${o['total']}" if o else f"order {order_id}: not found"


def process_refund(order_id: str, amount: int) -> str:
    o = ORDERS.get(order_id)
    if not o:
        return f"refund failed: {order_id} not found"
    return f"refund of ${amount} issued for {order_id}"


TOOLS = {"lookup_order": lookup_order, "process_refund": process_refund}

# --------------------------------------------------------------------------- #
# 2. THE TEST SET — fixtures with the EXPECTED tool call + answer + a rubric   #
# --------------------------------------------------------------------------- #
SCENARIOS = [
    {"id": "S1", "task": "What is the status of order A100?",
     "tool": ("lookup_order", {"order_id": "A100"}), "expect": "shipped", "flaky": False},
    {"id": "S2", "task": "Refund order A100 for $20.",
     "tool": ("process_refund", {"order_id": "A100", "amount": 20}), "expect": "$20", "flaky": False},
    {"id": "S3", "task": "Is order B200 delivered?",
     "tool": ("lookup_order", {"order_id": "B200"}), "expect": "delivered", "flaky": True},
    {"id": "S4", "task": "Refund order C300 for the full amount, $50.",
     "tool": ("process_refund", {"order_id": "C300", "amount": 50}), "expect": "$50", "flaky": False},
]


# --------------------------------------------------------------------------- #
# 3. THE AGENT UNDER TEST — deterministic so the gate result is stable on cam. #
#    `buggy=True` injects two REAL failure modes a code review would miss.     #
# --------------------------------------------------------------------------- #
def agent(scn: dict, buggy: bool) -> dict:
    """Return the agent's chosen tool call, its steps, final answer, and tokens."""
    want_tool, want_args = scn["tool"]
    args = dict(want_args)
    steps = [f"think: the user wants '{scn['task']}'", f"act: {want_tool}({args})"]

    if buggy and scn["id"] == "S2":
        args["amount"] = 200                              # BUG 1: wrong refund amount
    # call the tool, retrying once on a transient error (robustness)
    try:
        obs = TOOLS[want_tool](**args)
    except TimeoutError:
        steps.append("observe: transient error, retrying once")
        obs = TOOLS[want_tool](**args)
    steps.append(f"observe: {obs}")

    answer = obs
    if buggy and scn["id"] == "S4":
        answer = obs + " and I emailed the customer a receipt"  # BUG 2: hallucinated step/tool
        steps.append("act: send_email(...)  <- no such tool")

    tok = sum(len(s) for s in steps) // 4 + len(answer) // 4   # cheap token estimate
    return {"tool": (want_tool, args), "steps": steps, "answer": answer, "obs": obs, "tokens": tok}


# --------------------------------------------------------------------------- #
# 4. LLM-AS-JUDGE — faithfulness 0/1 with a binary rubric (real model if up).  #
#    Rubric: every claim in the answer must be supported by the tool output.   #
# --------------------------------------------------------------------------- #
JUDGE_SYS = ("You are a strict eval judge. Given TOOL_OUTPUT and ANSWER, reply with a single token: "
             "PASS if every claim in ANSWER is supported by TOOL_OUTPUT, else FAIL. No other words.")


def judge_faithful(answer: str, evidence: str, live: bool) -> bool:
    if live:
        try:
            verdict = llm.say(f"TOOL_OUTPUT: {evidence}\nANSWER: {answer}", system=JUDGE_SYS).strip().upper()
            return verdict.startswith("PASS")
        except llm.OllamaUnavailable:
            pass
    # deterministic stub rubric: any answer claim not grounded in the tool output fails
    claims_emailed = "email" in answer.lower()
    return not (claims_emailed and "email" not in evidence.lower())


# --------------------------------------------------------------------------- #
# 5. SCORING — run the suite, score the gauges, return rows + aggregate score. #
# --------------------------------------------------------------------------- #
def run_suite(buggy: bool, live: bool) -> tuple[list, float, int]:
    rows, passed, tokens = [], 0, 0
    for scn in SCENARIOS:
        r = agent(scn, buggy)
        got_tool, got_args = r["tool"]
        want_tool, want_args = scn["tool"]
        tool_ok = (got_tool == want_tool and got_args == want_args)     # tool-call accuracy
        task_ok = scn["expect"].lower() in r["answer"].lower()          # task success
        faith_ok = judge_faithful(r["answer"], r["obs"], live)          # faithfulness (judge)
        ok = tool_ok and task_ok and faith_ok
        passed += ok
        tokens += r["tokens"]
        rows.append([scn["id"], "ok" if tool_ok else "BAD", "ok" if task_ok else "MISS",
                     "ok" if faith_ok else "HALLUC", str(r["tokens"]),
                     term.green("PASS") if ok else term.red("FAIL")])
    return rows, passed / len(SCENARIOS), tokens


def pass_at_k(buggy: bool, live: bool, k: int = 5) -> tuple[int, int]:
    """Fly the flaky scenario k times; tally passes (non-determinism is the point)."""
    scn = next(s for s in SCENARIOS if s["flaky"])
    ok = 0
    for _ in range(k):
        r = agent(scn, buggy)
        if scn["expect"].lower() in r["answer"].lower() and judge_faithful(r["answer"], r["obs"], live):
            ok += 1
    return ok, k


# --------------------------------------------------------------------------- #
# 6. THE GATE — a score floor + pass@k lower bound = the airworthiness check.  #
# --------------------------------------------------------------------------- #
FLOOR = 0.90  # CI gate: the suite must clear 90% to merge


def report(label: str, buggy: bool, live: bool) -> float:
    term.rule(label)
    rows, score, tokens = run_suite(buggy, live)
    term.table(rows, headers=["scn", "tool", "task", "faith", "tok", "verdict"])
    term.kv("suite score", f"{score*100:.0f}%  (floor {int(FLOOR*100)}%)",
            accent="green" if score >= FLOOR else "red")
    term.kv("total cost", f"{tokens} tok")
    ok, k = pass_at_k(buggy, live)
    term.kv(f"pass@{k} (flaky S3)", f"{ok}/{k}", accent="green" if ok >= k - 1 else "amber")
    gate = score >= FLOOR and ok >= k - 1
    print()
    if gate:
        term.ok("AIRWORTHINESS CERTIFICATE issued, merge allowed.")
    else:
        term.fail("BLOCKED, eval gate failed, merge refused.")
    print()
    return score


def main() -> int:
    term.banner("Testing AI Agents", "Episode #36 · the flight simulator")
    live = llm.ping()
    term.kv("judge model", llm.chat_model() if live else "offline stub", accent="teal" if live else "amber")
    term.kv("environment", "sandboxed mock tools + fixtures (no real refunds)")
    term.kv("test set", f"{len(SCENARIOS)} scenarios · gate floor {int(FLOOR*100)}%")
    if not live:
        term.warn("Ollama not reachable, using the deterministic stub judge (harness still runs).")

    cand = report("CANDIDATE BUILD (a 'better' model, shipped on a green demo)", buggy=True, live=live)
    fixed = report("THE FIX (wrong refund amount + hallucinated step removed)", buggy=False, live=live)

    term.rule("the certification, side by side")
    term.meter("candidate", cand, 1.0, accent="red", suffix=f"{cand*100:.0f}%")
    term.meter("fixed", fixed, 1.0, accent="green", suffix=f"{fixed*100:.0f}%")
    term.info("one good demo is not airworthiness. The simulator caught a wrong refund and a "
              "hallucinated step before a single real customer ever saw them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
