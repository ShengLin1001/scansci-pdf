"""CLI entrypoint for ScanSci PDF server."""

from __future__ import annotations

from enum import Enum

import typer

app = typer.Typer(help="ScanSci PDF server")


class ServerMode(str, Enum):
    STDIO = "stdio"
    HTTP = "streamable_http"


@app.command("run")
def run_server(
    mode: ServerMode = typer.Option(ServerMode.STDIO, help="Transport mode"),
    host: str = typer.Option("0.0.0.0", help="HTTP host"),
    port: int = typer.Option(8000, help="HTTP port"),
) -> None:
    """Start the ScanSci PDF server."""
    from .deps import print_status
    from .log import get_logger
    log = get_logger()

    # Check dependencies before starting
    print_status()

    from .server import mcp_app

    if mode == ServerMode.STDIO:
        log.info("Starting in stdio mode")
        mcp_app.run(transport="stdio")
    else:
        import uvicorn
        log.info(f"Starting HTTP server on {host}:{port}")
        asgi_app = mcp_app.streamable_http_app()
        uvicorn.run(asgi_app, host=host, port=port)


@app.command("check")
def check_deps() -> None:
    """Check dependency status."""
    from .deps import print_status
    print_status()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
