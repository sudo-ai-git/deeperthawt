#!/usr/bin/env python3
"""Curated Python programming-knowledge lookup.

A referenced fact/idiom table for the Python language — stdlib, idioms,
pitfalls, concurrency, typing, performance, packaging. This is *referenced
retrieval*, NOT code generation or code reasoning: it tells you the documented
fact/idiom and where the authoritative reference is, then abstains when the
question is outside the table (e.g. "what is the bug in this snippet?" is
deferred to the separate code-execution oracle, not guessed here).

Scope note: this answers "how do I do X in Python" as a lookup with a
reference. It does NOT write, debug, or reason about code. It will NOT
generate a Python program. For executing/verifying snippets, the system has a
separate code_execution oracle; this table is purely knowledge retrieval.
"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional


KNOWLEDGE: List[Dict[str, Any]] = [
    {"keys": ["list comprehens", "comprehension"],
     "fact": ("A list comprehension is a concise way to build a list from an "
              "iterable: [expr for item in iterable if condition]. It is more "
              "readable and usually faster than an equivalent for-loop appending "
              "to a list."),
     "example": "squares = [x**2 for x in range(10) if x % 2 == 0]",
     "reference": "Python tutorial, 'List Comprehensions' (docs.python.org/tutorial/datastructures).",
     "hidden_pitfall": ("Comprehensions create a new list eagerly (memory cost); "
                        "use a generator expression (expr for ...) for laziness over "
                        "large inputs.")},
    {"keys": ["generator", "yield", "lazy"],
     "fact": ("A generator is a function using 'yield' (or a generator expression) "
              "that produces values lazily, one at a time, without storing the "
              "whole sequence in memory."),
     "example": "def count(n):\n    for i in range(n):\n        yield i",
     "reference": "Python tutorial, 'Generators' (docs.python.org/howto/functional).",
     "hidden_pitfall": "A generator is single-use: once exhausted it cannot be iterated again."},
    {"keys": ["dict default", "getdefault", "setdefault", "defaultdict", "missing key", "keyerror", "dict key"],
     "fact": ("d.get(key, default) returns a default instead of raising KeyError; "
              "d.setdefault(key, default) inserts the key if absent. collections."
              "defaultdict(factory) auto-creates missing entries on access."),
     "reference": "Python docs: dict.get / dict.setdefault; collections.defaultdict.",
     "hidden_pitfall": "'in' membership is O(1) average for dicts but O(n) for lists — don't use lists for lookups."},
    {"keys": ["with statement", "context manager", "__enter__", "__exit__"],
     "fact": ("The 'with' statement ensures a context manager's __exit__ runs "
              "even on exceptions — standard for files, locks, and transactions."),
     "example": "with open('f.txt') as f:\n    data = f.read()",
     "reference": "Python tutorial, 'Context Managers'; PEP 343.",
     "hidden_pitfall": "Always close files/acquire-and-release locks via 'with', not manual try/finally."},
    {"keys": ["gil", "global interpreter lock", "thread safety"],
     "fact": ("The CPython Global Interpreter Lock (GIL) allows only one thread "
              "to execute Python bytecode at a time, so pure-Python threads do "
              "not give CPU-parallel speedups. Use multiprocessing or async for "
              "that; threading is fine for I/O-bound work."),
     "reference": "Python docs, 'Glossary: GIL'; PEP 703 (free-threaded CPython).",
     "hidden_pitfall": "Threads share memory and can still race on object state; the GIL protects memory, not your logic."},
    {"keys": ["async", "await", "asyncio", "coroutine"],
     "fact": ("asyncio provides single-threaded concurrent I/O via coroutines "
              "(async def) and event awaitables. 'await' suspends the task until "
              "the awaited future resolves, enabling many I/O ops concurrently."),
     "reference": "Python docs: asyncio module; PEP 492.",
     "hidden_pitfall": "blocking calls (time.sleep, requests) inside async code block the whole event loop — use asyncio.sleep / async clients."},
    {"keys": ["type hint", "typing", "optional", "dataclass", "@dataclass"],
     "fact": ("Type hints (PEP 484) annotate signatures; typing.Optional[X] == "
              "X | None; @dataclass (PEP 557) auto-generates __init__/__repr__/"
              "__eq__ from annotated fields."),
     "example": "from dataclasses import dataclass\n\n@dataclass\nclass Point:\n    x: int\n    y: int",
     "reference": "PEP 484, PEP 557, PEP 604 (X | Y union syntax); docs.python.org dataclasses.",
     "hidden_pitfall": "Hints are NOT enforced at runtime by default — they're documentation for static checkers (mypy)."},
    {"keys": ["finally", "try", "except", "catch", "exceptions", "raise exception"],
     "fact": ("try/except/else/finally handles errors; 'except (A, B):' catches "
              "multiple types; 'raise from' chains exceptions for cause tracking; "
              "'finally' always runs (cleanup)."),
     "reference": "Python tutorial, 'Errors and Exceptions'.",
     "hidden_pitfall": "Catching bare 'except:' swallows KeyboardInterrupt/SystemExit — catch specific exceptions."},
    {"keys": ["f-string", "format", "string interpolation"],
     "fact": ("f-strings (PEP 498) embed expressions in strings: f'{value}' with "
              "format specs like :.2f; they are faster and more readable than "
              "%-formatting or str.format()."),
     "reference": "PEP 498; Python docs, 'Formatted string literals'.",
     "hidden_pitfall": "Do not build queries via naive f-string interpolation of untrusted input — SQL/path injection risk."},
    {"keys": ["list.sort", "sorted", "sort", "key function", "lambda sort", "sorting"],
     "fact": ("list.sort() sorts in place (O(n log n), stable); sorted() returns a "
              "new list. Both accept key=callable for sort-by-derived-value and "
              "reverse=bool. Tuples sort lexicographically."),
     "example": "items.sort(key=lambda x: x[1])",
     "reference": "docs.python.org HowTo Sorting.",
     "hidden_pitfall": "Sort with a 'key' function, not hand-written comparison lambdas (faster + no cmp wrangling)."},
    {"keys": ["packaging", "pip", "virtualenv", "site-packages", "requirements"],
     "fact": ("pip installs packages from PyPI into site-packages; virtualenv/venv "
              "isolate per-project dependencies; requirements.txt pins versions; "
              "pyproject.toml (PEP 621) is the modern project-metadata standard."),
     "reference": "Python Packaging User Guide; PEP 621.",
     "hidden_pitfall": "Pin transitive deps (pip freeze / lockfile); unpinned requirements rebuild differently tomorrow."},
    {"keys": ["memory", "reference counting", "garbage collection", "circular reference", "weakref"],
     "fact": ("CPython manages memory via reference counting with a cycle-detecting "
              "garbage collector for circular references; weakref / weak references "
              "hold a non-owning reference (doesn't keep the object alive)."),
     "reference": "CPython source (Modules/gcmodule); docs.python.org weakref.",
     "hidden_pitfall": "Circular references (a->b, b->a) need the GC, not just refcounting — they leak if uncollected."},
    {"keys": ["pathlib", "Path", "file path"],
     "fact": ("pathlib.Path(x) / 'sub' builds paths cross-platform; .exists(), "
              ".read_text(), .iterdir(), .glob('*.py') are the idiomatic file ops "
              "over raw os.path string joining."),
     "reference": "PEP 428; docs.python.org pathlib.",
     "hidden_pitfall": "Use pathlib over os.path concatenation for portability and clarity."},
    {"keys": ["datetime", "timezone", "aware datetime", "utc", "timezone aware"],
     "fact": ("datetime.now() returns a naive local time; datetime.now(timezone.utc) "
              "gives an aware time. Prefer aware datetimes (store UTC) to avoid "
              "DST/zone bugs; zoneinfo (PEP 615) provides tz data."),
     "reference": "docs.python.org datetime; PEP 615 (zoneinfo).",
     "hidden_pitfall": "Never compare or store naive local times across timezones — always make times timezone-aware."},
    {"keys": ["global", "nonlocal", "scope", "closure"],
     "fact": ("'global x' declares a module-level name; 'nonlocal x' rebinds a "
              "name from the enclosing (non-global) function; closures capture "
              "enclosing variables by reference."),
     "reference": "Python tutorial, 'More on scopes'; PEP 3104 (nonlocal).",
     "hidden_pitfall": "Assigning to a name inside a function makes it local unless declared global/nonlocal — surprising NameError."},
    {"keys": ["mutable default", "default argument", "arguments"],
     "fact": ("Default argument values are evaluated ONCE at def time, so a mutable "
              "default (def f(x=[])) is shared across calls and accumulates — a "
              "classic bug. Use None + create inside."),
     "example": "def f(x=None):\n    x = [] if x is None else x",
     "reference": "Python docs FAQ, 'Why are default arguments evaluated at definition time?'.",
     "hidden_pitfall": "This is one of the most common Python surprises; the fix is None-default + late binding."},
    {"keys": ["if __name__", "main guard", "__main__"],
     "fact": ("'if __name__ == \"__main__\":' runs a block only when the file is "
              "executed directly (not imported), letting a module be both importable "
              "and runnable."),
     "reference": "docs.python.org, 'The name of the main module'.",
     "hidden_pitfall": "Without the guard, import silently executes top-level side effects — keep imports side-effect-free."},
    {"keys": ["deepcopy", "copy", "shallow copy", "mutating list"],
     "fact": ("list(b) / b[:] and dict(b) make shallow copies (shared inner "
              "objects); copy.deepcopy(b) makes a deep copy. 'b = a' is an alias, "
              "not a copy — mutating b mutates a."),
     "reference": "docs.python.org copy module.",
     "hidden_pitfall": "Aliasing surprise: b = a and then b.append(...) also changes a — use a.copy() / list(a)."},
]


def lookup_python_knowledge(text: str) -> Optional[Dict[str, Any]]:
    """Return the referenced Python knowledge entry for a known topic, else None."""
    if not text:
        return None
    t = text.lower()
    # Abstain on code-generation requests ("write/generate a ... in python"):
    # this oracle retrieves documented facts, it does not write code (that is
    # the separate code-execution oracle's job).
    if (re.search(r"\b(write|generate|implement|create)\b.*\bin python\b", t)
            or re.search(r"\bcod(e|ing)\b.*\b(write|generate|implement|create)\b", t)):
        return None
    for entry in KNOWLEDGE:
        if any(k in t for k in entry["keys"]):
            return dict(entry)  # copy, no mutation
    return None


def lookup_python_knowledge_combined(text: str) -> Dict[str, Any]:
    """Oracle-friendly lookup result."""
    entry = lookup_python_knowledge(text)
    if entry is None:
        return {"status": "no_python_knowledge", "found": False}
    return {
        "status": "python_knowledge",
        "found": True,
        "fact": entry["fact"],
        "example": entry.get("example", ""),
        "reference": entry["reference"],
        "pitfall": entry.get("hidden_pitfall", ""),
        "note": "Referenced Python-knowledge retrieval; NOT code generation or code reasoning.",
    }


# quick self-test
if __name__ == "__main__":
    for q in [
        "how do list comprehensions work in python",
        "what is a generator and how does yield work",
        "how do I set a default for a dict key",
        "what does the with statement do",
        "is there a GIL in python threading",
        "how does asyncio async await work",
        "what is a dataclass in python",
        "how do I catch exceptions in python",
        "what is an f-string",
        "how do I sort a list by a key",
        "how do I set up a requirements.txt / venv",
        "what is the mutable default argument bug",
        "write a merge sort in python",  # should abstain (code-gen, not lookup)
        "explain quantum entanglement",   # not python -> abstain
    ]:
        r = lookup_python_knowledge_combined(q)
        print(f"  [{r['status']:20}] {q[:46]:48} ref={(r.get('reference') or '')[:34]}")
