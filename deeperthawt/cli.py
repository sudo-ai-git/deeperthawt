"""
DeeperThawt CLI — exercise the deterministic verifiable reasoning engine.

Commands:
  deeperthawt math "<query>"         deterministic symbolic math solve
  deeperthawt logic "<premises>" "<conclusion>"
  deeperthawt theorem "<text>"       known-theorem catalog lookup
  deeperthawt science "<text>"       cited science fact retrieval
  deeperthawt python "<text>"        cited python-knowledge retrieval
  deeperthawt sim "<a>" "<b>"        semantic similarity in the engine space
  deeperthawt selfcheck              run the packaged capability smoke test
"""

from __future__ import annotations

import json
import sys


def _math(engine, q):
    return json.dumps(engine.solve_math(q), default=str)


def _logic(engine, premises, conclusion):
    return json.dumps(engine.verify_logic(premises, conclusion), default=str)


def _theorem(engine, text):
    return json.dumps(engine.knowledge_math_theorem(text), default=str)


def _science(engine, text):
    return json.dumps(engine.knowledge_science(text), default=str)


def _python(engine, text):
    return json.dumps(engine.knowledge_python(text), default=str)


def _sim(engine, a, b):
    # Semantic comparison runs ONLY on the remote server (the engine + weights
    # are not shipped locally). Returns the numeric semantic-delta result.
    rows = [
        {"role": "tool", "approx_tokens": len(a.split()), "content_scrubbed": a},
        {"role": "tool", "approx_tokens": len(b.split()), "content_scrubbed": b},
    ]
    return json.dumps(engine.semantic_assess(rows, tier="content"), default=str)


def selfcheck(engine, _none=None) -> str:
    """Smoke test: exercise every capability and report PASS/FAIL."""
    rows = []
    # math
    m = engine.solve_math("integral of x^2 from 0 to 1")
    rows.append(("math integral 0..1 x^2 solved", m.get("status") == "solved"))
    m2 = engine.solve_math("2 + 2 = 4")
    rows.append(("math verifies 2+2=4", m2.get("status") == "solved" and m2.get("verified") is True))
    m3 = engine.solve_math("2 + 2 = 5")
    rows.append(("math refutes 2+2=5", m3.get("status") == "refuted"))
    # logic
    l = engine.verify_logic(["if it rains then the ground is wet", "it rains"], "the ground is wet")
    rows.append(("logic modus-ponens valid", l.get("status") == "valid"))
    # knowledge
    rows.append(("science lookup", engine.knowledge_science("why is the sky blue").get("found", False)))
    rows.append(("python lookup", engine.knowledge_python("list comprehension").get("found", False)))
    rows.append(("theorem lookup", engine.knowledge_math_theorem("infinitely many primes").get("status") == "known_theorem"))
    # remote semantic RPC is wired (engine+weights live only on the remote server)
    rows.append(("remote semantic client wired", hasattr(engine, "semantic_assess")))
    lines = [f"[{'PASS' if ok else 'FAIL'}] {name}" for name, ok in rows]
    passed = sum(1 for _, ok in rows if ok)
    return "\n".join(lines) + f"\nDeeperThawt selfcheck: {passed}/{len(rows)} passed"


COMMANDS = {
    "math": _math,
    "logic": _logic,
    "theorem": _theorem,
    "science": _science,
    "python": _python,
    "sim": _sim,
    "selfcheck": selfcheck,
}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        from . import DeeperThawt
        engine = DeeperThawt()
    except Exception as e:  # pragma: no cover
        print(f"DeeperThawt failed to initialize: {e}", file=sys.stderr)
        return 2
    if not argv or argv[0] not in COMMANDS:
        print(__doc__)
        return 1
    cmd = argv[0]
    args = argv[1:]
    try:
        if cmd == "selfcheck":
            print(selfcheck(engine))
        else:
            func = COMMANDS[cmd]
            print(func(engine, *args))
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
