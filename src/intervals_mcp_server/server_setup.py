import os
import logging
import uvicorn
import asyncio
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.endpoints import HTTPEndpoint
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

        # Używamy klas, aby Starlette wiedziało dokładnie jak obsłużyć ASGI
        class SSEEndpoint(HTTPEndpoint):
            async def get(self, request):
                scope = request.scope
                receive = request.receive
                send = request.send
                
                async with sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
                    logger.info("SSE Connection established.")
                    await mcp.server.run(
                        read_stream,
                        write_stream,
                        mcp.server.create_initialization_options()
                    )

        class MessagesEndpoint(HTTPEndpoint):
            async def post(self, request):
                await sse.handle_post_message(request.scope, request.receive, request.send)

        app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=SSEEndpoint),
                Route("/messages", endpoint=MessagesEndpoint),
            ]
        )

        logger.info(f"==> BOOTING MANUAL DISPATCHER ON PORT {port} <==")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

def setup_transport() -> str:
    return get_transport()
