# Agent Cost Optimization — Engineering Knowledge Base

A reference the cost-aware agent grounds its answers on. It also doubles as the
large, stable context the demo caches with Anthropic prompt caching.

## Why agent loops are expensive

A chatbot is one request and one response. An agent runs a loop: perceive, reason,
plan, act, and repeat. At every turn the whole accumulated context (the system
prompt, the tools, the running transcript, the tool results) is re-sent to the
model. Cost therefore COMPOUNDS rather than adds: step ninety pays to re-read the
eighty-nine steps before it. The same loop that makes an agent capable is the loop
that makes it expensive, so cost has to be treated as a first-class part of how the
agent is engineered, not a billing surprise discovered at the end of the month.

The three biggest cost drivers are: (1) sending every request to the most capable,
most expensive model; (2) re-sending a large, unchanging context on every call; and
(3) recomputing answers the system has already produced. Each driver has a direct,
well-understood lever.

## Lever 1 — Model routing (send easy work to the cheap model)

Not every request needs a frontier model. Classification, extraction, formatting,
short factual lookups, and routine summarization are handled well by a small, cheap
model. Multi-step reasoning, code generation, architecture and design, and
ambiguous open-ended tasks are where a capable model earns its price.

A router is a thin decision step in front of the model. The simplest router is a
keyword-and-length heuristic; a better one is a tiny classifier (which can itself be
the cheap model) that labels the request as easy or hard and emits a confidence. The
default route is the cheap model; the request escalates to the capable model only
when the classifier's confidence is low or the task is flagged hard. This is a
cheap-first cascade: spend a little to decide before you spend a lot.

The economics are stark. A capable tier commonly costs about five times the cheap
tier per token, in both directions. If most of your traffic is routine — and for
real assistants it usually is — routing the easy majority to the cheap model cuts
the blended cost dramatically while the rare hard request still gets full quality.
The failure mode to avoid is over-routing: if the cheap model silently mishandles a
hard request, you have traded a small saving for a wrong answer. Calibrate the
escalation threshold against real traffic and prefer to escalate when unsure.

## Lever 2 — Prompt caching (stop paying to re-read what never changes)

Most agent calls share a large stable prefix: a long system prompt, a tool catalog,
a knowledge base, retrieved documents, few-shot examples. Without caching you pay
full input price to process that identical prefix on every single call.

Prompt caching lets the provider store the processed prefix and reuse it. You mark
the end of the stable prefix with a cache control breakpoint. The first call writes
the cache (a small premium, around 1.25x the input price for the cached span); every
later call within the cache lifetime reads it at a large discount — on the order of
ten percent of the input price for that span. The volatile part of the request (the
user's actual question) goes after the breakpoint so it never invalidates the cache.

Caching is a prefix match: any byte change anywhere in the prefix invalidates
everything after it. The common silent invalidators are a timestamp or a random id
injected into the system prompt, non-deterministic JSON key ordering, and changing
the tool set between calls. Keep the prefix frozen and deterministic. Verify the
cache is working by reading the cache-read token count in the response usage; if it
is zero across repeated identical-prefix calls, something upstream is mutating the
prefix. There is also a minimum cacheable prefix (a few thousand tokens) below which
caching silently does nothing, so caching pays off precisely when the shared context
is large — which is exactly the agent case.

## Lever 3 — Context pruning and compression

Even a cached context can carry dead weight: stale tool outputs, finished sub-tasks,
verbose documents where only a paragraph matters. Pruning removes context that is no
longer load-bearing; compression replaces a long span with a shorter summary. A
cheap model can do the compression pass before the expensive model ever sees the
context, so you are not paying a frontier model to read filler. Reported compression
ratios range from four to ten times, occasionally higher, for a small accuracy cost.
Context editing (dropping old tool results) and server-side compaction (summarizing
earlier turns when you approach the context window) are the productized forms.

## Lever 4 — Budget awareness

The agent can be made aware of its own spend. A budget-aware planner tracks the
tokens and dollars consumed in the current task and adjusts behaviour as the budget
is consumed: fewer exploratory tool calls, terser intermediate reasoning, a switch
to a cheaper model for low-stakes steps, and a graceful wrap-up rather than an
open-ended loop. Hard ceilings (a maximum output per response, a maximum number of
loop iterations) prevent a runaway agent from producing a five or six figure bill
from a single unattended run, which is a real and repeatedly reported failure mode.

## A repeat cache for identical requests

Separate from provider-side prompt caching, an application-level cache can answer an
identical or near-identical request without calling the model at all. Exact-match
caching keys on a normalized form of the request and is trivially safe for
deterministic lookups. Semantic caching embeds the request and serves a stored
answer when a previous request is sufficiently similar; it catches paraphrases but
must be tuned carefully, because a wrong cache hit serves one user another user's
answer, or yesterday's truth for a question whose answer has changed. A stale cache
hit is worse than a cache miss, so apply the safe, exact levers first and add
semantic matching only with a conservative similarity threshold and clear
invalidation rules.

## Putting it together

A production cost-aware agent composes these levers. Incoming requests hit a repeat
cache; misses go to a router that picks the cheap model by default and escalates on
low confidence; the shared context is marked for prompt caching so its prefix is
billed once and read cheaply thereafter; a compression pass trims oversized context;
and a budget-aware planner keeps the whole loop inside a spend ceiling. Together
these routinely cut spend by half to ninety percent without measurably changing
answer quality, because none of them touch what the model is actually good at — they
remove waste around it. Frugality, in other words, becomes a cognitive function: the
agent does not just answer, it weighs whether the answer is worth its price.

## Measuring savings honestly

Always compute savings from real token counts returned by the API, not from
estimates. The headline percentage depends on the shape of your traffic: how
repetitive it is (more repeats means more cache and repeat-cache wins), how large
the shared context is (larger context means bigger caching wins), and how many
requests are genuinely hard (more hard requests means more unavoidable expensive
calls). Report the methodology alongside the number. The capable model still earns
its keep on the requests that need it; the goal is not to never use it, but to stop
paying its price for work the cheap model, the cache, and the compressor can do.
