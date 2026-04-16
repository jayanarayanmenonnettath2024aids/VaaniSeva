"""Backward-compatible alias module.

The runtime voice provider is now Twilio.
Legacy imports from this module continue to work by proxying to
`app.services.twilio_voice_service`.
"""

from app.services.twilio_voice_service import create_call, generate_processing_response_xml, generate_response_xml
