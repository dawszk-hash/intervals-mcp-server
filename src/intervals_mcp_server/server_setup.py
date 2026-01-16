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

        # Zmiana: Przyjmujemy scope, receive i send bezpośrednio (standard ASGI)
        async def handle_sse(scope, receive, send):
            try:
                logger.info("Incoming SSE connection...")
                # Przekazujemy surowe parametry do transportu MCP
                async with sse.connect_sse(scope, receive, send) as (read_stream, write_stream):
                    logger.info("SSE streams connected. Running MCP server loop...")
                    await mcp.server.run(
                        read_stream,
                        write_stream,
                        mcp.server.create_initialization_options()
                    )
            except Exception as e:
                logger.error(f"CRITICAL ERROR in SSE handler: {str(e)}", exc_info=True)
                raise

        async def handle_messages(scope, receive, send):
            try:
                await sse.handle_post_message(scope, receive, send)
            except Exception as e:
                logger.error(f"Error in message handler: {str(e)}")
                raise

        app = Starlette(
            debug=True,
            routes=[
                # Używamy surowych funkcji zamiast dekoratora request
                Route("/sse", endpoint=handle_sse),
                Route("/messages", endpoint=handle_messages, methods=["POST"]),
            ]
        )

        logger.info(f"==> BOOTING MANUAL DISPATCHER ON PORT {port} <==")
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

def setup_transport() -> str:
    return get_transport()
