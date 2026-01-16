import os
import logging
import asyncio

logger = logging.getLogger("intervals_icu_mcp_server")

def get_transport() -> str:
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    return transport

def start_server(mcp, transport: str) -> None:
    if transport == "stdio":
        logger.info("Starting MCP server with STDIO transport...")
        mcp.run(transport="stdio")
    
    elif transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route
        import uvicorn

        port = int(os.getenv("UVICORN_PORT", "10000"))
        
        # Tworzymy instancję transportu SSE
        sse = SseServerTransport("/messages")

        async def handle_sse(request):
            async with sse.connect_sse(request.scope, request.receive, request.send) as (read_stream, write_stream):
                # Tutaj łączymy transport z serwerem MCP
                await mcp.server.run(
                    read_stream,
                    write_stream,
                    mcp.server.create_initialization_options()
                )

        async def handle_messages(request):
            await sse.handle_post_message(request.scope, request.receive, request.send)

        # Ręcznie budujemy aplikację Starlette, którą Uvicorn na pewno zrozumie
        app = Starlette(
            routes=[
                Route("/sse", endpoint=handle_sse),
                Route("/messages", endpoint=handle_messages, methods=["POST"]),
            ]
        )

        logger.info(f"Manual SSE Dispatcher starting on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

def setup_transport() -> str:
    return get_transport()
