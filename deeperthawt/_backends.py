"""
DeeperThawt vendored capability backends — LOCAL, deterministic, NON-SECRET.

This module bundles the minimal, self-contained deterministic solvers from the
VRE/hybrid-agi harness so the pip package stands alone:

  - MathematicalOracle + fib helper (deterministic SymPy math solver)
  - logic_engine inference + syllogism (propositional + category logic)
  - known_theorems / science / python knowledge retrieval (cited)

SECRET-INGREDIENT POLICY: the semantic engine (gematria projection +
fixed-parameter attention + trained latent adapter + tuned weights) lives ONLY
on the remote DeeperThawt server and is intentionally NOT vendored here. The
local package ships only a numeric-only RPC client to that server.

AGPL-3.0 open core; commercial license for proprietary embedding.
"""

from __future__ import annotations

import os as _os
import sys as _sys

# Make the vendored deterministic core importable by absolute module names.
_HARNESS = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "_vendored")
if _HARNESS not in _sys.path:
    _sys.path.insert(0, _HARNESS)

# Re-export the real local solvers (NO semantic engine — it stays remote).
from ._backends_core import (  # noqa: E402
    MathematicalOracle,
    evaluate_inference,
    verify_logic_argument,
    parse_known_theorem,
    lookup_science_fact_combined,
    lookup_python_knowledge_combined,
    lookup_puzzle_combined,
)

# Safety: if anyone tries to vendored-import the semantic engine here it must
# not be present. GematriaTokenizer / SemanticSpace / adapter are NOT exported.

__all__ = [
    "MathematicalOracle", "evaluate_inference", "verify_logic_argument",
    "parse_known_theorem", "lookup_science_fact_combined",
    "lookup_python_knowledge_combined", "lookup_puzzle_combined",
]
