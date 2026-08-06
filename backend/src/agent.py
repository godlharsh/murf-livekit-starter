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
from livekit.plugins import murf, silero, groq, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")


SYSTEM_PROMPT = """
You are Bharat Voice Tutor, a friendly English teacher for Indian students.

Rules:
- Greet the user only once at the beginning of the conversation.
- Do not repeat greetings.
- Do not say thank you unless the user actually thanks you.
- Keep every response under 40 words.
- Ask one follow-up question after every answer.
"""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT
        )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Connect to LiveKit room first
    await ctx.connect()


    session = AgentSession(

        # Speech to Text
        stt=deepgram.STT(
            model="nova-3"
        ),

        # LLM Brain
        llm=groq.LLM(
            model="llama-3.1-8b-instant",
        ),

        # Text to Speech
        tts=murf.TTS(
            voice="Pooja",
            style="Conversational",
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2
            ),
            text_pacing=True
        ),

        # Voice detection
        turn_detection=MultilingualModel(),

        vad=ctx.proc.userdata["vad"],

        preemptive_generation=False,
    )


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


if __name__ == "__main__":
    cli.run_app(server)