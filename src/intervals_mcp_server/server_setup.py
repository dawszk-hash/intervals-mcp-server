import os
import logging

logger = logging.getLogger("intervals_icu_mcp_server")

def get_transport() -> str:
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport not in ["stdio", "sse"]:
        raise ValueError(f"Unsupported transport type: {transport}")
    return transport

def start_server(mcp, transport: str) -> None:
    if transport == "stdio":
        logger.info("Starting MCP server with STDIO transport...")
        mcp.run(transport="stdio")

    elif transport == "sse":
        import uvicorn
        from starlette.applications import Starlette

        host = os.getenv("UVICORN_HOST", "0.0.0.0")
        port = int(os.getenv("UVICORN_PORT", "10000"))

        logger.info(f"Starting MCP server via Uvicorn on {host}:{port}")

        # Wersja 1.25.0: mcp.run() jest ograniczone, więc wyciągamy aplikację Starlette
        # Próbujemy najpierw oficjalnej metody tworzenia aplikacji
        try:
            app = mcp.create_app()
        except AttributeError:
            # Jeśli create_app nie istnieje, używamy wewnętrznego atrybutu
            app = getattr(mcp, "_app", mcp)

        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            # Wyłączamy lifespan, jeśli biblioteka go nie wspiera (widoczne w logach)
            lifespan="off"
        )
    else:
        raise ValueError(f"Unsupported transport: {transport}")

def setup_transport() -> str:
    return get_transport()
