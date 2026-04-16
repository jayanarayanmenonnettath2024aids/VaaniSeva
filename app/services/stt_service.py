import logging
import os
import tempfile
import glob
from typing import Dict

import requests

from app.config import settings

try:
    import scipy.io.wavfile as wavfile
    import numpy as np
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

logger = logging.getLogger(__name__)

_model = None


def _resolve_cached_model_path(model_name: str) -> str | None:
    # If caller already provided a local directory, use it directly.
    if os.path.isdir(model_name):
        return model_name

    cache_root = os.path.expanduser("~/.cache/huggingface/hub")
    repo_dir = os.path.join(cache_root, f"models--Systran--faster-whisper-{model_name}")
    snapshots_glob = os.path.join(repo_dir, "snapshots", "*")
    snapshot_dirs = [p for p in glob.glob(snapshots_glob) if os.path.isdir(p)]

    if not snapshot_dirs:
        return None

    snapshot_dirs.sort(key=os.path.getmtime, reverse=True)
    for snapshot in snapshot_dirs:
        if os.path.exists(os.path.join(snapshot, "model.bin")):
            return snapshot
    return snapshot_dirs[0]


def _get_model():
    global _model
    if _model is not None:
        return _model

    try:
        from faster_whisper import WhisperModel
    except Exception as exc:  # pragma: no cover - runtime dependency check
        raise RuntimeError(
            "faster-whisper is not installed. Install it with: pip install faster-whisper"
        ) from exc

    logger.info(
        "[STT] Loading Faster-Whisper model=%s device=%s compute_type=%s",
        settings.LOCAL_STT_MODEL,
        settings.LOCAL_STT_DEVICE,
        settings.LOCAL_STT_COMPUTE_TYPE,
    )

    model_source = _resolve_cached_model_path(settings.LOCAL_STT_MODEL) or settings.LOCAL_STT_MODEL
    if model_source != settings.LOCAL_STT_MODEL:
        logger.info("[STT] Using cached model snapshot path: %s", model_source)

    try:
        _model = WhisperModel(
            model_source,
            device=settings.LOCAL_STT_DEVICE,
            compute_type=settings.LOCAL_STT_COMPUTE_TYPE,
        )
    except OSError as exc:
        # On Windows without symlink privileges, huggingface cache linking can fail.
        # If a snapshot is already present, retry from the local snapshot directory.
        if "WinError 1314" not in str(exc):
            raise

        fallback_source = _resolve_cached_model_path(settings.LOCAL_STT_MODEL)
        if not fallback_source:
            raise

        logger.warning("[STT] Retrying model load from local snapshot after symlink error: %s", fallback_source)
        _model = WhisperModel(
            fallback_source,
            device=settings.LOCAL_STT_DEVICE,
            compute_type=settings.LOCAL_STT_COMPUTE_TYPE,
        )
    return _model


def _infer_mime(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".mp3"):
        return "audio/mpeg"
    if lower.endswith(".m4a"):
        return "audio/mp4"
    if lower.endswith(".ogg"):
        return "audio/ogg"
    if lower.endswith(".aac"):
        return "audio/aac"
    return "audio/wav"


def _download_twilio_recording(audio_url: str) -> tuple[str, bytes, str]:
    filename = (audio_url.rsplit("/", 1)[-1] or "recording.wav").split("?", 1)[0]
    mime = _infer_mime(filename)

    auth = None
    if settings.TWILIO_VOICE_ACCOUNT_SID and settings.TWILIO_VOICE_AUTH_TOKEN:
        auth = (settings.TWILIO_VOICE_ACCOUNT_SID, settings.TWILIO_VOICE_AUTH_TOKEN)

    response = requests.get(audio_url, auth=auth, timeout=20)
    response.raise_for_status()
    return filename, response.content, mime


def _trim_silence_from_wav(audio_bytes: bytes) -> bytes:
    """Remove leading/trailing silence from WAV audio to speed up transcription.
    Typical speedup: 30-50% reduction in processing time.
    """
    if not HAS_SCIPY:
        return audio_bytes

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_bytes)
            tmp_read_path = tmp.name

        sample_rate, audio_data = wavfile.read(tmp_read_path)
        if len(audio_data.shape) > 1:
            # Convert stereo to mono by averaging channels
            audio_data = np.mean(audio_data, axis=1).astype(audio_data.dtype)

        # Compute RMS to detect silence (threshold: 2% of max RMS)
        rms = np.sqrt(np.mean(audio_data.astype(float) ** 2, axis=0))
        max_rms = np.max(np.abs(audio_data)) / 32768.0 if audio_data.dtype == np.int16 else np.max(np.abs(audio_data))
        threshold = max(0.02 * max_rms, 0.001)

        # Find first and last non-silent frame
        non_silent = np.where(np.abs(audio_data) > threshold * 32768)[0] if audio_data.dtype == np.int16 else np.where(np.abs(audio_data) > threshold)[0]
        if len(non_silent) == 0:
            return audio_bytes  # All silence, return original

        start_idx = int(max(0, non_silent[0] - 0.1 * sample_rate))  # Keep 100ms leading buffer
        end_idx = int(min(len(audio_data), non_silent[-1] + 0.1 * sample_rate))  # Keep 100ms trailing buffer
        trimmed_audio = audio_data[start_idx:end_idx]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_out:
            wavfile.write(tmp_out.name, sample_rate, trimmed_audio)
            with open(tmp_out.name, "rb") as f:
                trimmed_bytes = f.read()
            os.remove(tmp_out.name)

        os.remove(tmp_read_path)
        logger.info("[STT] Trimmed silence: %.1f%% time reduction", 100 * (1 - len(trimmed_audio) / len(audio_data)))
        return trimmed_bytes
    except Exception as exc:
        logger.warning("[STT] Silence trimming failed, using original: %s", exc)
        return audio_bytes


def _local_whisper_transcribe(audio_url: str, preferred_language: str = "") -> Dict[str, str]:
    filename, audio_bytes, mime = _download_twilio_recording(audio_url)
    model = _get_model()

    # Trim silence to speed up transcription
    audio_bytes = _trim_silence_from_wav(audio_bytes)

    suffix = os.path.splitext(filename)[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        temp_path = tmp.name

    preferred = (preferred_language or "").strip().lower()
    if preferred not in {"en", "ta", "hi", "ml", "te"}:
        preferred = ""

    language_hint = preferred or settings.LOCAL_STT_LANGUAGE_HINT.strip() or None
    beam_size = max(1, int(settings.LOCAL_STT_BEAM_SIZE))
    if preferred in {"ta", "hi", "ml", "te"}:
        # Slightly wider beam helps with regional language transcriptions on short clips.
        beam_size = max(beam_size, 3)

    def _transcribe_with_language(lang: str | None):
        return model.transcribe(
            temp_path,
            beam_size=beam_size,
            vad_filter=False,
            language=lang,
            condition_on_previous_text=False,
            task="transcribe",
        )

    try:
        logger.info("[STT] Transcribing local audio file: %s", temp_path)
        try:
            segments, info = _transcribe_with_language(language_hint)
            # Extract text from segments - if empty or only whitespace, return empty
            text = " ".join((seg.text or "").strip() for seg in segments).strip()
            if not text:
                logger.warning("[STT] Transcription returned empty/silent audio")
                return {"text": "", "language": "unknown"}
            
            language = str(getattr(info, "language", "unknown") or "unknown")
            logger.info("[STT] Extracted text: %s, language: %s", text[:100], language)
            return {"text": text, "language": language}
            
        except RuntimeError as exc:
            # On some Windows environments, auto language detection can fail with
            # a JSON null type error. Retry with explicit language candidates.
            msg = str(exc)
            if language_hint is not None or "json.exception.type_error.305" not in msg:
                raise

            fallback_langs = [
                lang.strip()
                for lang in settings.LOCAL_STT_FALLBACK_LANGS.split(",")
                if lang.strip()
            ] or ["en", "hi", "ta", "te", "ml"]
            if preferred:
                fallback_langs = [preferred] + [lang for lang in fallback_langs if lang != preferred]
            logger.warning("[STT] Auto language detection failed, retrying with explicit languages: %s", fallback_langs)
            last_exc = exc
            for lang in fallback_langs:
                try:
                    segments, info = _transcribe_with_language(lang)
                    text = " ".join((seg.text or "").strip() for seg in segments).strip()
                    if text:
                        language = str(getattr(info, "language", lang) or lang)
                        logger.info("[STT] Extracted text after fallback lang=%s: %s", lang, text[:100])
                        return {"text": text, "language": language}
                except RuntimeError as fallback_exc:
                    last_exc = fallback_exc

            logger.warning("[STT] Fallback language retries failed: %s", last_exc)
            return {"text": "", "language": "unknown"}
    finally:
        try:
            os.remove(temp_path)
        except Exception:
            pass


def process_audio(audio_url: str, preferred_language: str = "") -> Dict[str, str]:
    try:
        return _local_whisper_transcribe(audio_url, preferred_language=preferred_language)
    except Exception as exc:
        logger.exception("Local Whisper STT failed: %s", exc)
        return {
            "text": "",
            "language": "unknown",
            "error": "local_whisper_failed",
        }
