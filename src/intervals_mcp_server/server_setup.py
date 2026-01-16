import os
import logging
import uvicorn
import asyncio
from starlette.applications import Starlette
from starlette.routing import Route
from mcp.server.sse import SseServerTransport

# Konfiguracja loggera
logger = logging.getLogger("intervals_icu_mcp_server")

def get_transport() -> str:
    """Pobiera typ transportu z env, domyślnie sse."""
    return os.getenv("MCP_TRANSPORT", "sse").lower()

def start_server(mcp, transport: str) -> None:
    """Uruchamia serwer MCP w zależności od wybranego transportu."""
    port = int(os.getenv("UVICORN_PORT", "10000"))
    
    if transport == "stdio":
        logger.info("Starting MCP server via STDIO...")
        mcp.run(transport="stdio")
    
    else:
        # Konfiguracja SSE
        sse = SseServerTransport("/messages")

        async def handle_sse(request):
            """Endpoint dla połączeń strumieniowych SSE."""
            try:
                logger.info(f"Incoming SSE connection from {request.client.host}")
                async with sse.connect_sse(request.scope, request.receive, request.send) as (read_stream, write_stream):
                    # Ręczne powiązanie serwera MCP z uzyskanymi strumieniami
                    logger.info("SSE streams connected. Running MCP server loop...")
                    await mcp.server.run(
                        read_stream,
                        write_stream,
                        mcp.server.create_initialization_options()
                    )
            except Exception as e:
                logger.error(f"CRITICAL ERROR in SSE handler: {str(e)}", exc_info=True)
                # Wyjątek zostanie zalogowany w panelu Render
                raise

        async def handle_messages(request):
            """Endpoint dla wiadomości POST od klienta do serwera."""
            try:
                await sse.handle_post_message(request.scope, request.receive, request.send)
            except Exception as e:
                logger.error(f"Error in message handler: {str(e)}")
                raise

        # Budowa aplikacji Starlette
        # To jest obiekt, który Uvicorn uruchamia poprawnie
        app = Starlette(
            debug=True,  # Włączamy debugowanie dla lepszych logów na Render
            routes=[
                Route("/sse", endpoint=handle_sse),
                Route("/messages", endpoint=handle_messages, methods=["POST"]),
            ]
        )

        logger.info(f"==> BOOTING MANUAL DISPATCHER ON PORT {port} <==")
        logger.info(f"==> SSE Endpoint: /sse | Message Endpoint: /messages <==")
        
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

def setup_transport() -> str:
    """Zwraca aktywny transport."""
    return get_transport()
