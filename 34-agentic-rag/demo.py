#!/usr/bin/env python3
"""Demo: Agentic RAG — how an agent decides WHEN to retrieve.

neurals.ca · neurals.ca · github.com/neuralsca/foundations-demos

The spine: a deep-sea salvage crew. The captain (the agent) does not send the ROV
down on every question. It DECIDES whether to dive at all, GRADES every sample the
ROV hauls up, throws back the junk, and re-dives with new coordinates when the haul
is bad, capped so it never loops forever.

Three real questions, answered against a LOCAL model (Ollama, no API key), over a
tiny in-memory vector store the base model has never seen:

    Q1  answerable from the model's own knowledge      -> DECIDE: no dive (reason)
    Q2  needs the private docs                          -> DIVE: retrieve, grade, answer
    Q3  first haul is junk                              -> REFINE: rewrite + re-dive, then answer

Retrieval = embed the query (nomic-embed-text), cosine vs each chunk, take top-k.
Grading  = an LLM relevance check per chunk (Self-RAG's ISREL / Corrective-RAG's
evaluator), so JUNK never reaches the answer. The loop is capped at MAX_DIVES.

Run:
    export PYTHONPATH=../../_shared-demos:$PYTHONPATH
    ollama serve            # + once: ollama pull llama3.1 && ollama pull nomic-embed-text
    python3 demo.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))  # neurals_demo at repo root
from neurals_demo import llm, term  # noqa: E402

TOP_K = 2
MAX_DIVES = 3          # bounded curiosity: never loop forever
GEN = {"num_predict": 90}   # keep answers short + the demo snappy

# --- the private knowledge base (the seabed): facts the base model cannot know -- #
# A fictional satellite so the model MUST retrieve, plus distractor chunks so the
# grader has real junk to throw back.
DOCS = [
    "The Kestrel-7 earth-observation satellite flies in a sun-synchronous orbit at "
    "an altitude of 512 kilometers, crossing the equator at 10:30 local time.",
    "The Kestrel-7 ground station and mission control are operated by the Atacama "
    "Relay Cooperative from a site in northern Chile.",
    "Kestrel-7 carries a hyperspectral imager with 240 spectral bands used mainly "
    "for crop-stress and wildfire detection.",
    # distractors (similar words, wrong facts) the grader must reject as JUNK:
    "Coffee brewed above 96 degrees Celsius over-extracts and tastes bitter; a 92 "
    "degree pour is the barista standard.",
    "The peregrine falcon, sometimes nicknamed a kestrel by mistake, dives at over "
    "380 kilometers per hour, the fastest animal on earth.",
    "A sun-synchronous marketing campaign in 2019 used orbital imagery as a backdrop "
    "but had no connection to any real spacecraft program.",
]

ROUTER_SYS = (
    "You are a retrieval router for a RAG agent. Reply with ONE word: ANSWER or RETRIEVE.\n"
    "ANSWER = broad, well-known general knowledge you can answer reliably on your own.\n"
    "RETRIEVE = a specific named entity, product, person, or private fact you cannot be sure of.\n"
    "Examples:\n"
    "Q: What is machine learning? -> ANSWER\n"
    "Q: What is retrieval-augmented generation? -> ANSWER\n"
    "Q: What orbit does the Kestrel-7 satellite fly in? -> RETRIEVE\n"
    "Q: Who is the CEO of Acme Robotics? -> RETRIEVE")
GRADER_SYS = ("You grade whether a passage is RELEVANT to a question. "
              "Answer ONLY 'YES' or 'NO'.")


def _index(docs):
    return [(d, llm.embed(d)) for d in docs]


def retrieve(index, query, k=TOP_K):
    qv = llm.embed(query)
    scored = sorted(((llm.cosine(qv, dv), d) for d, dv in index), reverse=True)
    return [(d, s) for s, d in scored[:k]]


def route(query) -> str:
    r = llm.say(query, system=ROUTER_SYS, temperature=0, **GEN).strip().upper()
    return "RETRIEVE" if "RETRIEVE" in r else "ANSWER"


def grade(query, passage) -> bool:
    r = llm.say(f"Question: {query}\nPassage: {passage}\nRelevant?",
                system=GRADER_SYS, temperature=0, num_predict=4).strip().upper()
    return r.startswith("Y")


def rewrite(query) -> str:
    nq = llm.say(f"Rewrite this search query to be more specific and literal, "
                 f"one line, no preamble: {query}", temperature=0.3, num_predict=40).strip()
    return nq.splitlines()[0].strip('"') if nq else query


def answer_from(query, chunks) -> str:
    ctx = "\n".join(f"- {c}" for c in chunks)
    sys_ = "Answer in one sentence using ONLY the context. If the context lacks it, say so."
    return llm.say(f"Context:\n{ctx}\n\nQuestion: {query}", system=sys_,
                   temperature=0.1, **GEN).strip()


def answer_parametric(query) -> str:
    return llm.say(query, system="Answer in one sentence from your own general knowledge.",
                   temperature=0.1, **GEN).strip()


def handle(index, query):
    term.rule(query)
    # 1) DECIDE — retrieve or reason? (Self-RAG's retrieve reflection token)
    decision = route(query)
    term.step(f"DECIDE -> {decision}", reset=True)
    if decision == "ANSWER":
        term.info(term.teal("shallow: the model already knows this. No dive."))
        term.ok("ANSWER (no retrieval): " + answer_parametric(query))
        return {"dives": 0, "graded": 0, "junked": 0, "retrieved": False}

    graded = junked = 0
    q = query
    for dive in range(1, MAX_DIVES + 1):
        term.step(f"DIVE {dive}: RETRIEVE top-{TOP_K}  (query: {q[:46]})")
        hits = retrieve(index, q)
        keep = []
        for doc, score in hits:
            graded += 1
            good = grade(query, doc)
            tag = term.teal("RELEVANT") if good else term.red("JUNK")
            term.info(f"  GRADE {tag}  ({score:.2f})  {doc[:54]}…")
            if good:
                keep.append(doc)
            else:
                junked += 1
        if keep:
            term.ok("ANSWER (grounded): " + answer_from(query, keep))
            return {"dives": dive, "graded": graded, "junked": junked, "retrieved": True}
        if dive < MAX_DIVES:
            q = rewrite(q)
            term.warn(f"REFINE: whole haul was junk, rewrite + re-dive -> {q[:46]}")
    term.fail("dive limit reached: no grounded answer, would radio the surface (web fallback)")
    return {"dives": MAX_DIVES, "graded": graded, "junked": junked, "retrieved": True}


QUERIES = [
    "In one sentence, what is retrieval-augmented generation?",   # parametric -> no dive
    "What orbit does the Kestrel-7 satellite fly in?",            # needs the private docs
    "Who operates the Kestrel-7 ground station?",                 # first haul junk -> refine
]


def main() -> int:
    term.banner("Agentic RAG", "Episode #34 · decide when to retrieve")
    if not llm.ping():
        term.fail("Ollama is not running. Start it with `ollama serve`, then re-run.")
        term.info("once: ollama pull llama3.1 && ollama pull nomic-embed-text")
        return 1
    term.kv("chat model", llm.chat_model())
    term.kv("embed model", llm.embed_model())
    term.kv("knowledge base", f"{len(DOCS)} chunks (private seabed)")
    try:
        term.step("indexing the seabed (embedding the chunks)", reset=True)
        index = _index(DOCS)
        term.ok(f"indexed {len(index)} chunks")
        stats = [handle(index, q) for q in QUERIES]
    except llm.OllamaUnavailable as e:
        term.fail(str(e))
        return 1

    term.rule("the captain's log")
    dives = sum(s["dives"] for s in stats)
    graded = sum(s["graded"] for s in stats)
    junked = sum(s["junked"] for s in stats)
    skipped = sum(1 for s in stats if not s["retrieved"])
    term.kv("questions", str(len(QUERIES)))
    term.kv("no-dive answers", f"{skipped}/{len(QUERIES)}", accent="teal")
    term.kv("total dives", str(dives), accent="violet")
    term.kv("chunks graded", str(graded))
    term.kv("junk thrown back", str(junked), accent="amber")
    print()
    term.info("a good agent is not the one that searches the most. It is the one that "
              "knows when not to, grades what it hauls up, and stops when the answer is good.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
