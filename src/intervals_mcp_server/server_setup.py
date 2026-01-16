import os
import logging

logger = logging.getLogger("intervals_icu_mcp_server")

def get_transport() -> str:
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport not in ["stdio", "sse"]:
        raise ValueError(f"Unsupported transport type: {transport}")
    return transport

def start_server(mcp, transport: str) -> None:
    """
    Uruchamia serwer MCP. Dla SSE używamy wbudowanej metody mcp.run,
    która sama zajmie się poprawnym wystawieniem aplikacji.
    """
    if transport == "stdio":
        logger.info("Starting MCP server with STDIO transport...")
        mcp.run(transport="stdio")

    elif transport == "sse":
        host = os.getenv("UVICORN_HOST", "0.0.0.0")
        port = int(os.getenv("UVICORN_PORT", "10000"))

        logger.info(f"Starting MCP server with SSE transport on {host}:{port}")
        
        # Wersja 1.25.0 najlepiej radzi sobie sama, gdy wywołamy run z transportem sse
        mcp.run(
            transport="sse",
            host=host,
            port=port
        )
    else:
        raise ValueError(f"Unsupported transport: {transport}")

def setup_transport() -> str:
    return get_transport()
