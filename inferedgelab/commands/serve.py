from __future__ import annotations

import typer
import uvicorn


def serve_cmd(
    host: str = typer.Option("127.0.0.1", "--host", help="API server host"),
    port: int = typer.Option(8000, "--port", help="API server port"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development"),
):
    uvicorn.run(
        "inferedgelab.api:app",
        host=host,
        port=port,
        reload=reload,
    )
