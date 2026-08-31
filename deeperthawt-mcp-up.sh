#!/usr/bin/env bash
# Start the deeperthawt deterministic-verifier FastMCP server (streamable-http
# on 127.0.0.1:8000/mcp) if it isn't already running. Idempotent.
#
# The native Hermes MCP client (config mcp_servers.deeperthawt) connects to
# http://127.0.0.1:8000/mcp at FIRST SESSION START — so run this (or add it to
# your shell profile) before launching a Hermes session that needs the tools.
#
# Tools exposed (mcp_deeperthawt_*): math_verify, math_solve, logic_verify,
# knowledge_theorem/science/python, semantic_assess, evidence, capabilities.
set -euo pipefail
URL="http://127.0.0.1:8000/mcp"
if curl -sf -o /dev/null "$URL" 2>/dev/null; then
  echo "deeperthawt MCP already up at $URL"
  exit 0
fi
cd /home/sudosudo/deeperthawt
nohup python3 -c "from deeperthawt.mcp_fast import _make_server; _make_server().run(transport='streamable-http')" \
  >> /home/sudosudo/deeperthawt/mcp_fast.log 2>&1 &
for i in $(seq 1 20); do
  sleep 0.5
  if curl -sf -o /dev/null "$URL" 2>/dev/null; then
    echo "deeperthawt MCP up at $URL (pid $!)"
    exit 0
  fi
done
echo "WARNING: deeperthawt MCP did not respond within 10s; check mcp_fast.log" >&2
exit 1
