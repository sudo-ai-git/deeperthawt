#!/usr/bin/env python3
"""Verify the RESTARTED deeperthawt MCP server exposes + runs kyber_keygen."""
import asyncio, sys, httpx

async def main():
    url = "http://127.0.0.1:8000/mcp"
    try:
        from mcp.client.streamable_http import streamablehttp_client
        from mcp import ClientSession
        def factory(headers=None, timeout=None, auth=None):
            return httpx.AsyncClient(timeout=timeout or 15.0, auth=auth)
    except Exception as e:
        print("SETUP FAIL", e); return 1
    try:
        async with streamablehttp_client(url, httpx_client_factory=factory) as (r, w, _):
            async with ClientSession(r, w) as s:
                tools = await s.list_tools()
                names = [t.name for t in tools.tools]
                print("list_tools:", names)
                if "kyber_keygen" not in names:
                    print("FAIL: kyber_keygen not exposed (server may be running OLD code)")
                    return 1
                for ps in ["512", "768", "1024", "999"]:
                    res = await s.call_tool("kyber_keygen", {"paramset": ps})
                    print(f"kyber_keygen({ps}) ->", [getattr(c,'text','?') for c in res.content][0][:200])
                return 0
    except Exception as e:
        import traceback; traceback.print_exc()
        print("CLIENT FAILED:", repr(e)); return 1

sys.exit(asyncio.run(main()))
