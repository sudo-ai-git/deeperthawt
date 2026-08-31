#!/usr/bin/env bash
# Keep the deeperthawt deterministic-verifier MCP server alive on :8000/mcp.
# Runs from cron every 2 minutes; the launcher is idempotent (no-op if up).
# Quiet unless the launcher reports a real failure (never spams cron mail).
set -uo pipefail
OUT=$(/home/sudosudo/deeperthawt/deeperthawt-mcp-up.sh 2>&1)
rc=$?
if [ $rc -ne 0 ]; then
  echo "[keepalive $(date -u +%FT%TZ)] $OUT" >> /home/sudosudo/deeperthawt/mcp_keepalive.log
fi
exit 0
