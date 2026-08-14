# ============================================================
# BHARAT BUDDY
# Day 9 - Specialist Handoff Agent (Fixed)
# ============================================================

import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
from livekit import rtc

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
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


# ============================================================
# PATH
# ============================================================

SRC_DIR = Path(__file__).resolve().parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from learning_data import find_exercise
from escalation import create_escalation
from calls import init_calls_db, start_call, end_call
from maths_specialist import MathsSpecialist


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger("bharat-buddy")

load_dotenv(".env.local")

init_calls_db()


# ============================================================
# SYSTEM PROMPT (SHORTENED TO SAVE TOKENS)
# ============================================================

SYSTEM_PROMPT = """
IDENTITY

You are Bharat Buddy, a friendly AI Voice Tutor for Indian students.

USER

The user's name is Rishabh. If they ask their name, say "Your name is Harsh."

LANGUAGE & SCRIPT

Reply in the language the student uses (English, Hindi, or Hinglish).
Hindi must always be written in Devanagari script (नमस्ते), never romanized.
Keep replies short (2-4 sentences), since they are spoken aloud.

TOOLS

1. get_next_exercise - use for Python, English grammar, or Computer Science
   practice questions. Default level=beginner if the student doesn't say one.
   Never invent an exercise yourself; only use what the tool returns.

2. handoff_to_maths_specialist - use ONLY when the student wants to practice
   mathematics or solve a maths problem. ALWAYS call this as a real tool call,
   never write it out as text. Before calling it, say out loud:
   "Sure! Let me connect you to our Maths Specialist."

3. create_escalation - use ONLY if the student sounds emotionally distressed
   (upset, hopeless, wants to give up) OR explicitly asks for a real teacher.
   Always ask permission first, and only call this if they say yes. Never
   include passwords, OTPs, PINs, or account numbers in the summary.

RULES

- Never insult, shame, or diagnose a student.
- Never help with cheating on live exams or assignments.
- Introduce yourself only once, at the start of the conversation.
- Do not mention tool names, JSON, or implementation details to the student.

FIRST GREETING (browser conversations)

"Namaste! I'm Bharat Buddy, your AI Voice Tutor. I can help you learn in
English, Hindi, or Hinglish. What would you like to learn today?"

OUTBOUND CALLS

Introduce yourself as Bharat Buddy, explain you're calling for a short
learning practice session, keep the opening short, and let the person end
the call anytime if they're not interested.
"""


# ============================================================
# ASSISTANT
# ============================================================

class Assistant(Agent):

    def __init__(self) -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT
        )
        self.exercise_delivered = False

    # ========================================================
    # DAY 5 LEARNING TOOL
    # ========================================================

    @function_tool(
        name="get_next_exercise",
        description=(
            "Retrieve a real learning practice exercise from the "
            "Bharat Buddy local learning dataset. Use for Python, "
            "English grammar, or Computer Science practice questions. "
            "Do NOT use this for mathematics - use "
            "handoff_to_maths_specialist instead. "
            "If the student does not specify a level, use beginner."
        ),
    )
    async def get_next_exercise(
        self,
        context: RunContext,
        level: str,
        topic: str,
    ) -> str:

        logger.info(
            "TOOL CALL -> get_next_exercise | level=%s | topic=%s",
            level,
            topic,
        )

        try:

            level = level.lower().strip()
            topic = topic.lower().strip()

            if level not in {"beginner", "intermediate"}:
                level = "beginner"

            topic_aliases = {
                "math": "mathematics",
                "maths": "mathematics",
                "english": "english grammar",
                "grammar": "english grammar",
                "coding": "python",
                "programming": "python",
                "python programming": "python",
                "python programming language": "python",
                "cs": "computer science",
                "computer": "computer science",
            }

            topic = topic_aliases.get(topic, topic)

            exercise = find_exercise(level=level, topic=topic)

            if exercise is None:

                logger.warning(
                    "TOOL RESULT -> no exercise | level=%s | topic=%s",
                    level,
                    topic,
                )

                return (
                    "NO_EXERCISE_FOUND. Tell the student this topic is "
                    "currently unavailable and suggest Python, English "
                    "grammar, or Computer Science."
                )

            logger.info(
                "TOOL RESULT -> exercise found | level=%s | topic=%s",
                level,
                topic,
            )

            self.exercise_delivered = True

            return (
                "EXERCISE_FOUND. "
                f"Topic: {exercise['topic']}. "
                f"Level: {exercise['level']}. "
                f"Question: {exercise['question']} "
                f"Answer: {exercise['answer']} "
                f"Explanation: {exercise['explanation']}"
            )

        except Exception as error:

            logger.exception(
                "TOOL ERROR -> get_next_exercise failed: %s",
                error,
            )

            return (
                "TOOL_ERROR. Tell the student the exercise service is "
                "temporarily unavailable and ask them to try again."
            )

    # ========================================================
    # DAY 7 ESCALATION TOOL
    # ========================================================

    @function_tool(
        name="create_escalation",
        description=(
            "Create a human escalation request when the student is "
            "emotionally distressed or explicitly asks for a real "
            "teacher/human. Call this ONLY after the student has given "
            "explicit permission. Decide urgency yourself: "
            "'low', 'medium', 'high', or 'emergency'."
        ),
    )
    async def escalate(
        self,
        context: RunContext,
        learner_name: str,
        reason: str,
        already_checked: str,
        urgency: str,
        language: str,
        follow_up_method: str,
    ) -> str:

        logger.info(
            "TOOL CALL -> create_escalation | reason=%s | urgency=%s",
            reason,
            urgency,
        )

        try:

            result = await create_escalation(
                learner_name=learner_name,
                reason=reason,
                already_checked=already_checked,
                urgency=urgency,
                language=language,
                follow_up_method=follow_up_method,
            )

            logger.info("TOOL RESULT -> create_escalation | %s", result)

            return result

        except Exception as error:

            logger.exception(
                "TOOL ERROR -> create_escalation failed: %s",
                error,
            )

            return (
                "TOOL_ERROR. Tell the student you are having trouble "
                "reaching the support team and to try again shortly."
            )

    # ========================================================
    # DAY 9 - HANDOFF TO MATHS SPECIALIST
    # ========================================================

    @function_tool(
        name="handoff_to_maths_specialist",
        description=(
            "Hand off the conversation to the Maths Practice Specialist. "
            "Use this ONLY when the student wants to practice mathematics "
            "or solve a maths problem. Do NOT use for Python, grammar, "
            "or computer science."
        ),
    )
    async def handoff_to_maths_specialist(
        self,
        context: RunContext,
        reason: str,
    ) -> Agent:

        logger.info(
            "HANDOFF -> transferring to Maths Specialist | reason=%s",
            reason,
        )

        try:
            await context.session.say(
                "Sure! Let me connect you to our Maths Specialist "
                "who can help you better with this."
            )
        except Exception:
            pass

        return MathsSpecialist(chat_ctx=self.chat_ctx)


# ============================================================
# LIVEKIT SERVER
# ============================================================

server = AgentServer()


# ============================================================
# PREWARM
# ============================================================

def prewarm(proc: JobProcess) -> None:

    logger.info("Loading Silero VAD...")

    proc.userdata["vad"] = silero.VAD.load()

    logger.info("Silero VAD loaded successfully.")


server.setup_fnc = prewarm


# ============================================================
# VOICE AGENT
# ============================================================

@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    logger.info(
        "Bharat Buddy session starting | room=%s",
        ctx.room.name,
    )

    # ========================================================
    # CHECK OUTBOUND CALL METADATA
    # ========================================================

    outbound_phone = None

    try:

        metadata = ctx.job.metadata

        if metadata:
            data = json.loads(metadata)
            outbound_phone = data.get("phone_number")

    except (json.JSONDecodeError, TypeError):

        logger.warning(
            "Job metadata was not valid outbound JSON: %s",
            ctx.job.metadata,
        )

    if outbound_phone:
        logger.info(
            "Outbound call detected | destination=%s",
            outbound_phone,
        )

    # ========================================================
    # DAY 8 - START CALL TRACKING
    # ========================================================

    call_id = ctx.room.name
    channel = "sip" if outbound_phone else "browser"
    start_call(call_id=call_id, channel=channel)

    # ========================================================
    # VOICE AI PIPELINE
    # ========================================================

    session = AgentSession(

        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),

        llm=groq.LLM(
            model="llama-3.3-70b-versatile",
        ),

        tts=murf.TTS(
            voice="Anisha",
            style="Conversational",
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2,
            ),
            text_pacing=True,
        ),

        turn_detection=MultilingualModel(),

        vad=ctx.proc.userdata["vad"],

        max_tool_steps=3,

        preemptive_generation=True,
    )

    # ========================================================
    # START SESSION
    # ========================================================

    assistant = Assistant()

    await session.start(
        agent=assistant,
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

    logger.info("Bharat Buddy session started successfully.")

    # ========================================================
    # DAY 8 - END CALL TRACKING ON SHUTDOWN (ASYNC FIXED)
    # ========================================================

    async def _on_shutdown():
        end_call(
            call_id=call_id,
            success=assistant.exercise_delivered,
            reason="exercise_completed" if assistant.exercise_delivered else "no_exercise_delivered",
        )
        logger.info(
            "Call ended | call_id=%s | success=%s",
            call_id,
            assistant.exercise_delivered,
        )

    ctx.add_shutdown_callback(_on_shutdown)

    # ========================================================
    # CONNECT TO LIVEKIT ROOM
    # ========================================================

    await ctx.connect()

    logger.info(
        "Bharat Buddy connected to room=%s",
        ctx.room.name,
    )

    # ========================================================
    # OUTBOUND CALL GREETING
    # ========================================================

    if outbound_phone:

        participant_identity = (
            "phone_" +
            "".join(
                character
                for character in outbound_phone
                if character.isalnum()
            )[-24:]
        )

        try:

            participant = await ctx.wait_for_participant(
                identity=participant_identity,
            )

            logger.info(
                "Outbound SIP participant connected | identity=%s",
                participant.identity,
            )

            try:
                await ctx.wait_for_participant(
                    identity=participant_identity,
                    kind=rtc.ParticipantKind.PARTICIPANT_KIND_SIP,
                )
            except Exception:
                pass

            await session.generate_reply(
                instructions=(
                    "This is an outbound call. Start the conversation "
                    "immediately. Say who you are, why you are calling, "
                    "and that the person can end the call anytime. Keep "
                    "it short and friendly. Do not mention APIs, tools, "
                    "LiveKit, SIP, or technical details."
                ),
            )

        except Exception as error:

            logger.exception(
                "Outbound participant did not connect: %s",
                error,
            )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    cli.run_app(server)