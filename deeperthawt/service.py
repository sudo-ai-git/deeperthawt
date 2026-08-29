#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
deeperthawt.service — unified deterministic verifiable-reasoning HTTP service.

MERGE (2026-08-29): folds thawt-api v1.0.0 into the deeperthawt monorepo as the
canonical service layer, calling the LOCAL DeeperThawt engine directly (no
duplicated vendored copy — the thawt-api repo held byte-identical copies of the
same 6 engine files, a dual-vendor maintenance hazard now removed), and wires
token-analytics as an /evidence endpoint (the deterministic token-cost data
product).

Endpoints (deterministic, no LLM):
  GET  /healthz
  POST /v1/math/verify        {"expression": str}
  POST /v1/math/solve         {"expression": str}
  POST /v1/logic/verify       {"premises": [str], "conclusion": str}
  POST /v1/knowledge/theorem  {"text": str}
  POST /v1/knowledge/science  {"text": str}
  POST /v1/knowledge/python   {"text": str}
  POST /v1/semantic/assess    {"messages": [...], "tier": str}
  GET  /v1/evidence           token-cost intelligence report
  GET  /v1/capabilities

Run: python -m deeperthawt.service
Env: THAWT_HOST (127.0.0.1) THAWT_PORT (8105) THAWT_API_KEY THAWT_DEBUG
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from . import DeeperThawt

VERSION = "2.0.0"          # unified product version (1.0.0 was thawt-api only)
_ENGINE = None
_ENGINE_ERR = None


def _load_engine():
    global _ENGINE, _ENGINE_ERR
    if _ENGINE is not None:
        return _ENGINE
    try:
        _ENGINE = DeeperThawt()
        return _ENGINE
    except Exception as e:  # pragma: no cover
        _ENGINE_ERR = str(e)
        _ENGINE = None
    return _ENGINE


def handle_math_verify(text: str) -> Dict[str, Any]:
    eng = _load_engine()
    if eng is None:
        return {"error": "engine_unavailable", "detail": _ENGINE_ERR}
    return eng.solve_math(str(text))


def handle_logic_verify(premises: list, conclusion: str) -> Dict[str, Any]:
    eng = _load_engine()
    if eng is None:
        return {"error": "engine_unavailable", "detail": _ENGINE_ERR}
    try:
        return eng.verify_logic([str(p) for p in premises], str(conclusion))
    except Exception as e:
        return {"error": "logic_error", "detail": str(e)}


def handle_knowledge(kind: str, text: str) -> Dict[str, Any]:
    eng = _load_engine()
    if eng is None:
        return {"error": "engine_unavailable", "detail": _ENGINE_ERR}
    if kind == "theorem":
        return eng.knowledge_math_theorem(str(text))
    if kind == "science":
        return eng.knowledge_science(str(text))
    if kind == "python":
        return eng.knowledge_python(str(text))
    return {"error": "unknown_kind", "detail": kind}


def handle_semantic(messages: list, tier: str) -> Dict[str, Any]:
    eng = _load_engine()
    if eng is None:
        return {"error": "engine_unavailable", "detail": _ENGINE_ERR}
    try:
        return eng.semantic_assess(list(messages), tier=str(tier))
    except Exception as e:
        return {"error": "semantic_error", "detail": str(e)}


def handle_evidence() -> Dict[str, Any]:
    """Deterministic token-cost intelligence (the evidence layer)."""
    try:
        from .evidence import build_evidence_report
        return build_evidence_report()
    except Exception as e:
        return {"error": "evidence_unavailable", "detail": str(e)}


def capabilities() -> Dict[str, Any]:
    return {
        "api": "deeperthawt.service",
        "version": VERSION,
        "auth": "optional bearer (THAWT_API_KEY)",
        "no_llm": True,
        "endpoints": [
            {"path": "/v1/math/verify", "method": "POST", "body": {"expression": "str"}},
            {"path": "/v1/math/solve", "method": "POST", "body": {"expression": "str"}},
            {"path": "/v1/logic/verify", "method": "POST", "body": {"premises": ["str"], "conclusion": "str"}},
            {"path": "/v1/knowledge/theorem", "method": "POST", "body": {"text": "str"}},
            {"path": "/v1/knowledge/science", "method": "POST", "body": {"text": "str"}},
            {"path": "/v1/knowledge/python", "method": "POST", "body": {"text": "str"}},
            {"path": "/v1/semantic/assess", "method": "POST", "body": {"messages": ["..."], "tier": "str"}},
            {"path": "/v1/evidence", "method": "GET"},
            {"path": "/v1/capabilities", "method": "GET"},
        ],
    }


def _json_default(o):
    if isinstance(o, (int, float, bool)):
        return o
    nm = type(o).__name__
    if nm in ("Integer", "Rational", "Float"):
        try:
            return str(o)
        except Exception:
            pass
    try:
        if hasattr(o, "evalf"):
            return float(o.evalf())
    except Exception:
        pass
    if isinstance(o, set):
        return sorted(str(x) for x in o)
    return str(o)


def _read_json(body: bytes) -> Optional[Dict[str, Any]]:
    try:
        d = json.loads(body.decode("utf-8"))
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def _require(d: Dict[str, Any], *keys: str) -> Optional[str]:
    for k in keys:
        if k not in d or d[k] is None:
            return f"missing required field: {k}"
    return None


class _Handler(BaseHTTPRequestHandler):
    server_version = "deeperthawt.service/2.0"

    def log_message(self, fmt, *args):
        if os.environ.get("THAWT_DEBUG"):
            sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def _json(self, code, obj, cors=False):
        body = json.dumps(obj, default=_json_default).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if cors:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def _auth_ok(self) -> bool:
        key = os.environ.get("THAWT_API_KEY", "")
        if not key:
            return True
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {key}"

    def do_OPTIONS(self):
        self._json(204, {}, cors=True)

    def _route(self, path, body):
        if not self._auth_ok():
            return self._json(401, {"error": "unauthorized", "detail": "THAWT_API_KEY required"})
        if path == "/v1/capabilities":
            return self._json(200, capabilities(), cors=True)
        if path == "/v1/evidence":
            return self._json(200, handle_evidence(), cors=True)
        if path in ("/v1/math/verify", "/v1/math/solve"):
            if body is None:
                return self._json(400, {"error": "invalid_json"})
            err = _require(body, "expression")
            if err:
                return self._json(400, {"error": err})
            return self._json(200, handle_math_verify(body["expression"]), cors=True)
        if path == "/v1/logic/verify":
            if body is None:
                return self._json(400, {"error": "invalid_json"})
            err = _require(body, "premises", "conclusion")
            if err:
                return self._json(400, {"error": err})
            return self._json(200, handle_logic_verify(body["premises"], body["conclusion"]), cors=True)
        m = re.fullmatch(r"/v1/knowledge/(theorem|science|python)", path)
        if m:
            if body is None:
                return self._json(400, {"error": "invalid_json"})
            err = _require(body, "text")
            if err:
                return self._json(400, {"error": err})
            return self._json(200, handle_knowledge(m.group(1), body["text"]), cors=True)
        if path == "/v1/semantic/assess":
            if body is None:
                return self._json(400, {"error": "invalid_json"})
            err = _require(body, "messages")
            if err:
                return self._json(400, {"error": err})
            return self._json(200,
                              handle_semantic(body["messages"], body.get("tier", "content")),
                              cors=True)
        return self._json(404, {"error": "not_found", "detail": path})

    def _dispatch(self):
        from urllib.parse import urlparse as _u
        path = _u(self.path).path
        if path == "/healthz":
            return self._json(200, {"status": "ok", "version": VERSION, "ts": int(time.time())})
        if path.startswith("/v1/"):
            n = int(self.headers.get("Content-Length") or 0)
            body = _read_json(self.rfile.read(n)) if n else None
            return self._route(path, body)
        return self._json(404, {"error": "not_found", "detail": path})

    def do_GET(self):
        self._dispatch()

    def do_POST(self):
        self._dispatch()


def main():
    if any(a in ("--help", "-h") for a in sys.argv[1:]):
        print(__doc__.splitlines()[1].strip())
        print("Usage: python -m deeperthawt.service [--help] [--version]")
        return 0
    if any(a in ("--version", "-V") for a in sys.argv[1:]):
        print(f"deeperthawt.service {VERSION}")
        return 0
    host = os.environ.get("THAWT_HOST", "127.0.0.1")
    port = int(os.environ.get("THAWT_PORT", "8105"))
    srv = ThreadingHTTPServer((host, port), _Handler)
    print(f"deeperthawt.service listening on http://{host}:{port} (no-LLM deterministic)", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nshutdown", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
