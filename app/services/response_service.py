import os
from typing import Dict

import requests

from app.config import settings


def _fallback_response(language: str, has_previous_issue: bool) -> str:
    followups = {
        "en": "You reported a complaint earlier. Do you want an update on it?",
        "ta": "நீங்கள் முன்பு ஒரு புகார் பதிவு செய்துள்ளீர்கள். அதற்கான புதுப்பிப்பு வேண்டுமா?",
        "hi": "आपने पहले एक शिकायत दर्ज की थी। क्या आप उसका अपडेट चाहते हैं?",
        "ml": "നിങ്ങൾ മുമ്പ് ഒരു പരാതി നൽകിയിരുന്നു. അതിന്റെ അപ്‌ഡേറ്റ് വേണോ?",
        "te": "మీరు ముందుగా ఒక ఫిర్యాదు ఇచ్చారు. దానికి అప్డేట్ కావాలా?",
    }

    base = {
        "en": "Thank you. I have noted your complaint and will assist you further.",
        "ta": "நன்றி. உங்கள் புகாரை பதிவு செய்துள்ளேன். தொடர்ந்து உதவுகிறேன்.",
        "hi": "धन्यवाद। आपकी शिकायत दर्ज कर ली गई है। मैं आगे सहायता करता हूँ।",
        "ml": "നന്ദി. നിങ്ങളുടെ പരാതി രേഖപ്പെടുത്തി. തുടർ സഹായം നൽകാം.",
        "te": "ధన్యవాదాలు. మీ ఫిర్యాదును నమోదు చేసాను. నేను ముందుకు సహాయం చేస్తాను.",
    }

    selected_lang = language if language in base else "en"
    reply = base[selected_lang]
    if has_previous_issue:
        reply = f"{reply} {followups[selected_lang]}"
    return reply


def _call_openai_for_response(text: str, language: str, context: Dict[str, object]) -> str:
    endpoint = f"{settings.OPENAI_API_BASE_URL}/chat/completions"
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    prompt = (
        "You are a polite government assistant. Reply in the same language code provided "
        "(en, ta, hi, ml, te). Keep response concise, warm, and helpful."
    )

    response = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {settings.AI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": (
                        f"Language: {language}\n"
                        f"User text: {text}\n"
                        f"Previous issue: {context.get('last_issue', '')}"
                    ),
                },
            ],
            "temperature": 0.4,
        },
        timeout=5,
    )
    response.raise_for_status()
    data = response.json()
    return str(data.get("choices", [{}])[0].get("message", {}).get("content", "")).strip()


def _call_claude_for_response(text: str, language: str, context: Dict[str, object]) -> str:
    endpoint = f"{settings.CLAUDE_API_BASE_URL}/messages"
    model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")

    response = requests.post(
        endpoint,
        headers={
            "x-api-key": settings.AI_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 150,
            "temperature": 0.4,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "You are a polite government assistant. "
                        "Reply in the same language code provided (en, ta, hi, ml, te). "
                        f"Language: {language}. "
                        f"User text: {text}. "
                        f"Previous issue: {context.get('last_issue', '')}."
                    ),
                }
            ],
        },
        timeout=5,
    )
    response.raise_for_status()
    data = response.json()
    chunks = data.get("content", [])
    if isinstance(chunks, list) and chunks:
        return str(chunks[0].get("text", "")).strip()
    return ""


def generate_response(text: str, language: str, context: Dict[str, object]) -> str:
    has_previous_issue = bool(str(context.get("last_issue", "")).strip())

    if settings.AI_API_KEY:
        try:
            provider = settings.AI_MODEL_PROVIDER.lower().strip()
            if provider == "openai":
                ai_response = _call_openai_for_response(text, language, context)
            elif provider == "claude":
                ai_response = _call_claude_for_response(text, language, context)
            else:
                ai_response = ""

            if ai_response:
                return ai_response
        except Exception:
            pass

    return _fallback_response(language, has_previous_issue)
