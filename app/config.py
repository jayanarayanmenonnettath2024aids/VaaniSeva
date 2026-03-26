import os
from dataclasses import dataclass
from pathlib import Path
from typing import List


def _load_env_file() -> None:
    """Load key-value pairs from .env into os.environ (without overriding existing env vars)."""
    env_path = Path(".env")
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_env_file()


@dataclass(frozen=True)
class Settings:
    AI_MODEL_PROVIDER: str = os.getenv("AI_MODEL_PROVIDER", "local")
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "phi3:mini")
    ACTION_ENGINE_URL: str = os.getenv("ACTION_ENGINE_URL", "")
    AI_ENGINE_URL: str = os.getenv("AI_ENGINE_URL", "")

    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")

    EXOTEL_API_BASE_URL: str = os.getenv("EXOTEL_API_BASE_URL", "https://api.exotel.com/v1")

    SARVAM_STT_URL: str = os.getenv("SARVAM_STT_URL", "https://api.sarvam.ai/stt")
    OPENAI_API_BASE_URL: str = os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
    CLAUDE_API_BASE_URL: str = os.getenv("CLAUDE_API_BASE_URL", "https://api.anthropic.com/v1")

    EXOTEL_SID_INBOUND: str = os.getenv("EXOTEL_SID_INBOUND", "")
    EXOTEL_TOKEN_INBOUND: str = os.getenv("EXOTEL_TOKEN_INBOUND", "")
    EXOTEL_NUMBER_INBOUND: str = os.getenv("EXOTEL_NUMBER_INBOUND", "")

    EXOTEL_SID_OUTBOUND: str = os.getenv("EXOTEL_SID_OUTBOUND", "")
    EXOTEL_TOKEN_OUTBOUND: str = os.getenv("EXOTEL_TOKEN_OUTBOUND", "")
    EXOTEL_NUMBER_OUTBOUND: str = os.getenv("EXOTEL_NUMBER_OUTBOUND", "")

    SARVAM_API_KEYS: List[str] = None  # type: ignore[assignment]
    BASE_URL: str = os.getenv("BASE_URL", "https://your-ngrok-url")
    ESCALATION_CALL_URL: str = os.getenv("ESCALATION_CALL_URL", "")

    # Useful for webhook callbacks when generating record action URLs.
    PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")

    def __post_init__(self) -> None:
        api_keys_raw = os.getenv("SARVAM_API_KEYS", "")
        parsed_keys = [k.strip() for k in api_keys_raw.split(",") if k.strip()]
        object.__setattr__(self, "SARVAM_API_KEYS", parsed_keys)


settings = Settings()
