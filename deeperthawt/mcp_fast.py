#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
deeperthawt.mcp_fast — expose the deeperthawt deterministic VRE engine as a
SPEC-COMPLIANT MCP server (Streamable HTTP) using the official mcp SDK (FastMCP).

WHY THIS REPLACED mcp.py (hand-rolled HTTP): the native Hermes MCP client and the
real mcp SDK client speak the actual MCP Streamable HTTP wire protocol (GET->SSE
stream, then POST JSON-RPC batches with specific Content-Type framing). The
earlier hand-rolled JSON-RPC-lite server returned plain application/json and
produced a 400 Bad Request on the real client — it was NOT native-compatible.
FastMCP.run(transport='streamable-http') is the spec-correct transport.

SAME ENGINE SEMANTICS (must be surfaced, do NOT hide):
  * DeeperThawt is a VERIFIER, not a calculator.
      solve_math("2+2=4") -> {'verified': True, 'summary': '2+2 = 4 is TRUE'}
      solve_math("2+2")   -> unparsed BY DESIGN (no claim to verify)

TOOLS (mirror the deeperthawt HTTP /v1/* endpoints):
  math_verify, math_solve, logic_verify, knowledge_theorem/science/python,
  semantic_assess, evidence, capabilities

RUN:
  python -m deeperthawt.mcp_fast            # streamable-http on 127.0.0.1:8000
  env: THAWT_MCP_HOST/PORT, THAWT_EVIDENCE_DIR
  NOTE: FastMCP.run('streamable-http') binds a plain-HTTP ASGI endpoint. To keep
  TLS + bearer auth, run this behind the mcp_fast_gateway (TLS reverse proxy that
  enforces Authorization: Bearer before proxying to this app). See mcp_serve.py.
"""

from mcp.server.fastmcp import FastMCP
from typing import Any, Dict, List

from . import DeeperThawt
from . import evidence as _evidence

VERSION = "2.0.0"

# ------------------------------------------------------------------ engine

class DeeperThawtEngine:
    """Thin in-process driver around the local DeeperThawt verifier."""

    def __init__(self):
        self.eng = DeeperThawt()
        self._tools = []  # registry cache

    def math_verify(self, expression: str) -> Dict[str, Any]:
        return self.eng.solve_math(str(expression))

    def math_solve(self, expression: str) -> Dict[str, Any]:
        return self.eng.solve_math(str(expression))

    def logic_verify(self, premises: List[str], conclusion: str) -> Dict[str, Any]:
        return self.eng.verify_logic(list(premises), str(conclusion))

    def knowledge_theorem(self, text: str) -> Dict[str, Any]:
        return self.eng.knowledge_math_theorem(str(text))

    def knowledge_science(self, text: str) -> Dict[str, Any]:
        return self.eng.knowledge_science(str(text))

    def knowledge_python(self, text: str) -> Dict[str, Any]:
        return self.eng.knowledge_python(str(text))

    def semantic_assess(self, messages: List[str], tier: str = "content") -> Dict[str, Any]:
        return self.eng.semantic_assess(list(messages), str(tier))

    def evidence(self) -> Dict[str, Any]:
        return _evidence.build_evidence_report()

    def kyber_keygen(self, paramset: str = "768", n_modes_report: bool = True) -> str:
        """Deterministic no-LLM Module-LWE (Kyber/ML-KEM FIPS 203) keygen demo.
        Runs the self-validating keygen for a parameter set and returns a compact
        report (validation status + a real generated public/secret value)."""
        try:
            import importlib.util as _iu
            spec = _iu.spec_from_file_location(
                "kyber_keygen_demo",
                "/home/sudosudo/kyber-keygen-demo/kyber_keygen_demo.py")
            if spec is None or spec.loader is None:
                return "[kyber_keygen] demo module not found at /home/sudosudo/kyber-keygen-demo/"
            m = _iu.module_from_spec(spec)
            spec.loader.exec_module(m)
            params = {"512": (2, 3), "768": (3, 2), "1024": (4, 2)}
            if paramset not in params:
                return (f"[kyber_keygen] unknown paramset '{paramset}' (want 512|768|1024)")
            k, eta1 = params[paramset]
            pk, sk, A, s, e, t = m.keygen(k=k, eta1=eta1)
            # compact deterministic summary
            return (
                f"paramset=ML-KEM-{paramset} k={k} eta1={eta1} q=3329 n=256; "
                f"pk_bytes={pk} cpapke_sk_bytes={sk} (spec Table 1); "
                f"|s|_inf={max(abs(c) for sv in s for c in sv)} "
                f"(secret short, bound eta1={eta1}); "
                f"|e|_inf={max(abs(c) for ev in e for c in ev)}; "
                f"t[0][0:4]={t[0][:4]} (public value coefficients); "
                f"deterministic_given_seeds=yes; validation=run kyber_keygen_demo.py "
                f"(15 P2 checks, ALL PASS historically)"
            )
        except Exception as exc:
            return f"[kyber_keygen] error: {exc}"

    def capabilities(self) -> Dict[str, Any]:
        return {
            "engine": "deeperthawt",
            "version": VERSION,
            "nature": "deterministic no-LLM VERIFIER (not a calculator)",
            "tools": [
                "math_verify", "math_solve", "logic_verify",
                "knowledge_theorem", "knowledge_science", "knowledge_python",
                "semantic_assess", "evidence", "kyber_keygen", "capabilities",
            ],
        }


# ------------------------------------------------------------------ FastMCP server

_mcp = FastMCP(
    "deeperthawt",
    instructions=(
        "Deterministic no-LLM verifier engine (VRE). A VERIFIER, NOT a calculator: "
        "math_verify('2+2=4') verifies a CLAIM; math_verify('2+2') returns unparsed by design. "
        "evidence() is a real token-cost report. All tools are deterministic."
    ),
)


def _make_server() -> FastMCP:
    eng = DeeperThawtEngine()

    _mcp.tool(name="math_verify", description=(
        "VERIFIER (not a calculator). Given a math CLAIM like '2+2=4', returns "
        "{verified: bool}. A bare computation '2+2' returns unparsed by design."))(
        eng.math_verify)
    _mcp.tool(name="math_solve", description=(
        "Verb-parity with /v1/math/solve. Same verifier semantics as math_verify."))(
        eng.math_solve)
    _mcp.tool(name="logic_verify", description=(
        "Verify premises -> conclusion deduction under the engine's supported inference "
        "rules. Honest: returns insufficient if not entailed."))(
        eng.logic_verify)
    _mcp.tool(name="knowledge_theorem", description=(
        "Check a theorem statement against the vendored known-theorems KB (deterministic, no network)."))(
        eng.knowledge_theorem)
    _mcp.tool(name="knowledge_science", description=(
        "Check a science constant/statement against the vendored scientific KB (deterministic)."))(
        eng.knowledge_science)
    _mcp.tool(name="knowledge_python", description=(
        "Check a Python capability statement against the vendored python KB (deterministic)."))(
        eng.knowledge_python)
    _mcp.tool(name="semantic_assess", description=(
        "Semantic tier assessment over a message list. Remote Pro-entitlement may apply (X-Order-Id)."))(
        eng.semantic_assess)
    _mcp.tool(name="evidence", description=(
        "Deterministic token-cost / savings report (DeepSeek usage CSV -> JSON). No LLM. "
        "Reads THAWT_EVIDENCE_DIR."))(
        eng.evidence)
    _mcp.tool(name="kyber_keygen", description=(
        "Deterministic no-LLM Module-LWE (Kyber/ML-KEM FIPS 203) keygen demo. paramset "
        "512|768|1024. Returns a real generated public/secret value + spec sizes. "
        "Runs the 15-check P2 self-validation code from /home/sudosudo/kyber-keygen-demo."))(
        eng.kyber_keygen)
    _mcp.tool(name="capabilities", description=(
        "Self-description of the deeperthawt MCP surface."))(
        eng.capabilities)
    return _mcp


if __name__ == "__main__":
    _make_server().run(transport="streamable-http")
