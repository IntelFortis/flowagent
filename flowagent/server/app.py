"""FastAPI application for FlowAgent Web UI."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from flowagent.server.api.workflows import router as workflows_router
from flowagent.server.api.nodes import router as nodes_router
from flowagent.server.api.models import router as models_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="FlowAgent",
        description="FlowAgent - Visual Workflow Automation Platform",
        version="1.0.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(workflows_router, prefix="/api")
    app.include_router(nodes_router, prefix="/api")
    app.include_router(models_router, prefix="/api")

    # Serve frontend static files
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists() and (static_dir / "index.html").exists():
        app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            # Don't serve SPA for API routes that weren't matched
            if full_path.startswith("api/"):
                return JSONResponse({"detail": "Not Found"}, status_code=404)
            file_path = static_dir / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(static_dir / "index.html"))

    return app


# For running with: python -m flowagent.server.app
app = create_app()
