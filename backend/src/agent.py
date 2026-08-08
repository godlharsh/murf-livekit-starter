import logging

from dotenv import load_dotenv
from livekit import rtc

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    tokenize,
    room_io,
)

from livekit.plugins import (
    murf,
    silero,
    groq,
    deepgram,
    noise_cancellation,
)

from livekit.plugins.turn_detector.multilingual import MultilingualModel


logger = logging.getLogger("agent")

load_dotenv(".env.local")


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
LANGUAGE

- Understand whether the user is speaking English, Hindi, or Hinglish
  and respond naturally in the same language.

- If the user speaks English, respond in natural, clear Indian English.

- If the user speaks Hindi, respond in natural Indian Hindi with
  clear Hindi pronunciation, natural Indian rhythm, and natural
  Indian sentence flow.

- Do NOT speak Hindi with an American, British, or foreign accent.

- If the user speaks Hinglish, respond in natural Indian Hinglish,
  like a normal Indian student or teacher speaking casually.

- Keep Hindi and Hinglish pronunciation natural for Indian listeners.

- Use simple, everyday Hindi instead of highly formal or Sanskritized Hindi.

- Common English words such as "concept", "example", "practice",
  "problem", "answer", and "explain" can naturally remain in English
  when speaking Hinglish.

- If the user speaks English, continue in English.

- If the user speaks Hindi, continue in Hindi.

- If the user speaks Hinglish, continue in Hinglish.

- Follow the user's language naturally and do not randomly switch
  between languages.

- If the user's speech is unclear, use the conversation context to
  determine whether they are speaking English, Hindi, or Hinglish.

- Keep the overall tone friendly, casual, clear, and natural for
  Indian students.

- Keep sentences short and conversational because all responses
  are spoken aloud.
"""


# ============================================================
# ASSISTANT
# ============================================================

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT
        )


# ============================================================
# LIVEKIT SERVER
# ============================================================

server = AgentServer()


# ============================================================
# PREWARM
# ============================================================

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


# ============================================================
# VOICE AGENT
# ============================================================

@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):

    # --------------------------------------------------------
    # Logging
    # --------------------------------------------------------

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # ========================================================
    # VOICE AI PIPELINE
    # ========================================================

    session = AgentSession(

        # ----------------------------------------------------
        # SPEECH TO TEXT
        # ----------------------------------------------------

        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),

        # ----------------------------------------------------
        # LARGE LANGUAGE MODEL
        # ----------------------------------------------------

        llm=groq.LLM(
            model="llama-3.1-8b-instant",
        ),

        # ----------------------------------------------------
        # TEXT TO SPEECH
        # ----------------------------------------------------

        tts=murf.TTS(
            voice="Abhinav",
            style="Conversational",
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2
            ),
            text_pacing=True,
        ),

        # ----------------------------------------------------
        # MULTILINGUAL TURN DETECTION
        # ----------------------------------------------------

        turn_detection=MultilingualModel(),

        # ----------------------------------------------------
        # VOICE ACTIVITY DETECTION
        # ----------------------------------------------------

        vad=ctx.proc.userdata["vad"],

        # ----------------------------------------------------
        # PREEMPTIVE GENERATION
        # ----------------------------------------------------

        preemptive_generation=True,
    )

    # ========================================================
    # START SESSION
    # ========================================================

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # ========================================================
    # CONNECT TO LIVEKIT ROOM
    # ========================================================

    await ctx.connect()


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    cli.run_app(server)