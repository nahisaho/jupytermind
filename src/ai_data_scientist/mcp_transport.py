"""Real streamable-http transport for the Jupyter MCP server.

Implements the ``_Transport`` callable jupyter_mcp_client.JupyterMCPClient
expects, using the real ``mcp`` Python SDK. Verified interactively against a
live jupyter-mcp-server 2.2.3: the installed SDK exposes
``mcp.client.streamable_http.streamable_http_client`` (not
``streamablehttp_client``), yields a 2-tuple ``(read, write)``, accepts auth
headers only via an injected ``httpx.AsyncClient``, and each discovered
``Tool`` exposes its JSON schema as ``input_schema`` (snake_case).
"""

from __future__ import annotations

import asyncio

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

_TOOL_NAME = "execute_code"


async def _execute_code_async(port: int, token: str, code: str) -> dict:
    url = f"http://127.0.0.1:{port}/mcp"
    headers = {"Authorization": "Bearer " + token}
    async with (
        httpx.AsyncClient(headers=headers) as http_client,
        streamable_http_client(url, http_client=http_client) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.call_tool(_TOOL_NAME, {"code": code})
        if result.is_error:
            text = "".join(block.text for block in result.content if hasattr(block, "text"))
            return {"status": "error", "output": text}
        outputs = (result.structured_content or {}).get("outputs")
        if outputs is not None:
            output = "\n".join(str(item) for item in outputs)
        else:
            output = "".join(block.text for block in result.content if hasattr(block, "text"))
        return {"status": "ok", "output": output}


# @id CODE-AIDS-045
# @implements REQ-AIDS-038
# @design DES-AIDS-026
def execute_code(port: int, token: str, code: str) -> dict:
    """Run ``code`` on a live jupyter-mcp-server and return its result.

    Matches the ``_Transport`` Protocol expected by JupyterMCPClient:
    ``(port, token, code) -> {"status": "ok"|"error", "output": str}``.
    """
    return asyncio.run(_execute_code_async(port, token, code))
