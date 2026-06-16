"""A tiny, framework-free ReAct agent loop.

This is the bare skeleton the Playlist 1 demos use to show "an agent is just a
loop + tools + a stop condition" WITHOUT pulling in LangChain/CrewAI. The model
emits plain-text actions which we parse, run, and feed back as observations:

    Thought: <reasoning>
    Action: <tool_name>
    Action Input: <args>
    ...observation appended...
    Final Answer: <answer>

It is deliberately small and readable so it can be shown on screen. Tools are
plain Python callables wrapped in Tool(). Works with any Ollama chat model.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from . import llm, term


@dataclass
class Tool:
    name: str
    description: str
    func: Callable[[str], str]

    def __call__(self, arg: str) -> str:
        return str(self.func(arg))


_SYS = """You are a small reasoning agent. Solve the task using the available tools.
Respond in EXACTLY this format, one block at a time:

Thought: <your reasoning>
Action: <one tool name from the list, or "none">
Action Input: <the input string for the tool>

After you receive an Observation, continue with another Thought/Action, or finish with:

Thought: <final reasoning>
Final Answer: <the answer for the user>

Available tools:
{tools}

Use one Action per step. Do not invent tools. Keep thoughts short."""


_ACTION_RE = re.compile(r"Action:\s*(.+?)\s*[\r\n]+Action Input:\s*(.*?)(?:\n\n|\nThought:|\Z)", re.S)
_FINAL_RE = re.compile(r"Final Answer:\s*(.*)", re.S)


def run_react(task: str, tools: list[Tool], model: str | None = None,
              max_steps: int = 6, show: bool = True) -> str:
    """Run the loop and return the final answer. Narrates each step when show=True."""
    tool_list = "\n".join(f"- {t.name}: {t.description}" for t in tools)
    by_name = {t.name: t for t in tools}
    messages = [
        {"role": "system", "content": _SYS.format(tools=tool_list)},
        {"role": "user", "content": f"Task: {task}"},
    ]

    for i in range(max_steps):
        reply = llm.chat(messages, model=model, temperature=0.1)["message"]["content"]

        final = _FINAL_RE.search(reply)
        if final:
            answer = final.group(1).strip()
            if show:
                term.ok(f"Final Answer: {answer}")
            return answer

        m = _ACTION_RE.search(reply)
        if show:
            thought = reply.split("Action:")[0].replace("Thought:", "").strip()
            if thought:
                term.info(f"thought · {thought[:120]}")
        if not m:
            # No parseable action and no final answer; nudge once then stop.
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": "Use an Action, or give a Final Answer."})
            continue

        name, arg = m.group(1).strip(), m.group(2).strip()
        if name.lower() == "none":
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": "Give a Final Answer now."})
            continue

        tool = by_name.get(name)
        if not tool:
            obs = f"Error: unknown tool {name!r}. Choose from: {', '.join(by_name)}."
        else:
            if show:
                term.step(f"{term.teal(name)}({arg})")
            try:
                obs = tool(arg)
            except Exception as e:  # tools should never crash the loop
                obs = f"Error running {name}: {e}"
        if show:
            term.info(f"observation · {str(obs)[:160]}")
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"Observation: {obs}"})

    return "(stopped: reached max steps without a Final Answer)"
