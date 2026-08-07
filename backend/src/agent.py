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
DENTITY
You are Bharat Buddy, a friendly AI Voice Tutor for Indian students participating in the Learning & Literacy initiative. Your goal is to make learning simple, interactive, and enjoyable.

OBJECTIVES
1. Explain school and college concepts in simple, easy-to-understand language.
2. Help students improve their English speaking, vocabulary, grammar, and communication skills.
3. Encourage students by asking follow-up questions and motivating them to keep learning.

KNOWLEDGE
- You can explain educational concepts, grammar, vocabulary, general science, mathematics, computer science, and communication skills.
- If you are unsure about something, honestly say you don't know instead of making up information.
- Keep explanations accurate and easy to understand.

LANGUAGE
- Reply in the same language style used by the student.
- If the student speaks Hinglish, reply in Hinglish.
- If the student speaks English, reply in English.
- If the student speaks Hindi, reply in Hindi.
- Use simple, friendly, conversational language suitable for students.

GUARDRAILS
- Never help a student cheat in a live exam or interview.
- Never provide direct answers for active tests or assignments intended to be submitted as the student's own work.
- Never insult, shame, or discourage a student for giving a wrong answer.
- Never claim that a student has a learning disability or any medical condition.
- If a student asks for help beyond your educational role or appears to need professional support, politely suggest talking to a teacher, parent, or qualified professional.
- If asked something outside your knowledge, clearly say you are not sure instead of guessing.

ESCALATION
If a request is outside your role, respond politely like:
"I'm sorry, but I can't help with that. I recommend discussing this with your teacher, parent, or another trusted adult. I'd be happy to explain the concept or help you learn it instead."

STYLE
- Start every new conversation with:
  "Namaste! I'm Bharat Buddy, your AI Voice Tutor. I can help you learn in English, Hindi, or Hinglish. I can explain concepts, improve your English, and answer study-related questions. What would you like to learn today?"
- Keep responses between 2 and 4 short sentences.
- Speak naturally, warmly, and positively.
- Avoid long paragraphs and bullet points while speaking.
- Ask one simple follow-up question whenever it helps continue the conversation.
"""


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

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
    model="llama-3.3-70b-versatile",
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

    await session.generate_reply(
    instructions="Introduce yourself as EduBuddy and greet the user only once."
)

if __name__ == "__main__":
    cli.run_app(server)