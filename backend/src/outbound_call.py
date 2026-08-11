# ============================================================
# BHARAT BUDDY
# Day 6 - Outbound Call Launcher
# ============================================================

import asyncio
import json
import logging
import os
from uuid import uuid4

from dotenv import load_dotenv
from livekit import api


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(".env.local")


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("bharat-buddy-outbound")


# ============================================================
# CONFIGURATION
# ============================================================

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

LIVEKIT_SIP_TRUNK_ID = os.getenv("LIVEKIT_SIP_TRUNK_ID")

AGENT_NAME = os.getenv(
    "AGENT_NAME",
    "my-agent",
)

# For Linphone this should be a SIP address, for example:
# sip:bihari@sip.linphone.org
OUTBOUND_DESTINATION = os.getenv("OUTBOUND_DESTINATION")


# ============================================================
# VALIDATE ENVIRONMENT
# ============================================================

def validate_environment() -> None:
    required_variables = {
        "LIVEKIT_URL": LIVEKIT_URL,
        "LIVEKIT_API_KEY": LIVEKIT_API_KEY,
        "LIVEKIT_API_SECRET": LIVEKIT_API_SECRET,
        "LIVEKIT_SIP_TRUNK_ID": LIVEKIT_SIP_TRUNK_ID,
        "OUTBOUND_DESTINATION": OUTBOUND_DESTINATION,
    }

    missing = [
        name
        for name, value in required_variables.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
        )


# ============================================================
# CREATE SAFE SIP IDENTITY
# ============================================================

def make_participant_identity(destination: str) -> str:
    clean_destination = "".join(
        character
        for character in destination
        if character.isalnum()
    )

    return "phone_" + clean_destination[-24:]


# ============================================================
# MAKE OUTBOUND CALL
# ============================================================

async def make_call(destination: str) -> None:

    validate_environment()

    destination = destination.strip()

    if not destination:
        raise ValueError(
            "Outbound destination cannot be empty."
        )

    # --------------------------------------------------------
    # Create unique LiveKit room
    # --------------------------------------------------------

    room_name = (
        "bharat_buddy_outbound_"
        + uuid4().hex[:12]
    )

    participant_identity = make_participant_identity(
        destination
    )

    # --------------------------------------------------------
    # Metadata passed to agent.py
    # --------------------------------------------------------

    metadata = json.dumps(
        {
            "phone_number": destination,
            "call_type": "outbound",
        }
    )

    logger.info(
        "Starting Bharat Buddy outbound call"
    )

    logger.info(
        "Agent: %s",
        AGENT_NAME,
    )

    logger.info(
        "Room: %s",
        room_name,
    )

    logger.info(
        "Destination: %s",
        destination,
    )

    # --------------------------------------------------------
    # LiveKit API client
    # --------------------------------------------------------

    livekit_api = api.LiveKitAPI(
        url=LIVEKIT_URL,
        api_key=LIVEKIT_API_KEY,
        api_secret=LIVEKIT_API_SECRET,
    )

    try:

        # ====================================================
        # START AGENT DISPATCH
        # ====================================================

        dispatch = (
            await livekit_api.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(
                    agent_name=AGENT_NAME,
                    room=room_name,
                    metadata=metadata,
                )
            )
        )

        logger.info(
            "Agent dispatch created successfully."
        )

        logger.info(
            "Dispatch ID: %s",
            dispatch.id,
        )

        # ====================================================
        # CREATE SIP PARTICIPANT
        # ====================================================

        logger.info(
            "Creating SIP participant..."
        )

        sip_participant = (
            await livekit_api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    sip_trunk_id=LIVEKIT_SIP_TRUNK_ID,
                    sip_call_to=destination,
                    room_name=room_name,
                    participant_identity=participant_identity,
                    participant_name="Bharat Buddy",
                    wait_until_answered=True,
                )
            )
        )

        # ====================================================
        # SUCCESS
        # ====================================================

        logger.info(
            "SIP participant created successfully."
        )

        logger.info(
            "Participant identity: %s",
            participant_identity,
        )

        logger.info(
            "Outbound call connected successfully!"
        )

        logger.info(
            "Bharat Buddy is now connected to the call."
        )

    except Exception as error:

        logger.exception(
            "Outbound call failed: %s",
            error,
        )

        raise

    finally:

        await livekit_api.aclose()


# ============================================================
# MAIN
# ============================================================

async def main() -> None:

    validate_environment()

    destination = OUTBOUND_DESTINATION.strip()

    logger.info(
        "Using configured outbound destination."
    )

    await make_call(destination)


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    asyncio.run(main())