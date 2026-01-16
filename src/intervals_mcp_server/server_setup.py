import os
import logging

# Używamy getLogger (poprawione)
logger = logging.getLogger("intervals_icu_mcp_server")


def get_transport() -> str:
    """
    Parse MCP_TRANSPORT environment variable and validate it.
    """
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport not in ["stdio", "sse"]:
        raise ValueError(f"Unsupported transport type: {transport}")
    return transport


def start_server(mcp, transport: str) -> None:
    """
    Start the MCP server with the selected transport.
    """
    if transport == "stdio":
        logger.info("Starting MCP server with STDIO transport...")
        mcp.run(transport="stdio")

    elif transport == "sse":
        logger.info("Starting MCP server with SSE transport via HTTP...")
        import uvicorn

        # Pobieramy host i port z Environment Variables Rendera
        host = os.getenv("UVICORN_HOST", "0.0.0.0")
        port = int(os.getenv("UVICORN_PORT", "10000"))

        logger.info(
            f"Starting MCP server with SSE transport at http://{host}:{port}/sse"
        )

        # W wersji 1.25.0 FastMCP aplikacja Starlette jest pod .starlette_app
        uvicorn.run(
            mcp.starlette_app, 
            host=host,
            port=port,
            log_level="info"
        )

    else:
        raise ValueError(f"Unsupported transport: {transport}")


def setup_transport() -> str:
    """
    Helper to setup transport type.
    """
    return get_transport()
