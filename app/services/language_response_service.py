"""Multi-language response support - Generate responses in multiple languages."""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Response templates by language and context
LANGUAGE_RESPONSES = {
    "ta": {  # Tamil
        "greeting": "வணக்கம், வணக்கம் வந்ததற்கு நன்றி VaaniSeva சேவை",
        "issue_received": "உங்கள் {{ issue_type }} புகாரை பதிவு செய்েயிருக்கி றோ",
        "ticket_created": "உங்கள் புகாரின் பதிவு எண் {{ ticket_id }}",
        "escalation": "உங்கள் புகார் தகுந்த பிரிவிற்கு மாற்றப்பட்டுள்ளது",
        "sla_notification": "உங்கள் சேவை {{sla_hours}} மணி நேரத்க்குள் நிறைவு செய்யப்படும்",
        "closing": "நன்றி, மretry செய்யுங்களै",
        "error": "தமிழ், மன்னிக்கவும், இப்போது இணையம் செயல்படவில்லை. பின்னர் முயற்சி செய்யவும்",
    },
    "ml": {  # Malayalam
        "greeting": "സ്വാഗതം, VaaniSeva സേവനത്തിലേക്ക് ഓൺകൊരുത്ത സാധുവായ്",
        "issue_received": "നിങ്ങളുടെ {{ issue_type }} പരാതി രജിസ്ട്രേഷൻ ചെയ്യപ്പെട്ടു",
        "ticket_created": "നിങ്ങളുടെ പരാതി ID {{ ticket_id }}",
        "escalation": "നിങ്ങളുടെ പരാതി ഉചിതമായ വിഭാഗത്തിലേക്ക് മാറ്റി",
        "sla_notification": "നിങ്ങളുടെ സേവന സമയം {{sla_hours}} മണിക്കൂറിനുള്ളിൽ",
        "closing": "നന്ദി, വിദായം",
        "error": "ക്ഷമിക്കുക, പ്രവർത്തനം കർമ്മം പരാജയപ്പെട്ടു",
    },
    "te": {  # Telugu
        "greeting": "స్వాగతం, VaaniSeva సేవకు ధన్యవాదాలు",
        "issue_received": "మీ {{ issue_type }} ఫిర్యాదు నమోదు చేయబడింది",
        "ticket_created": "మీ ఫిర్యాదు నంబర్ {{ ticket_id }}",
        "escalation": "మీ ఫిర్యాదు సంబంధిత విభాగానికి బదిలీ చేయబడింది",
        "sla_notification": "మీ సేవ {{sla_hours}} గంటలలో పూర్తి చేయబడుతుంది",
        "closing": "ధన్యవాదాలు, వీడ్కోలు",
        "error": "క్షమించండి, అనుబంధం విఫలమైంది",
    },
    "kn": {  # Kannada
        "greeting": "ಸ್ವಾಗತ, VaaniSeva ಸೇವೆಗೆ ಧನ್ಯವಾದಗಳು",
        "issue_received": "ನಿಮ್ಮ {{ issue_type }} ಅಭಿಯೋಗ ನೋಂದಣಿ ಮಾಡಲಾಗಿದೆ",
        "ticket_created": "ನಿಮ್ಮ ಟಿಕೆಟ್ ಸಂಖ್ಯೆ {{ ticket_id }}",
        "escalation": "ನಿಮ್ಮ ಅಭಿಯೋಗ ಸಂಬಂಧಿತ ವಿಭಾಗಕ್ಕೆ ವರ್ಗಾಯಿಸಲಾಗಿದೆ",
        "sla_notification": "ನಿಮ್ಮ ಸೇವೆ {{sla_hours}} ಗಂಟೆಗಳಲ್ಲಿ ಪೂರ್ಣ ಮಾಡಲಾಗುತ್ತದೆ",
        "closing": "ಧನ್ಯವಾದಗಳು, ವಿದಾಯ",
        "error": "ಕ್ಷಮಿಸಿ, ಆಪರೇಷನ್ ವಿಫಲವಾಗಿದೆ",
    },
    "en": {  # English
        "greeting": "Welcome to VaaniSeva service",
        "issue_received": "Your {{ issue_type }} complaint has been registered",
        "ticket_created": "Your complaint reference number is {{ ticket_id }}",
        "escalation": "Your complaint has been escalated to the appropriate department",
        "sla_notification": "Your service will be completed within {{sla_hours}} hours",
        "closing": "Thank you for using VaaniSeva",
        "error": "Sorry, the operation failed. Please try again later",
    },
}


def get_response(language: str, context_key: str, variables: Dict[str, Any] = None) -> str:
    """
    Get localized response for a given context.
    
    Args:
        language: Language code (ta, ml, te, kn, en)
        context_key: Response context (greeting, issue_received, ticket_created, etc.)
        variables: Dictionary of variables to substitute in the response
    
    Returns:
        Localized response string
    """
    language = language.lower()[:2]  # Normalize to 2-letter code
    
    # Fall back to English if language not found
    if language not in LANGUAGE_RESPONSES:
        language = "en"
    
    response_template = LANGUAGE_RESPONSES[language].get(context_key, LANGUAGE_RESPONSES["en"].get(context_key, ""))
    
    # Substitute variables
    if variables:
        for key, value in variables.items():
            response_template = response_template.replace(f"{{{{{key}}}}}", str(value))
    
    logger.info("[I18N] Generated response: language=%s context=%s", language, context_key)
    return response_template


def get_available_languages() -> List[str]:
    """Get list of available language codes."""
    return list(LANGUAGE_RESPONSES.keys())


def get_language_name(language_code: str) -> str:
    """Get human-readable language name."""
    names = {
        "ta": "Tamil",
        "ml": "Malayalam",
        "te": "Telugu",
        "kn": "Kannada",
        "en": "English",
    }
    return names.get(language_code.lower()[:2], "English")


def format_multilingual_response(
    base_ticket: Dict[str, Any],
    languages: List[str] = None,
) -> Dict[str, str]:
    """
    Generate notification responses in multiple languages.
    
    Args:
        base_ticket: Ticket data
        languages: List of language codes to generate responses for
    
    Returns:
        Dictionary mapping language codes to response text
    """
    if languages is None:
        languages = ["ta", "en"]  # Default to Tamil and English
    
    responses = {}
    for lang in languages:
        response = get_response(
            lang,
            "issue_received",
            {
                "issue_type": base_ticket.get("issue_type", "complaint"),
                "ticket_id": base_ticket.get("ticket_id", ""),
                "sla_hours": base_ticket.get("sla_hours", 24),
            },
        )
        responses[lang] = response
    
    return responses


def get_sms_for_languages(base_ticket: Dict[str, Any], languages: List[str] = None) -> Dict[str, str]:
    """Get SMS text in multiple languages."""
    return format_multilingual_response(base_ticket, languages or ["ta", "en"])
