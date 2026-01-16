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
        logger.info("Starting MCP server with SSE transport via HTTP...")
        import uvicorn

        host = os.getenv("UVICORN_HOST", "0.0.0.0")
        port = int(os.getenv("UVICORN_PORT", "10000"))

        # W wersji 1.25.0 aplikacja siedzi dokładnie tutaj:
        app_to_run = mcp._app

        logger.info(f"Starting MCP server with SSE transport at http://{host}:{port}/sse")

        uvicorn.run(
            app_to_run,
            host=host,
            port=port,
            log_level="info"
        )
    else:
        raise ValueError(f"Unsupported transport: {transport}")

def setup_transport() -> str:
    return get_transport()
