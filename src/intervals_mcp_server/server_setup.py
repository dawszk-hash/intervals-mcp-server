"""
Server setup and initialization for intervals-icu MCP server.

This module handles transport configuration and server startup logic.
"""

import os
import logging

from intervals_mcp_server.types import TransportOptions

logger = logging.getLogger("intervals_icu_mcp_server")


def get_transport() -> TransportOptions:
    """
    Parse MCP_TRANSPORT environment variable and validate it against
    supported transport types.

    Returns:
        TransportOptions: The selected transport type.

    Raises:
        ValueError: If the transport type is not supported.
    """
    transport_env = os.getenv("MCP_TRANSPORT", "stdio").lower()
    
    # Create a dictionary mapping strings to TransportOptions values
    transport_map = {
        "stdio": TransportOptions.STDIO,
        "sse": TransportOptions.SSE,
    }
    
    # Look up the transport type
    transport = transport_map.get(transport_env)
    
    if transport is None:
        raise ValueError(f"Unsupported transport type: {transport_env}")
    
    return transport


def start_server(mcp, transport: TransportOptions) -> None:
    """
    Start the MCP server with the selected transport.

    Args:
        mcp: The FastMCP instance to start.
        transport: The transport type to use (STDIO or SSE).
    """
    # Run the server with STDIO transport or SSE via HTTP
    if transport == TransportOptions.STDIO:
        logger.info("Starting MCP server with STDIO transport...")
        mcp.run(transport="stdio")
    
    elif transport == TransportOptions.SSE:
        logger.info("Starting MCP server with SSE transport via HTTP...")
        import uvicorn
        
        # Get host and port from environment variables
        host = os.getenv("UVICORN_HOST", "127.0.0.1")
        port = int(os.getenv("UVICORN_PORT", "8000"))
        
        logger.info(
            f"Starting MCP server with SSE transport at http://{host}:{port}/sse (messages: /messages/)."
        )
        
        uvicorn.run(
            mcp.app,
            host=host,
            port=port,
            log_level="info"
        )
    
    else:
        raise ValueError(f"Unsupported transport: {transport}")


def setup_transport() -> TransportOptions:
    """
    Get and validate the MCP_TRANSPORT environment variable, returning the selected transport.
    """
    return get_transport()
