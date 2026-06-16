"""Local-first LLM access for the neurals.ca demos.

Talks to a local Ollama server (default http://localhost:11434) over its HTTP
API using ONLY the standard library (urllib + json). No pip install, no API key.

Model defaults are env-configurable so a demo runs against whatever you have
pulled:

    NEURALS_OLLAMA_MODEL   chat / reasoning model   (default: llama3.1)
    NEURALS_EMBED_MODEL    embedding model          (default: nomic-embed-text)
    NEURALS_VISION_MODEL   multimodal model         (default: llama3.2-vision)
    OLLAMA_HOST            host:port or full URL    (default: localhost:11434)

Pull what a demo needs once, e.g.:
    ollama pull llama3.1
    ollama pull nomic-embed-text
    ollama pull llama3.2-vision

Every call raises OllamaUnavailable with a friendly hint if the server is down
or the model is missing, so demos can fail loudly but cleanly on camera.
"""
from __future__ import annotations

import base64
import json
import math
import os
import time
import urllib.error
import urllib.request
from typing import Any, Iterable, Iterator


class OllamaUnavailable(RuntimeError):
    """Raised when the Ollama server is unreachable or a model is missing."""


def _base_url() -> str:
    host = os.environ.get("OLLAMA_HOST", "localhost:11434").rstrip("/")
    if not host.startswith("http"):
        host = "http://" + host
    return host


def chat_model() -> str:
    return os.environ.get("NEURALS_OLLAMA_MODEL", "llama3.1")


def embed_model() -> str:
    return os.environ.get("NEURALS_EMBED_MODEL", "nomic-embed-text")


def vision_model() -> str:
    return os.environ.get("NEURALS_VISION_MODEL", "llama3.2-vision")


def _post(path: str, payload: dict[str, Any], timeout: float = 600.0) -> dict[str, Any]:
    url = _base_url() + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise OllamaUnavailable(
            f"Could not reach Ollama at {_base_url()} ({e}). "
            "Is it running?  Start it with `ollama serve` (or open the Ollama app)."
        ) from e
    except urllib.error.HTTPError as e:  # pragma: no cover - network dependent
        body = e.read().decode("utf-8", "replace")
        if "not found" in body.lower() or e.code == 404:
            raise OllamaUnavailable(
                f"Model not found on the Ollama server: {body}. "
                "Pull it first, e.g. `ollama pull llama3.1`."
            ) from e
        raise OllamaUnavailable(f"Ollama HTTP {e.code}: {body}") from e


# ---------------------------------------------------------------------------
# Chat / generate
# ---------------------------------------------------------------------------

def chat(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.2,
    tools: list[dict] | None = None,
    **options: Any,
) -> dict[str, Any]:
    """Single (non-streaming) chat turn.

    Returns the raw Ollama response dict. The assistant text is at
    response["message"]["content"]; token counts at ["prompt_eval_count"] and
    ["eval_count"]. If `tools` is passed, native tool calls (when the model
    supports them) are at response["message"].get("tool_calls").
    """
    payload: dict[str, Any] = {
        "model": model or chat_model(),
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, **options},
    }
    if tools:
        payload["tools"] = tools
    return _post("/api/chat", payload)


def say(prompt: str, system: str | None = None, **kw: Any) -> str:
    """Convenience: send one user prompt, return just the assistant text."""
    msgs: list[dict[str, str]] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return chat(msgs, **kw)["message"]["content"]


def generate(prompt: str, model: str | None = None, temperature: float = 0.2, **options: Any) -> str:
    """Raw completion via /api/generate; returns the text."""
    payload = {
        "model": model or chat_model(),
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, **options},
    }
    return _post("/api/generate", payload).get("response", "")


def chat_stream(
    messages: list[dict[str, str]], model: str | None = None, temperature: float = 0.2, **options: Any
) -> Iterator[str]:
    """Stream assistant text token-by-token (nice for on-camera typing)."""
    payload = {
        "model": model or chat_model(),
        "messages": messages,
        "stream": True,
        "options": {"temperature": temperature, **options},
    }
    url = _base_url() + "/api/chat"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            for line in resp:
                line = line.strip()
                if not line:
                    continue
                chunk = json.loads(line)
                piece = chunk.get("message", {}).get("content", "")
                if piece:
                    yield piece
                if chunk.get("done"):
                    break
    except urllib.error.URLError as e:
        raise OllamaUnavailable(f"Could not reach Ollama at {_base_url()} ({e}).") from e


# ---------------------------------------------------------------------------
# Embeddings (used by the semantic-cache and memory demos)
# ---------------------------------------------------------------------------

def embed(text: str, model: str | None = None) -> list[float]:
    """Return an embedding vector for `text` via the embedding model."""
    resp = _post("/api/embeddings", {"model": model or embed_model(), "prompt": text})
    vec = resp.get("embedding")
    if not vec:
        raise OllamaUnavailable(
            f"No embedding returned by model {model or embed_model()!r}. "
            "Pull an embedding model: `ollama pull nomic-embed-text`."
        )
    return vec


def cosine(a: Iterable[float], b: Iterable[float]) -> float:
    """Cosine similarity between two vectors (stdlib only)."""
    a = list(a)
    b = list(b)
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return 0.0 if na == 0 or nb == 0 else dot / (na * nb)


# ---------------------------------------------------------------------------
# Vision (used by the multimodal demo)
# ---------------------------------------------------------------------------

def vision(prompt: str, image_path: str, model: str | None = None, temperature: float = 0.2) -> str:
    """Ask a multimodal model about a local image. Returns the assistant text."""
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    resp = chat(
        [{"role": "user", "content": prompt, "images": [b64]}],
        model=model or vision_model(),
        temperature=temperature,
    )
    return resp["message"]["content"]


# ---------------------------------------------------------------------------
# Token accounting helper (used by the cost-aware demo)
# ---------------------------------------------------------------------------

def usage(response: dict[str, Any]) -> dict[str, int]:
    """Pull prompt/output/total token counts out of an Ollama chat response."""
    pin = int(response.get("prompt_eval_count", 0) or 0)
    out = int(response.get("eval_count", 0) or 0)
    return {"input": pin, "output": out, "total": pin + out}


def ping() -> bool:
    """True if the Ollama server answers. Use for a friendly pre-flight check."""
    try:
        req = urllib.request.Request(_base_url() + "/api/tags")
        with urllib.request.urlopen(req, timeout=5):
            return True
    except Exception:
        return False


def wait_until_ready(seconds: float = 0) -> bool:
    """Optionally block briefly until the server is up; returns readiness."""
    deadline = time.time() + seconds
    while True:
        if ping():
            return True
        if time.time() >= deadline:
            return False
        time.sleep(0.5)
