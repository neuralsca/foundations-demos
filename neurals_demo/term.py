"""Brand-styled terminal output for the neurals.ca demos.

Pure stdlib. Truecolor ANSI tuned to the neurals.ca palette so a screen
recording of a demo reads as on-brand SEGMENT-5 footage:

    violet  #a78bfa  (brand accent)
    teal    #2dd4bf  ("live" accent)
    white   #f0f6fc  · muted #8b949e · amber #fbbf24 (warn) · red #f87171

Helpers: banner(), rule(), step(), ok(), warn(), kv(), meter(), diff(),
table(), and typed()/type-out for on-camera typing. Honors NO_COLOR.
"""
from __future__ import annotations

import os
import sys
import time
from typing import Iterable, Sequence

_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
if os.environ.get("NEURALS_FORCE_COLOR"):
    _USE_COLOR = True

# neurals.ca palette (truecolor)
VIOLET = (167, 139, 250)
TEAL = (45, 212, 191)
WHITE = (240, 246, 252)
MUTED = (139, 148, 158)
AMBER = (251, 191, 36)
RED = (248, 113, 113)
GREEN = (52, 211, 153)


def _fg(rgb: tuple[int, int, int]) -> str:
    return f"\x1b[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m" if _USE_COLOR else ""


def _c(text: str, rgb: tuple[int, int, int], bold: bool = False) -> str:
    if not _USE_COLOR:
        return text
    b = "\x1b[1m" if bold else ""
    return f"{b}{_fg(rgb)}{text}\x1b[0m"


# Public color shortcuts ------------------------------------------------------
def violet(t: str, bold: bool = False) -> str: return _c(t, VIOLET, bold)
def teal(t: str, bold: bool = False) -> str: return _c(t, TEAL, bold)
def white(t: str, bold: bool = False) -> str: return _c(t, WHITE, bold)
def muted(t: str, bold: bool = False) -> str: return _c(t, MUTED, bold)
def amber(t: str, bold: bool = False) -> str: return _c(t, AMBER, bold)
def red(t: str, bold: bool = False) -> str: return _c(t, RED, bold)
def green(t: str, bold: bool = False) -> str: return _c(t, GREEN, bold)


def banner(title: str, subtitle: str = "") -> None:
    """A neurals.ca demo header block."""
    bar = "━" * 64
    print()
    print(violet(bar, bold=True))
    print("  " + teal("⬢ ", bold=True) + white(title, bold=True)
          + ("   " + muted(subtitle) if subtitle else ""))
    print("  " + muted("neurals.ca · Visualizing Agentic AI"))
    print(violet(bar, bold=True))


def rule(label: str = "") -> None:
    line = "─" * (62 - len(label))
    if label:
        print(teal("── ") + white(label, bold=True) + " " + muted(line))
    else:
        print(muted("─" * 64))


_STEP_N = 0


def step(text: str, reset: bool = False) -> None:
    """A numbered pipeline step (violet index)."""
    global _STEP_N
    if reset:
        _STEP_N = 0
    _STEP_N += 1
    print(violet(f"  [{_STEP_N}] ", bold=True) + white(text))


def ok(text: str) -> None: print(green("  ✓ ") + white(text))
def warn(text: str) -> None: print(amber("  ! ") + white(text))
def fail(text: str) -> None: print(red("  ✗ ") + white(text))
def info(text: str) -> None: print(muted("    " + text))


def kv(key: str, value: str, accent: str = "teal") -> None:
    color = {"teal": teal, "violet": violet, "amber": amber,
             "green": green, "red": red}.get(accent, teal)
    print("  " + muted(f"{key:<18}") + color(str(value), bold=True))


def meter(label: str, value: float, maximum: float, width: int = 32,
          accent: str = "teal", suffix: str = "") -> None:
    """A horizontal bar meter, e.g. for a token/cost budget."""
    frac = 0.0 if maximum <= 0 else max(0.0, min(1.0, value / maximum))
    fill = int(round(frac * width))
    color = teal if accent == "teal" else (violet if accent == "violet"
            else (amber if accent == "amber" else (green if accent == "green" else red)))
    bar = color("█" * fill) + muted("░" * (width - fill))
    print(f"  {muted(label):<22} {bar} {color(suffix or f'{value:g}/{maximum:g}', bold=True)}")


def table(rows: Sequence[Sequence[str]], headers: Sequence[str] | None = None) -> None:
    """Simple aligned table with a violet header row."""
    cols = list(zip(*([headers] + list(rows)))) if headers else list(zip(*rows))
    widths = [max(len(str(c)) for c in col) for col in cols]
    if headers:
        print("  " + "  ".join(violet(str(h).ljust(w), bold=True) for h, w in zip(headers, widths)))
        print("  " + "  ".join(muted("─" * w) for w in widths))
    for row in rows:
        print("  " + "  ".join(white(str(c).ljust(w)) for c, w in zip(row, widths)))


def diff(before: str, after: str) -> None:
    """A minimal red/green unified-ish diff for code-fix demos."""
    for line in before.splitlines():
        print(red("  - " + line))
    for line in after.splitlines():
        print(green("  + " + line))


def typed(text: str, delay: float = 0.012, color=white) -> None:
    """Type text out character-by-character (on-camera effect). Respects speed env."""
    delay = float(os.environ.get("NEURALS_TYPE_DELAY", delay))
    for ch in text:
        sys.stdout.write(color(ch) if _USE_COLOR else ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


class Term:
    """Namespaced handle if you prefer `t = Term(); t.step(...)`."""
    banner = staticmethod(banner)
    rule = staticmethod(rule)
    step = staticmethod(step)
    ok = staticmethod(ok)
    warn = staticmethod(warn)
    fail = staticmethod(fail)
    info = staticmethod(info)
    kv = staticmethod(kv)
    meter = staticmethod(meter)
    table = staticmethod(table)
    diff = staticmethod(diff)
    typed = staticmethod(typed)
    violet = staticmethod(violet)
    teal = staticmethod(teal)
    white = staticmethod(white)
    muted = staticmethod(muted)
    amber = staticmethod(amber)
    red = staticmethod(red)
    green = staticmethod(green)
