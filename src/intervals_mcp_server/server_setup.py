import os
import logging
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
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

        async def handle_sse(request: Request):
            """
            Używamy obiektu Request i wyciągamy z niego surowe 
            funkcje receive i send, których potrzebuje MCP.
            """
            async with sse.connect_sse(
                request.scope, 
                request.receive, 
                request._send # Używamy wewnętrznej funkcji send Starlette
            ) as (read_stream, write_stream):
                await mcp.server.run(
                    read_stream,
                    write_stream,
                    mcp.server.create_initialization_options()
                )

        async def handle_messages(request: Request):
            """Obsługa komunikatów sterujących."""
            await sse.handle_post_message(
                request.scope, 
                request.receive, 
                request._send
            )

        app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Route("/messages", endpoint=handle_messages, methods=["POST"]),
            ]
        )

        logger.info(f"==> BOOTING FIXED DISPATCHER ON PORT {port} <==")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

def setup_transport() -> str:
    return get_transport()
