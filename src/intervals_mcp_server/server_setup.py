import os
import logging
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from mcp.server.sse import SseServerTransport

logger = logging.getLogger("intervals_icu_mcp_server")

def get_transport() -> str:
    return os.getenv("MCP_TRANSPORT", "sse").lower()

def start_server(mcp, transport: str) -> None:
    port = int(os.getenv("UVICORN_PORT", "10000"))
    
    if transport == "stdio":
        logger.info("Starting MCP server via STDIO...")
        mcp.run(transport="stdio")
    else:
        sse = SseServerTransport("/messages")

        async def handle_lobe_manifest(request: Request):
            """Obsługa Lobe Chat (Manifest narzędzi)"""
            return JSONResponse({
                "mcpVersion": "1.0",
                "capabilities": mcp.server.capabilities.dict(),
                "tools": [
                    {
                        "name": name,
                        "description": tool.description,
                        "inputSchema": tool.input_schema
                    } for name, tool in mcp.server.get_tools().items()
                ]
            })

        async def handle_sse(request: Request):
            async with sse.connect_sse(
                request.scope, 
                request.receive, 
                request._send
            ) as (read_stream, write_stream):
                await mcp.server.run(
                    read_stream,
                    write_stream,
                    mcp.server.create_initialization_options()
                )

        async def handle_messages(request: Request):
            await sse.handle_post_message(request.scope, request.receive, request._send)

        app = Starlette(
            debug=True,
            routes=[
                Route("/", endpoint=handle_lobe_manifest, methods=["GET", "POST"]),
                Route("/sse", endpoint=handle_sse),
                Route("/messages", endpoint=handle_messages, methods=["POST"]),
            ]
        )

        logger.info(f"==> BOOTING HYBRID SERVER (SSE + LOBE) ON PORT {port} <==")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

# Ta funkcja jest wymagana przez server.py
def setup_transport() -> str:
    return get_transport()
