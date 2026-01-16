import os
import logging

logger = logging.get_logger("intervals_icu_mcp_server")


def get_transport() -> str:
    """
    Parse MCP_TRANSPORT environment variable and validate it against
    supported transport types.

    Returns:
        str: The selected transport type ("stdio" or "sse").

    Raises:
        ValueError: If the transport type is not supported.
    """
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    if transport not in ["stdio", "sse"]:
        raise ValueError(f"Unsupported transport type: {transport}")

    return transport


def start_server(mcp, transport: str) -> None:
    """
    Start the MCP server with the selected transport.

    Args:
        mcp: The FastMCP instance to start.
        transport: The transport type to use ("stdio" or "sse").
    """
    if transport == "stdio":
        logger.info("Starting MCP server with STDIO transport...")
        mcp.run(transport="stdio")

    elif transport == "sse":
        logger.info("Starting MCP server with SSE transport via HTTP...")
        import uvicorn

        # Set host and port from environment variables
        host = os.getenv("UVICORN_HOST", "127.0.0.1")
        port = int(os.getenv("UVICORN_PORT", "8000"))

        logger.info(
            f"Starting MCP server with SSE transport at http://{host}:{port}/sse (messages: /messages/)."
        )

        uvicorn.run(
            mcp.create_app(), # Zmienione z mcp.app na mcp.create_app()
            host=host,
            port=port,
            log_level="info"
        )

    else:
        raise ValueError(f"Unsupported transport: {transport}")


def setup_transport() -> str:
    """
    Get and validate the MCP_TRANSPORT environment variable, returning the selected transport.
    """
    return get_transport()
