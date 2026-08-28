"""
DeeperThawt vendored core — re-exports the real LOCAL deterministic solvers.

The `_vendored` directory holds vendored copies of the hybrid-agi/VRE core
modules (AGPL-3.0 open core) — but ONLY the deterministic, non-secret solvers.
The semantic engine (gematria projection / attention / adapter / weights) is
deliberately NOT vendored: it lives on the remote DeeperThawt server and is
reached through a numeric-only RPC client.
"""

from __future__ import annotations

import os as _os
import sys as _sys

_V = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "_vendored")
if _V not in _sys.path:
    _sys.path.insert(0, _V)

# --- math solver (local, deterministic) ---
from math_solver_oracle import MathematicalOracle  # noqa: E402

# --- logic engine (local, deterministic) ---
from logic_engine import (  # noqa: E402
    evaluate_inference,
    verify_logic_argument,
)

# --- knowledge (local, cited retrieval) ---
from known_theorems import parse_known_theorem  # noqa: E402
from scientific_knowledge import lookup_science_fact_combined  # noqa: E402
from python_knowledge import lookup_python_knowledge_combined  # noqa: E402

__all__ = [
    "MathematicalOracle", "evaluate_inference", "verify_logic_argument",
    "parse_known_theorem", "lookup_science_fact_combined",
    "lookup_python_knowledge_combined",
]
