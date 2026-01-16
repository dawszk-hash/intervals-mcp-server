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
        mcp.run(transport="stdio")
    else:
        # Ręczna konfiguracja transportu SSE
        sse = SseServerTransport("/messages")

        async def handle_sse(request):
            async with sse.connect_sse(request.scope, request.receive, request.send) as (read_stream, write_stream):
                # Kluczowy moment: uruchamiamy serwer MCP na strumieniach SSE
                await mcp.server.run(
                    read_stream,
                    write_stream,
                    mcp.server.create_initialization_options()
                )

        async def handle_messages(request):
            await sse.handle_post_message(request.scope, request.receive, request.send)

        # Tworzymy czystą aplikację Starlette - Uvicorn ją uwielbia
        app = Starlette(
            routes=[
                Route("/sse", endpoint=handle_sse),
                Route("/messages", endpoint=handle_messages, methods=["POST"]),
            ]
        )

        logger.info(f"==> BOOTING MANUAL DISPATCHER ON PORT {port} <==")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

def setup_transport() -> str:
    return get_transport()
