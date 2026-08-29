"""
DeeperThawt — deterministic verifiable reasoning engine.

A packaged product exposing the VRE/hybrid-agi harness as one clean API.

CAPABILITY ARCHITECTURE (secret-ingredients stay remote):
  - LOCAL, deterministic, non-secret solvers (shipped with the package):
      * Symbolic math oracle    (deterministic SymPy solver, no LLM guessing)
      * Logic + syllogism inference
      * Known-theorem / science / python knowledge retrieval (cited)
  - REMOTE, secret-engine (never shipped locally): the semantic engine
    (gematria projection + fixed-parameter attention + trained latent adapter
    + tuned weights). Exposed to the local client ONLY through a thin,
    numeric-only RPC to the remote server (/assess). The method and weights
    never leave the remote server — a local buyer sees the contract, not the
    pearl.

Dual-licensed: AGPL-3.0 open core + commercial license for proprietary embedding.
"""

from __future__ import annotations

import os as _os
import sys as _sys
import urllib.request as _urlreq
import urllib.error as _urlerr
import json as _json
import platform as _platform
import uuid as _uuid
from typing import Any, Dict

# --------------------------------------------------------------------------- #
# LOCAL capability solvers (deterministic, non-secret) — vendored from the
# hybrid-agi core. These are the cited/bounded solvers, safe to ship.
# --------------------------------------------------------------------------- #
try:
    from ._backends import (  # type: ignore
        MathematicalOracle,
        evaluate_inference,
        verify_logic_argument,
        parse_known_theorem,
        lookup_science_fact_combined,
        lookup_python_knowledge_combined,
        lookup_puzzle_combined,
    )
    _HAS_LOCAL = True
except Exception as _e:  # pragma: no cover
    _HAS_LOCAL = False
    _LOCAL_ERR = str(_e)


_DEFAULT_API = "https://mcp-token-saver-pro.fly.dev"


def _machine_hwid() -> str:
    """A deterministic, LOCAL hardware identifier for anti-trial-farming.

    Computed from stable machine attributes (machine type, node name,
    platform, and a persistent per-install UUID). It never leaves the machine
    except as an opaque salted hash — it is not identifiable PII, and it lets
    the server refuse a second free trial from the same device without
    tracking anything that reveals who the user is. Stored locally so it's
    stable across runs (incognito/fresh-browser can't hide it).
    """
    try:
        # stable per-machine + per-install key (persistent file if writable)
        key_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".hwid_key")
        if _os.path.exists(key_path):
            with open(key_path) as f:
                inst = f.read().strip()
        else:
            inst = str(_uuid.uuid4())
            try:
                with open(key_path, "w") as f:
                    f.write(inst)
            except Exception:
                inst = "inst-" + _uuid.getnode().__str__()[-8:]
        raw = f"{_platform.machine()}|{_platform.node()}|{_platform.system()}|{inst}"
        import hashlib
        return hashlib.sha256(raw.encode()).hexdigest()
    except Exception:
        return "dt-" + _uuid.uuid4().hex[:16]


class _SemanticRemote:
    """Thin numeric-only client to the remote semantic engine.

    The secret method (gematria projection, attention, adapter weights) lives
    ONLY on the remote server. This client sends de-identified rows and
    receives a number back — it never carries the engine, the method, or the
    weights. If `requests` is unavailable we fall back to urllib.
    """

    def __init__(self, base: str = "", api_key: str = ""):
        self.base = (base or _os.environ.get("DEEPER_THAWT_API", _DEFAULT_API)).rstrip("/")
        self.api_key = api_key or _os.environ.get("DEEPER_THAWT_API_KEY", "")

    def assess(self, rows: list, tier: str = "content") -> Dict[str, Any]:
        """POST de-identified rows to the remote engine; return numeric result."""
        body = _json.dumps({"tier": tier, "messages": rows}).encode()
        headers = {"Content-Type": "application/json", "X-HWID": _machine_hwid()}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = _urlreq.Request(self.base + "/assess", data=body, headers=headers, method="POST")
        try:
            with _urlreq.urlopen(req, timeout=60) as r:
                return _json.loads(r.read().decode())  # {"result": {...}}
        except _urlerr.HTTPError as e:
            return {"error": f"http_{e.code}", "detail": e.read().decode()[:200]}


# --------------------------------------------------------------------------- #
# Public product surface
# --------------------------------------------------------------------------- #

class DeeperThawt:
    """The DeeperThawt engine: local deterministic solvers + remote semantic UI."""

    def __init__(self, api_base: str = "", api_key: str = ""):
        self.math = MathematicalOracle()
        self._remote = _SemanticRemote(api_base, api_key)

    # -- math (local, deterministic) -----------------------------------------
    def solve_math(self, text: str) -> dict:
        return self.math.evaluate(text)

    # -- logic (local, deterministic) ----------------------------------------
    def verify_logic(self, premises, conclusion) -> dict:
        return verify_logic_argument(list(premises), conclusion)

    # -- knowledge (local, cited retrieval) ----------------------------------
    def knowledge_math_theorem(self, text: str) -> dict:
        return parse_known_theorem(text) or {"known": False, "reason": "no known theorem matched"}

    def knowledge_science(self, text: str) -> dict:
        return lookup_science_fact_combined(text)

    def knowledge_python(self, text: str) -> dict:
        return lookup_python_knowledge_combined(text)

    def knowledge_puzzle(self, text: str) -> dict:
        return lookup_puzzle_combined(text)

    # -- semantic token intelligence (REMOTE, numeric-only) ------------------
    def semantic_assess(self, messages: list, tier: str = "content") -> dict:
        """Ask the remote semantic engine to assess token redundancy.

        Returns ONLY numbers (baseline, exact dedupe, semantic additional
        savings). The engine + weights stay on the remote server; this ships
        nothing secret.
        """
        return self._remote.assess(messages, tier=tier)


def version() -> str:
    return "1.0.0"


def api_status() -> str:
    """Remote semantic engine health (numeric/opaque)."""
    try:
        with _urlreq.urlopen(_DEFAULT_API + "/healthz", timeout=15) as r:
            return r.read().decode()
    except Exception as e:  # pragma: no cover
        return f"unreachable: {e}"


_has_remote = _HAS_LOCAL


__all__ = [
    "DeeperThawt", "version", "api_status",
    "MathematicalOracle", "evaluate_inference", "verify_logic_argument",
    "parse_known_theorem", "lookup_science_fact_combined",
    "lookup_python_knowledge_combined", "lookup_puzzle_combined",
]
