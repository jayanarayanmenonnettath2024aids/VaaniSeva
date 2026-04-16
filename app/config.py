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
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "phi3:mini")
    ACTION_ENGINE_URL: str = os.getenv("ACTION_ENGINE_URL", "")
    AI_ENGINE_URL: str = os.getenv("AI_ENGINE_URL", "")

    BHASHINI_API_URL: str = os.getenv("BHASHINI_API_URL", "")
    BHASHINI_API_KEY: str = os.getenv("BHASHINI_API_KEY", "")

    # Twilio Voice account (inbound/outbound calls)
    TWILIO_VOICE_ACCOUNT_SID: str = os.getenv("TWILIO_VOICE_ACCOUNT_SID", "")
    TWILIO_VOICE_AUTH_TOKEN: str = os.getenv("TWILIO_VOICE_AUTH_TOKEN", "")
    TWILIO_VOICE_NUMBER: str = os.getenv("TWILIO_VOICE_NUMBER", "")

    # Twilio Messaging account (SMS/WhatsApp)
    TWILIO_MSG_ACCOUNT_SID: str = os.getenv("TWILIO_MSG_ACCOUNT_SID", "")
    TWILIO_MSG_AUTH_TOKEN: str = os.getenv("TWILIO_MSG_AUTH_TOKEN", "")
    TWILIO_SMS_NUMBER: str = os.getenv("TWILIO_SMS_NUMBER", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")

    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "data/pallavi.db")
    AUDIT_HASH_SALT: str = os.getenv("AUDIT_HASH_SALT", "pallavi-default-salt")
    GEOCODING_URL: str = os.getenv("GEOCODING_URL", "https://nominatim.openstreetmap.org/search")
    GEOCODING_USER_AGENT: str = os.getenv("GEOCODING_USER_AGENT", "pallavi-voice-system/1.0")

    SARVAM_STT_URL: str = os.getenv("SARVAM_STT_URL", "https://api.sarvam.ai/stt")

    # Whisper STT (OpenAI-compatible transcription endpoint)
    WHISPER_STT_URL: str = os.getenv(
        "WHISPER_STT_URL",
        "https://api.groq.com/openai/v1/audio/transcriptions",
    )
    WHISPER_API_KEY: str = os.getenv("WHISPER_API_KEY", "")
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "whisper-large-v3-turbo")
    WHISPER_LANGUAGE_HINT: str = os.getenv("WHISPER_LANGUAGE_HINT", "")
    WHISPER_PROMPT: str = os.getenv("WHISPER_PROMPT", "Indian English and Indian regional accents")
    WHISPER_RESPONSE_FORMAT: str = os.getenv("WHISPER_RESPONSE_FORMAT", "verbose_json")

    # Wispr Flow STT
    WISPR_FLOW_STT_URL: str = os.getenv("WISPR_FLOW_STT_URL", "")
    WISPR_FLOW_API_KEY: str = os.getenv("WISPR_FLOW_API_KEY", "")
    WISPR_FLOW_AUTH_SCHEME: str = os.getenv("WISPR_FLOW_AUTH_SCHEME", "bearer")
    WISPR_FLOW_API_KEY_HEADER: str = os.getenv("WISPR_FLOW_API_KEY_HEADER", "Authorization")
    # multipart (default) or json_url (for providers that accept remote URL)
    WISPR_FLOW_REQUEST_MODE: str = os.getenv("WISPR_FLOW_REQUEST_MODE", "multipart")
    WISPR_FLOW_MODEL: str = os.getenv("WISPR_FLOW_MODEL", "")
    WISPR_FLOW_LANGUAGE_HINT: str = os.getenv("WISPR_FLOW_LANGUAGE_HINT", "")
    WISPR_FLOW_PROMPT: str = os.getenv("WISPR_FLOW_PROMPT", "Indian English and Indian regional accents")
    WISPR_FLOW_RESPONSE_FORMAT: str = os.getenv("WISPR_FLOW_RESPONSE_FORMAT", "verbose_json")

    # Local STT (Faster-Whisper)
    LOCAL_STT_MODEL: str = os.getenv("LOCAL_STT_MODEL", "large-v3")
    LOCAL_STT_DEVICE: str = os.getenv("LOCAL_STT_DEVICE", "cpu")
    LOCAL_STT_COMPUTE_TYPE: str = os.getenv("LOCAL_STT_COMPUTE_TYPE", "int8")
    LOCAL_STT_LANGUAGE_HINT: str = os.getenv("LOCAL_STT_LANGUAGE_HINT", "")
    LOCAL_STT_BEAM_SIZE: str = os.getenv("LOCAL_STT_BEAM_SIZE", "5")
    LOCAL_STT_TIMEOUT_SEC: str = os.getenv("LOCAL_STT_TIMEOUT_SEC", "8")
    LOCAL_STT_FALLBACK_LANGS: str = os.getenv("LOCAL_STT_FALLBACK_LANGS", "en,hi,ta,te,ml")

    SARVAM_API_KEYS: List[str] = None  # type: ignore[assignment]
    BASE_URL: str = os.getenv("BASE_URL", "https://your-ngrok-url")
    ESCALATION_CALL_URL: str = os.getenv("ESCALATION_CALL_URL", "")
    SLA_MONITOR_ENABLED: bool = os.getenv("SLA_MONITOR_ENABLED", "false").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    # Useful for webhook callbacks when generating record action URLs.
    PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000")

    # Lyzr AI Voice (RAGAM AI agent)
    LYZR_API_KEY: str = os.getenv("LYZR_API_KEY", "")

    def __post_init__(self) -> None:
        api_keys_raw = os.getenv("SARVAM_API_KEYS", "")
        parsed_keys = [k.strip() for k in api_keys_raw.split(",") if k.strip()]
        object.__setattr__(self, "SARVAM_API_KEYS", parsed_keys)


settings = Settings()
