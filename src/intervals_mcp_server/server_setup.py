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
        # Inicjalizacja transportu SSE
        sse = SseServerTransport("/messages")

        async def handle_sse(scope, receive, send):
            """Surowy handler ASGI dla strumienia SSE."""
            try:
                async with sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
                    await mcp.server.run(
                        read_stream,
                        write_stream,
                        mcp.server.create_initialization_options()
                    )
            except Exception as e:
                logger.error(f"Error in SSE connection: {e}", exc_info=True)

        async def handle_messages(scope, receive, send):
            """Surowy handler ASGI dla przychodzących wiadomości POST."""
            try:
                await sse.handle_post_message(scope, receive, send)
            except Exception as e:
                logger.error(f"Error in message handler: {e}")

        # Budowa aplikacji Starlette z surowymi endpointami ASGI
        app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Route("/messages", endpoint=handle_messages, methods=["POST"]),
            ]
        )

        logger.info(f"==> BOOTING MANUAL DISPATCHER ON PORT {port} <==")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

def setup_transport() -> str:
    return get_transport()
