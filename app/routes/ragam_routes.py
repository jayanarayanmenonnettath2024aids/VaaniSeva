"""RAGAM AI - Lyzr voice session management endpoints for admin/department staff."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import ragam_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ragam", tags=["ragam-ai"])


class SessionStartRequest(BaseModel):
    """Request to start a RAGAM AI session."""

    agent_id: str = "69c6cc65acdaaa90b7006210"  # Default RAGAM AI agent ID
    user_identity: str = "ragam-admin"
    session_config: Dict[str, Any] | None = None


class SessionEndRequest(BaseModel):
    """Request to end a RAGAM AI session."""

    room_name: str


@router.post("/session/start", response_model=Dict[str, Any])
async def session_start(req: SessionStartRequest) -> Dict[str, Any]:
    """Start a new Lyzr RAGAM AI voice session for admin or department user.

    Response:
    - Success: {"status": "started", "room_name": "...", "session_url": "..."}
    - Error: {"status": "error", "error": "..."}
    """
    result = ragam_service.start_session(
        agent_id=req.agent_id,
        user_identity=req.user_identity,
        session_config=req.session_config,
    )

    if result.get("status") == "error":
        logger.warning("[RAGAM] Session start failed: %s", result.get("error"))
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to start session"))

    return result


@router.post("/session/end", response_model=Dict[str, Any])
async def session_end(req: SessionEndRequest) -> Dict[str, Any]:
    """End an existing Lyzr RAGAM AI session.

    Response:
    - Success: {"status": "ended"}
    - Error: {"status": "error", "error": "..."}
    """
    result = ragam_service.end_session(room_name=req.room_name)

    if result.get("status") == "error":
        logger.warning("[RAGAM] Session end failed: %s", result.get("error"))
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to end session"))

    return result
