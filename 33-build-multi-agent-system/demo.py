#!/usr/bin/env python3
"""The Automated Newsroom - the smallest real multi-agent system in Python.

neurals.ca - Playlist 1, Episode #33 - https://neurals.ca

A Researcher agent gathers facts and files them to a shared DESK (state); a Writer
agent shapes the story; an Editor approves or asks for ONE revision; a tiny
orchestrator runs a bounded loop and calls PUBLISH. Two specialized agents, one
shared state, no framework.

Local-first: talks to Ollama (http://localhost:11434) with only the standard
library. No pip install, no API key.

    ollama serve && ollama pull llama3.1
    python3 demo_public.py            # live
    python3 demo_public.py --mock     # canned, offline (deterministic)
"""
import json, os, sys, urllib.request, urllib.error

MOCK = "--mock" in sys.argv
MODEL = os.environ.get("NEURALS_OLLAMA_MODEL", "llama3.1")
HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MAX_ITERATIONS = 3
C = {"v": "\033[38;2;167;139;250m", "t": "\033[38;2;45;212;191m",
     "g": "\033[38;2;52;211;153m", "m": "\033[38;2;139;148;158m", "x": "\033[0m"}

QUERY = "Why do AI agents need long-term memory? Brief an engineer in 3 sentences."
RESEARCHER_SYS = "You are a Researcher agent. Return exactly 4 short factual bullets, no preamble."
WRITER_SYS = "You are a Writer agent. Use ONLY the supplied facts; write at most 3 sentences."
EDITOR_SYS = "You are an Editor. Reply APPROVE if the draft is <=3 sentences and uses the facts, else REVISE: <reason>."
MOCK_FACTS = ("- A context window is finite, so an agent forgets earlier turns.\n"
              "- Long-term memory persists facts and results across sessions.\n"
              "- Retrieval pulls only the relevant memories back, saving tokens.\n"
              "- Without memory, an agent repeats work and contradicts itself.")
MOCK_DRAFT = ("Agents need long-term memory because the context window is finite and old turns fall out "
              "of view. A persistent store plus retrieval brings back just the relevant memories instead "
              "of re-sending everything. Without it, the agent repeats work and contradicts itself.")


def say(system, user):
    """One Ollama chat turn, stdlib only."""
    body = json.dumps({"model": MODEL, "stream": False,
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": user}]}).encode()
    req = urllib.request.Request(HOST.rstrip("/") + "/api/chat", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["message"]["content"].strip()


def agent(system, user, canned):
    return canned if MOCK else say(system, user)


def main():
    print(f"\n{C['v']}# The Automated Newsroom - a multi-agent system{C['x']}  {C['m']}neurals.ca #33{C['x']}\n")
    state = {"query": QUERY, "facts": "", "draft": "", "iterations": 0, "published": False}

    # Agent 1: RESEARCHER -> files facts to the shared desk (state)
    print(f"{C['v']}[RESEARCHER]{C['x']} gathering facts")
    state["facts"] = agent(RESEARCHER_SYS, f"Topic: {state['query']}", MOCK_FACTS)
    print(state["facts"])
    print(f"{C['t']}[HANDOFF]{C['x']} facts filed to the shared desk\n")

    # Orchestrator: bounded loop of WRITER -> EDITOR until approved or capped
    while state["iterations"] < MAX_ITERATIONS:
        state["iterations"] += 1
        print(f"{C['v']}[WRITER]{C['x']} drafting from the desk")
        state["draft"] = agent(WRITER_SYS, f"Facts:\n{state['facts']}\nWrite on: {state['query']}", MOCK_DRAFT)
        print("  " + state["draft"] + "\n")
        print(f"{C['v']}[EDITOR]{C['x']} checking the copy")
        verdict = agent(EDITOR_SYS, f"Facts:\n{state['facts']}\nDraft:\n{state['draft']}", "APPROVE")
        if verdict.upper().startswith("APPROVE"):
            state["published"] = True
            break
        print(f"  revise ({state['iterations']}/{MAX_ITERATIONS}): {verdict}")

    if state["published"]:
        print(f"{C['g']}[PUBLISH]{C['x']} approved in {state['iterations']} iteration(s)\n")
        print(C["t"] + "FINAL STORY" + C["x"] + "\n  " + state["draft"])
    else:
        print(f"{C['m']}hit the iteration cap; the guardrail stopped the loop cleanly{C['x']}")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError:
        print("Ollama not reachable at " + HOST + " - run `ollama serve`, or `python3 demo_public.py --mock`.")
        sys.exit(1)
