"""neurals_demo - shared helpers for the neurals.ca Playlist 1 code demos.

Local-first: everything talks to a local Ollama server over its HTTP API using
only the Python standard library, so the demos run offline with no API key and
no pip install. Model names are env-configurable; see llm.py.

Public surface:
    from neurals_demo import llm, term, react
    from neurals_demo.llm import chat, generate, embed, vision
    from neurals_demo.term import Term, banner, rule, step, meter, kv, diff
    from neurals_demo.react import Tool, run_react
"""
from . import llm, term, react  # noqa: F401

__all__ = ["llm", "term", "react"]
