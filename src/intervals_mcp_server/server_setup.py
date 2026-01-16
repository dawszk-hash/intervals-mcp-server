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
        
        host = os.getenv("UVICORN_HOST", "0.0.0.0")
        port = int(os.getenv("UVICORN_PORT", "10000"))

        logger.info(f"Starting MCP server via Uvicorn on {host}:{port}")

        # Próba uzyskania aplikacji Starlette z obiektu FastMCP
        # W wersji 1.25.0 aplikacja zazwyczaj znajduje się pod jednym z tych atrybutów
        app = None
        for attr in ["starlette_app", "_app"]:
            if hasattr(mcp, attr):
                app = getattr(mcp, attr)
                break
        
        # Jeśli nie znaleziono atrybutu, wywołujemy create_app()
        if app is None and hasattr(mcp, "create_app"):
            app = mcp.create_app()
            
        if app is None:
            # Ostateczność: jeśli nic nie zadziała, używamy samego obiektu mcp
            app = mcp

        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            lifespan="off"  # Ważne: zapobiega błędom protokołu ASGI przy starcie
        )
    else:
        raise ValueError(f"Unsupported transport: {transport}")

def setup_transport() -> str:
    return get_transport()
