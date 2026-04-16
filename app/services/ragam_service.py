import logging
from typing import Any, Dict

import requests

from app.config import settings

logger = logging.getLogger(__name__)


DEFAULT_AGENT_ID = "69c6cc65acdaaa90b7006210"


def _default_session_payload(agent_id: str) -> Dict[str, Any]:
    """Default Lyzr realtime voice configuration for RAGAM AI."""


    
    return {
        "userIdentity": "ragam-admin",
        "agentId": agent_id,
        "agentConfig": {
            "engine": {
                "kind": "realtime",
                "llm": "openai/gpt-realtime",
                "voice": "sage",
                "language": "en",
            },
            "prompt": (
                "You are an intelligent AI governance co-pilot designed to support administrators with "
                "data-driven insights, strategic recommendations, and real-time situational awareness.\n\n"
                "Your goal is to assist administrators by providing clear insights, summarizing data, "
                "identifying key issues, and recommending actionable decisions based on real-time information.\n\n"
                "You are an intelligent voice-based AI assistant designed for administrators.\n\n"
                "You must:\n"
                "- Understand queries related to governance, data, and system insights\n"
                "- Provide clear, concise, and structured responses\n"
                "- Summarize complex data into simple, meaningful insights\n"
                "- Highlight key issues, trends, and anomalies\n"
                "- Suggest actionable recommendations when relevant\n\n"
                "You should:\n"
                "- Maintain a professional and confident tone\n"
                "- Respond in the same language as the user (auto-detect language)\n"
                "- Keep responses concise but insightful\n"
                "- Use a storytelling approach when explaining trends\n\n"
                "If data is insufficient:\n"
                "- Ask clarifying questions before answering\n\n"
                "Do NOT:\n"
                "- Give vague or generic answers\n"
                "- Overcomplicate explanations\n\n"
                "You must follow strict turn-based conversation:\n\n"
                "- Always allow the user to complete their speech fully before responding\n"
                "- Do not interrupt or respond while the user is still speaking\n"
                "- After the user finishes, process the input completely before replying\n"
                "- When responding, complete your full sentence clearly before stopping\n"
                "- Do not cut off responses midway\n"
                "- Maintain a smooth and natural conversational flow\n\n"
                "If the user pauses briefly, wait for confirmation before responding\n"
                "Prioritize listening accuracy over response speed.\n\n"
                "If the exact answer is not available in the knowledge base, do not say \"I don't know\" or \"provide data source\".\n\n"
                "Instead, provide the best possible answer using available context and general reasoning.\n\n"
                "Always try to:\n"
                "- infer from related data\n"
                "- give a meaningful and helpful response\n"
                "- suggest possible actions or insights\n\n"
                "If data is missing, respond like:\n"
                "\"Based on the available data, it appears that...\"\n\n"
                "If specific data is not available for a ward or query, provide the closest possible insight "
                "based on similar wards or overall trends instead of saying no data is available."
            ),
            "conversation_start": {
                "who": "ai",
                "greeting": (
                    "Say, \"Welcome. This is Ragam, your AI governance assistant. I can summarize key issues, "
                    "and help you make informed decisions. What would you like to know?\""
                ),
            },
            "turn_detection": "english",
            "noise_cancellation": {"enabled": True, "type": "telephony"},
            "vad_enabled": True,
            "preemptive_generation": False,
            "pronunciation_correction": True,
            "audio_recording_enabled": True,
            "knowledge_base": {
                "enabled": True,
                "lyzr_rag": {
                    "base_url": "https://rag-prod.studio.lyzr.ai",
                    "rag_id": "69c6f426efe9656d370ab8aa",
                    "rag_name": "pala32w",
                    "params": {"top_k": 5, "retrieval_type": "mmr", "score_threshold": 0.4},
                },
                "agentic_rag": [],
            },
            "background_audio": {
                "enabled": True,
                "ambient": {"enabled": True, "source": "OFFICE_AMBIENCE", "volume": 0.6},
                "tool_call": {
                    "enabled": True,
                    "sources": [
                        {"source": "KEYBOARD_TYPING_TRUNC", "volume": 0.8, "probability": 1}
                    ],
                },
                "turn_taking": {
                    "enabled": False,
                    "sources": [
                        {"source": "KEYBOARD_TYPING", "volume": 0.8, "probability": 0.6},
                        {"source": "KEYBOARD_TYPING2", "volume": 0.7, "probability": 0.4},
                    ],
                },
            },
        },
    }


def _lyzr_api_key() -> str:
    """Retrieve Lyzr API key from environment (never expose in frontend)."""
    return str(settings.LYZR_API_KEY or "")


def _lyzr_session_start_url() -> str:
    """Lyzr session start endpoint."""
    return "https://voice-livekit.studio.lyzr.ai/v1/sessions/start"


def _lyzr_session_end_url() -> str:
    """Lyzr session end endpoint."""
    return "https://voice-livekit.studio.lyzr.ai/v1/sessions/end"


def start_session(
    agent_id: str,
    user_identity: str = "ragam-admin",
    session_config: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Start a Lyzr AI voice session for admin or department staff.

    Args:
        agent_id: Lyzr agent ID (e.g., "69c6cc65acdaaa90b7006210")

    Returns:
        {
            "status": "started" | "error",
            "room_name": "<room-name>",  # when success
            "session_url": "<websocket-url>",  # when success
            "error": "<error-message>",  # when failed
        }
    """
    api_key = _lyzr_api_key()
    if not api_key:
        logger.error("[RAGAM] Lyzr API key not configured")
        return {"status": "error", "error": "Lyzr API key not configured"}

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }
    payload = _default_session_payload(agent_id=agent_id)
    payload["userIdentity"] = user_identity or "ragam-admin"
    if session_config:
        # Accept direct agentConfig override from API layer.
        payload["agentConfig"] = session_config

    try:
        response = requests.post(
            _lyzr_session_start_url(),
            json=payload,
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        room_name = str(data.get("roomName", "") or data.get("room_name", "") or "")
        session_url = str(data.get("sessionUrl", "") or data.get("session_url", "") or "")
        livekit_url = str(data.get("livekitUrl", "") or data.get("livekit_url", "") or "")
        user_token = str(data.get("userToken", "") or data.get("user_token", "") or "")
        session_id = str(data.get("sessionId", "") or data.get("session_id", "") or "")

        if not room_name:
            logger.error("[RAGAM] No roomName in Lyzr response: %s", data)
            return {"status": "error", "error": "No room name in response"}

        logger.info("[RAGAM] Session started: room_name=%s", room_name)
        return {
            "status": "started",
            "room_name": room_name,
            "session_url": session_url,
            "livekit_url": livekit_url,
            "user_token": user_token,
            "session_id": session_id,
            "raw": data,
        }

    except requests.Timeout:
        logger.exception("[RAGAM] Lyzr session start timeout")
        return {"status": "error", "error": "Lyzr API timeout"}
    except requests.RequestException as exc:
        logger.exception("[RAGAM] Lyzr session start failed: %s", exc)
        details = ""
        if exc.response is not None:
            try:
                details = f" | body={exc.response.text[:200]}"
            except Exception:  # noqa: BLE001
                details = ""
        return {"status": "error", "error": f"Lyzr API error: {str(exc)[:120]}{details}"}


def end_session(room_name: str) -> Dict[str, Any]:
    """End a Lyzr AI voice session.

    Args:
        room_name: Room name returned from start_session

    Returns:
        {"status": "ended" | "error", "error": "<error-message>"}
    """
    api_key = _lyzr_api_key()
    if not api_key:
        logger.error("[RAGAM] Lyzr API key not configured")
        return {"status": "error", "error": "Lyzr API key not configured"}

    if not room_name:
        return {"status": "error", "error": "Room name required"}

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }
    payload = {"roomName": room_name}

    try:
        response = requests.post(
            _lyzr_session_end_url(),
            json=payload,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        logger.info("[RAGAM] Session ended: room_name=%s", room_name)
        return {"status": "ended"}

    except requests.Timeout:
        logger.exception("[RAGAM] Lyzr session end timeout")
        return {"status": "error", "error": "Lyzr API timeout"}
    except requests.RequestException as exc:
        logger.exception("[RAGAM] Lyzr session end failed: %s", exc)
        return {"status": "error", "error": f"Lyzr API error: {str(exc)[:100]}"}
