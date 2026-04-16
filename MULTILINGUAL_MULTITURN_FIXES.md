# Multilingual & Multi-Turn Voice System - Comprehensive Fix Summary

**Date:** March 28, 2026  
**Issues Addressed:** Call cutting after first speech, no multi-turn conversation, missing multilingual speech output, no SMS/WhatsApp notifications, missing hold music

---

## Issues Fixed

### 1. **Call Getting Cut After First Speech (Multi-Turn Not Working)**

**Root Cause:**  
TwiML responses were ending with `<Hangup/>` after first message instead of looping back with `<Record>` tag.

**Fix Applied:**
- ✅ Modified `generate_followup_response_xml()` to return TwiML with:
  - Say tag for acknowledgment
  - Pause for breathing room
  - Say tag for "another complaint?" prompt
  - Pause before recording
  - `<Record>` tag WITHOUT `<Hangup>` (enables loop-back to `/process-recording`)
  - Added `timeout="5"` and `maxSilence="3"` attributes for better silence detection

**Result:**
- Turn 1: User speaks → Agent acknowledges → Agent asks for another complaint → User can speak again
- Turn 2: User speaks second complaint → Agent acknowledges → Agent asks again
- Turn 3: User speaks third complaint → Agent says final goodbye + `<Hangup/>`
- Max 3 turns per call (configurable in [voice_routes.py](app/routes/voice_routes.py#L663))

**Code Location:** [app/services/twilio_voice_service.py](app/services/twilio_voice_service.py#L137)

---

### 2. **No Notifications (SMS/WhatsApp Not Received)**

**Root Cause:**
- Mobile number not being preserved in session across requests
- Notifications queued but mobile might be empty in error paths

**Fixes Applied:**
- ✅ Added `update_mobile()` function to [session_service.py](app/services/session_service.py#L17) to update mobile after initial session creation
- ✅ Enhanced `/voice-response` endpoint to capture mobile and normalize to E.164 format (+91XXXXXXXXXX)
- ✅ Added detailed logging when notifications are sent: `"[Voice] Queueing notifications for mobile=%s, ticket_id=%s..."`
- ✅ Added warning logging when mobile is missing: `"No mobile number available for notifications"`
- ✅ Ensured mobile is captured in ALL error paths (timeout, empty text, extraction failure)

**Notification Content Includes:**
- Ticket ID
- Issue type (mapped department, not "General")
- Location and SLA hours
- SMS: Plain text acknowledgment
- WhatsApp: Formatted message with emoji and structured info

**Code Locations:**
- [session_service.py](app/services/session_service.py#L17-L22) - Mobile tracking
- [voice_routes.py](app/routes/voice_routes.py#L800-L809) - Notification logging

---

### 3. **No Tamil/Multilingual Language Speech Output**

**Root Cause:**
Say tags were using generic English voice ("alice") instead of language-specific Twilio voices with language codes.

**Fixes Applied:**
- ✅ Updated `_say_tag()` function to include `language` attribute:
  - English: `<Say voice="alice" language="en-IN">message</Say>`
  - Tamil: `<Say language="ta-IN">வணக்கம்</Say>`
  - Hindi: `<Say language="hi-IN">नमस्ते</Say>`
  - Malayalam: `<Say language="ml-IN">നമസ്കാരം</Say>`
  - Telugu: `<Say language="te-IN">నమస్కారం</Say>`

- ✅ Added `_say_language_code()` mapping function with full language codes
- ✅ Ensured language is detected from first STT result and persisted in session
- ✅ Applied language parameter to ALL TwiML Say tags (initial, followup, final, error responses)

**Language Detection Flow:**
1. User speaks in Tamil → Whisper/Faster-Whisper detects Tamil
2. Language stored in session via `session_service.update_language(call_id, "ta")`
3. All subsequent TwiML responses use `language="ta"` parameter in Say tags
4. Twilio selects appropriate Tamil voice based on ta-IN code

**Supported Languages:**
- 🇮🇳 English (en-IN)
- 🇮🇳 Tamil (ta-IN)
- 🇮🇳 Hindi (hi-IN)
- 🇮🇳 Malayalam (ml-IN)
- 🇮🇳 Telugu (te-IN)

**Code Location:** [app/services/twilio_voice_service.py](app/services/twilio_voice_service.py#L7-L25)

---

### 4. **Missing Wait/Hold Music During Recording**

**Fix Applied:**
- ✅ Added `<Pause length="1" />` tags before and after prompts
- ✅ Added `timeout="5"` to Record tag to prevent indefinite hanging
- ✅ Added `maxSilence="3"` to automatically end recording after 3 seconds of silence
- ✅ Proper spacing in TwiML for natural conversational flow

**User Experience:**
- Agent speaks initial greeting → 1-second pause → Agent explains (e.g., "Speak about your issue")
- Recording starts with clear beep
- User speaks complaint (up to 30 seconds, auto-ends on 3-second silence)
- Agent acknowledges → 1-second pause → Agent asks followup → User can speak again

---

## Multi-Turn Logic Flow

```
┌─ Call Initiated ─┐
│  /voice-response │
│  Initial prompt  │
│  + Record        │
└──────┬───────────┘
       │
       ▼
   User speaks complaint #1
       │
       ▼
┌─ /process-recording ─┐
│  Extract issue       │
│  Create Ticket       │
│  turn_count = 1      │
└──────┬───────────────┘
       │
       ├─→ turn_count (1) < max_turns (3)? ✓ YES
       │
       ▼
┌─ Return TwiML ─┐
│ Acknowledgment  │
│ Followup Prompt │
│ Record (no end) │
└──────┬──────────┘
       │
       ▼
   User speaks complaint #2
       │
       ▼
┌─ /process-recording ─┐
│  Extract issue       │
│  Create Ticket       │
│  turn_count = 2      │
└──────┬───────────────┘
       │
       ├─→ turn_count (2) < max_turns (3)? ✓ YES
       │
       ▼
   (Repeat pattern...)
       │
       ▼
   User speaks complaint #3
       │
       ▼
┌─ /process-recording ─┐
│  Extract issue       │
│  Create Ticket       │
│  turn_count = 3      │
└──────┬───────────────┘
       │
       ├─→ turn_count (3) < max_turns (3)? ✗ NO
       │
       ▼
┌─ Return Final TwiML ─┐
│ Final  Acknowledgment│
│ Hangup (call ends)   │
└─────────────────────┘
```

---

## Testing Checklist

After receiving a test call, verify in database:

```sql
-- Find latest tickets for call SID
SELECT ticket_id, issue, issue_type, department, sla_hours, created_at
FROM tickets
WHERE call_id = 'CAe2f96227a17c3bb4730ab679cad7e1d0'
ORDER BY created_at DESC;
```

**Expected Output:**
- ✅ Multiple tickets (one per complaint spoken)
- ✅ issue: Contains user's exact Tamil/Hindi speech text
- ✅ issue_type: Mapped correctly (not "General") - e.g., "Garbage", "Road", "Water", "Electricity"
- ✅ department: Correct department - e.g., "Sanitation", "PWD", "Municipality", "Electricity Board"
- ✅ sla_hours: Correct SLA based on issue type - e.g., 24h for Water, 48h for Road, 6h for Electricity
- ✅ SMS/WhatsApp: Received confirmation message with Ticket ID

**Check Notifications:**
```
Expected SMS: "Dear Citizen, your complaint has been registered. Ticket ID: TKT-XXXXXX Priority: LOW Department: Sanitation Resolution within: 24 hours."

Expected WhatsApp: "Hello Citizen! 👋
🎫 Ticket ID: TKT-XXXXXX
📋 Issue: [user's speech]
🏢 Department: Sanitation
📍 Location: [extracted from speech]
⏰ SLA: 24 hours"
```

---

## Code Changes Summary

### Modified Files:

1. **[app/services/twilio_voice_service.py](app/services/twilio_voice_service.py)**
   - Added `_say_language_code()` - Maps language codes to Twilio codes
   - Updated `_say_tag()` - Adds language attribute to Say tags
   - Updated `generate_response_xml()` - Added timeout and maxSilence
   - Updated `generate_followup_response_xml()` - Fixed multi-turn loop structure
   - Updated `generate_final_message_xml()` - Added Pause for UX

2. **[app/services/session_service.py](app/services/session_service.py)**
   - Added `update_mobile()` - Update mobile in existing session
   - Existing `increment_turn()` - Unchanged, working correctly

3. **[app/routes/voice_routes.py](app/routes/voice_routes.py)**
   - Updated `_voice_response_impl()` - Capture and normalize mobile, update session
   - Added multi-turn decision logging - Debug trace for turn decisions
   - Enhanced notification calls - Added logging for SMS/WhatsApp sends
   - Fixed language parameter propagation - Pass language to all TwiML generators

---

## Deployment Notes

- ✅ All files syntax-validated (py_compile)
- ✅ Session logic tested independently - turn counting works correctly
- ✅ TwiML generation tested - correct tags, attributes, language codes
- ✅ Backward compatible - no breaking changes to existing endpoints
- ✅ Error paths preserved - graceful handling of STT failures

---

## Known Limitations

1. **Tamil STT Quality**: Whisper model performs adequately on Tamil but not perfect (beam size increased for Indic languages). Consider fine-tuned model for production.
2. **Session Persistence**: In-memory sessions lost on backend restart. Use Redis for production multi-instance deployments.
3. **Hold Music**: Currently using Pause tags only. Can add Play tag with royalty-free music URL for enhanced experience.

---

## Next Steps for User

1. **Listen to incoming call** on +919843398325
2. **Speak complaint** in Tamil/Hindi/English
3. **Listen for agent's followup prompt** (agent should speak in same language detected)
4. **Speak another complaint** (if desired) or say "no"/"இல்லை"/"नहीं" to end
5. **Check SMS/WhatsApp** for ticket confirmation within 30 seconds
6. **Check database** for tickets with correct mapping (issue_type, department, SLA)

**Expected Duration:** ~30-45 seconds per call  
**Backend Logs:** [backend_multiturn_final.log](backend_multiturn_final.log) - Check for detailed multi-turn decision logs

---

**Status:** ✅ **READY FOR PRODUCTION TESTING**

Test Call SID: `CAe2f96227a17c3bb4730ab679cad7e1d0`
