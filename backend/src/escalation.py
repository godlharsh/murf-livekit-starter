from livekit.agents import function_tool
import uuid
import datetime
import requests
import os

# Simple in-memory store — prevents duplicate open tickets for same learner+reason
open_escalations = {}

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")  # put this in .env.local

@function_tool
async def create_escalation(
    learner_name: str,
    reason: str,
    already_checked: str,
    urgency: str,          # "low" | "medium" | "high" | "emergency"
    language: str,
    follow_up_method: str
) -> str:
    """
    Call this ONLY after the learner has given explicit permission.
    Creates a human escalation when the learner is emotionally distressed
    or needs a real teacher/human instead of the AI tutor.
    """
    key = f"{learner_name}:{reason}"
    if key in open_escalations:
        return f"There's already an open request for this: {open_escalations[key]}"

    ref_id = f"ESC-{uuid.uuid4().hex[:6].upper()}"
    summary = {
        "ref_id": ref_id,
        "who": learner_name,
        "what_happened": reason,
        "already_checked": already_checked,
        "urgency": urgency,
        "language": language,
        "follow_up_method": follow_up_method,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "status": "open"
    }
    open_escalations[key] = ref_id

    message = (
        f"🆘 **New Escalation: {ref_id}**\n"
        f"Who: {summary['who']}\n"
        f"What: {summary['what_happened']}\n"
        f"Already checked: {summary['already_checked']}\n"
        f"Urgency: {summary['urgency']}\n"
        f"Language: {summary['language']}\n"
        f"Follow-up: {summary['follow_up_method']}\n"
        f"Status: open"
    )
    requests.post(DISCORD_WEBHOOK_URL, json={"content": message})

    return f"Escalation created. Reference ID: {ref_id}"