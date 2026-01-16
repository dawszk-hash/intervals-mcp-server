import os
import logging
import uvicorn
from starlette.applications import Starlette
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

        # Używamy bezpośredniego wywołania sse.handle_sse, 
        # które jest już przygotowane jako aplikacja ASGI
        async def handle_sse(scope, receive, send):
            async with sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
                await mcp.server.run(
                    read_stream,
                    write_stream,
                    mcp.server.create_initialization_options()
                )

        app = Starlette(
            debug=True,
            routes=[
                # Mountujemy endpointy jako surowe aplikacje ASGI
                Route("/sse", endpoint=handle_sse),
                Route("/messages", endpoint=sse.handle_post_message, methods=["POST"]),
            ]
        )

        logger.info(f"==> BOOTING MANUAL DISPATCHER ON PORT {port} <==")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

def setup_transport() -> str:
    return get_transport()
