"""Model configuration API."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from flowagent.core.models import get_registry

router = APIRouter(tags=["models"])


class AliasCreate(BaseModel):
    alias: str
    model: str
    provider: Optional[str] = None
    api_base: Optional[str] = None


class DefaultSet(BaseModel):
    provider: str
    model: str


@router.get("/models/aliases")
async def list_aliases() -> Dict[str, Dict[str, Any]]:
    """List all model aliases."""
    return get_registry().list_aliases()


@router.post("/models/aliases")
async def create_alias(body: AliasCreate) -> Dict[str, str]:
    """Register a model alias."""
    kwargs = {}
    if body.api_base:
        kwargs["api_base"] = body.api_base
    get_registry().register_alias(body.alias, body.model, provider=body.provider, **kwargs)
    return {"status": "created", "alias": body.alias}


@router.delete("/models/aliases/{alias}")
async def delete_alias(alias: str) -> Dict[str, str]:
    """Delete a model alias."""
    removed = get_registry().unregister_alias(alias)
    if not removed:
        from fastapi import HTTPException
        raise HTTPException(404, "Alias not found")
    return {"status": "deleted"}


@router.get("/models/defaults")
async def list_defaults() -> Dict[str, str]:
    """List provider defaults."""
    return get_registry().list_defaults()


@router.post("/models/defaults")
async def set_default(body: DefaultSet) -> Dict[str, str]:
    """Set default model for a provider."""
    get_registry().set_default(body.provider, body.model)
    return {"status": "set"}
