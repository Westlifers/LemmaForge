from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.get("/status")
def api_agent_status():
    return {"available": False, "mode": "manual_patch_import"}

