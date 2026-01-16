import os
import logging
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
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
        # 1. Inicjalizujemy transport
        sse = SseServerTransport("/messages")

        # 2. Tworzymy surowe handlery ASGI, które ignorują próby wstrzykiwania 'Request' przez Starlette
        async def handle_sse(scope, receive, send):
            async with sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
                await mcp.server.run(
                    read_stream,
                    write_stream,
                    mcp.server.create_initialization_options()
                )

        async def handle_messages(scope, receive, send):
            await sse.handle_post_message(scope, receive, send)

        # 3. Budujemy aplikację. 
        # Używamy prostego routingu, który omija dekoratory Starlette.
        app = Starlette(
            debug=True,
            routes=[
                # Używamy niskopoziomowych definicji Route
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Route("/messages", endpoint=handle_messages, methods=["POST"]),
            ]
        )

        logger.info(f"==> BOOTING ROBUST DISPATCHER ON PORT {port} <==")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

def setup_transport() -> str:
    return get_transport()
