from typing import Dict

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


def generate_response(text: str, language: str, context: Dict[str, object]) -> str:
    has_previous_issue = bool(str(context.get("last_issue", "")).strip())
    recent_calls = context.get("recent_calls", [])
    if isinstance(recent_calls, list) and recent_calls:
        has_previous_issue = True
    # Local-only mode: response generation remains deterministic and offline-safe.
    if settings.AI_MODEL_PROVIDER.lower().strip() == "local":
        return _fallback_response(language, has_previous_issue)

    return _fallback_response(language, has_previous_issue)
