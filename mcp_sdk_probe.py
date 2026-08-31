#!/usr/bin/env python3
"""Probe the SPEC-COMPLIANT FastMCP server (plain HTTP :8000) with the REAL MCP
SDK client — the transport family Hermes' native client uses. This must fully
pass (intialize + list_tools + call_tool) for registration to be non-theater.
"""
import asyncio, sys, httpx

async def main():
    url = "http://127.0.0.1:8000/mcp"
    try:
        from mcp.client.streamable_http import streamablehttp_client
        from mcp import ClientSession

        def factory(headers=None, timeout=None, auth=None):
            return httpx.AsyncClient(timeout=timeout or 15.0, auth=auth)
    except Exception as e:
        print("IMPORT/SETUP FAIL:", e); return 1
    try:
        async with streamablehttp_client(url, httpx_client_factory=factory) as (read, write, _):
            async with ClientSession(read, write) as session:
                r = await session.initialize()
                print("initialize OK:", r.serverInfo.model_dump())
                tools = await session.list_tools()
                names = [t.name for t in tools.tools]
                print("list_tools:", names)
                if "math_verify" in names:
                    res = await session.call_tool("math_verify", {"expression": "2+2=4"})
                    txt = [getattr(c, "text", f"<{c.__class__.__name__}>") for c in res.content]
                    print("call math_verify ->", txt)
                    return 0
                print("math_verify MISSING from tools")
                return 1
    except Exception as e:
        import traceback; traceback.print_exc()
        print("MCP-SDK CLIENT FAILED:", repr(e))
        return 1

sys.exit(asyncio.run(main()))
