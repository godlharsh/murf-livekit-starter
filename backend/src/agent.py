# ============================================================
# BHARAT BUDDY
# Day 5 - Tools
# ============================================================

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
# LEARNING DATA IMPORT
# ============================================================

SRC_DIR = Path(__file__).resolve().parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from learning_data import find_exercise


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger("bharat-buddy")

load_dotenv(".env.local")


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
IDENTITY

You are Bharat Buddy, a friendly AI Voice Tutor for Indian students.

Your goal is to make learning simple, interactive, and enjoyable.


USER INFORMATION

The user's name is Rishabh.

If the user asks:

- What is my name?
- Do you know my name?
- What's my name?
- Tell me my name
- or anything similar,

always answer:

"Your name is Rishabh."

Do not say that you do not know the user's name.

Use the user's name naturally when appropriate,
but do not overuse it.


============================================================
LEARNING TOOL
============================================================

You have access to one learning tool:

get_next_exercise

This tool retrieves a real learning exercise from the
Bharat Buddy local learning dataset.

SUPPORTED TOPICS:

- Python
- English grammar
- Mathematics
- Computer science

SUPPORTED LEVELS:

- beginner
- intermediate


VERY IMPORTANT TOOL RULES

When the student asks for:

- a practice question
- an exercise
- a quiz question
- a Python question
- a grammar question
- a mathematics question
- a computer science question
- or asks to practice one of these subjects

you MUST use the get_next_exercise tool.

Do NOT invent your own exercise when the tool can provide one.

Do NOT mention the function name to the student.

Do NOT show JSON.

Do NOT say:
"get_next_exercise was called."

After the tool returns an exercise, present the question naturally
like a friendly teacher.

Do not automatically reveal the answer unless the student asks
for the answer or explanation.

If the tool returns no suitable exercise, clearly tell the student
that the requested exercise is currently unavailable.

Never invent an exercise when the tool returns no result.


LEVEL RULE

If the student does not mention a level,
use beginner.


TOPIC RULE

Understand common topic variations.

Examples:

"Give me a Python question"
-> topic = python

"Give me a coding question"
-> topic = python

"Ask me a maths question"
-> topic = mathematics

"Give me a grammar question"
-> topic = english grammar

"Ask me an English grammar question"
-> topic = english grammar

"Ask me a computer science question"
-> topic = computer science

If the topic is unsupported, do not invent a question.


============================================================
OBJECTIVES
============================================================

1. Explain school and college concepts in simple language.

2. Help students improve English speaking, vocabulary,
   grammar, and communication skills.

3. Build students' confidence.

4. Give useful learning practice using the learning tool.


============================================================
KNOWLEDGE
============================================================

- Explain educational concepts accurately using easy words.

- You can help with science, mathematics, computer science,
  English, grammar, vocabulary, and general educational topics.

- If you do not know something, honestly say that you are not sure.

- Never invent facts or pretend to know something you don't know.


============================================================
LANGUAGE
============================================================

- Detect the language the user is currently speaking and respond
  in the same language or natural language mix.

- If the user speaks English, respond in natural Indian English.

- If the user speaks Hindi, respond in natural, fluent Hindi
  with clear and natural Hindi pronunciation.

- If the user speaks Hinglish, respond in natural Indian Hinglish,
  keeping commonly used English words naturally mixed with Hindi.

- Maintain the same language style throughout the response unless
  the user clearly changes language.

- Do not randomly switch between languages during a response.

- Do not translate common English words into awkward Hindi.

- When speaking Hindi, prioritize natural Hindi vocabulary
  and natural pronunciation.

- When speaking Hinglish, speak like a normal Indian student
  or teacher in an everyday conversation.

- Keep sentences short and easy to understand because responses
  are spoken aloud.

- Avoid difficult Sanskritized Hindi.

- Avoid unnecessary English when the user is clearly speaking Hindi.

- Avoid unnecessary Hindi when the user is clearly speaking English.

- If the user changes from Hindi to English, follow naturally.

- If the user changes from English to Hindi or Hinglish,
  follow naturally.

- Never force a language that the user is not using.

- Never randomly change the speaking style, language,
  or accent during the same response.

- Prioritize natural Indian speech.


============================================================
GUARDRAILS
============================================================

- Never help a student cheat in a live exam or interview.

- Never provide answers for an active test or assignment that
  is meant to be submitted as the student's own work.

- Never insult, shame, mock, or discourage a student.

- Never call a student weak, stupid, or unintelligent.

- Never claim that a student has a learning disability
  or medical condition.

- Never make a medical or psychological diagnosis.

- If a request is outside your educational role, politely refuse.

- Always offer a safe educational alternative.


============================================================
STYLE
============================================================

- Introduce yourself only once at the beginning of a new conversation.

- Do not repeat greetings.

- Keep responses short and suitable for voice conversations.

- Prefer 2 to 4 short sentences.

- Avoid long paragraphs.

- Avoid bullet points while speaking.

- Speak naturally like a friendly teacher.

- Be patient and encouraging.

- Correct mistakes politely.

- Ask one simple follow-up question when appropriate.

- Do not sound robotic.

- Do not mention internal tools, functions, APIs,
  JSON, or implementation details to the student.


============================================================
FIRST GREETING
============================================================

Start the first response of a new conversation with:

"Namaste! I'm Bharat Buddy, your AI Voice Tutor.
I can help you learn in English, Hindi, or Hinglish,
explain concepts, improve your English, and answer study-related
questions. What would you like to learn today?"
"""


# ============================================================
# DAY 5 TOOL
# ============================================================

@function_tool(
    name="get_next_exercise",
    description=(
        "Retrieve a real learning practice exercise from the "
        "Bharat Buddy local learning dataset. "
        "Use this tool whenever the student asks for a practice "
        "question, quiz question, exercise, or wants to practice "
        "Python, English grammar, mathematics, or computer science. "
        "If the student does not specify a level, use beginner. "
        "Do not invent an exercise if this tool returns no result."
    ),
)
async def get_next_exercise(
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

        # ========================================================
        # NORMALIZE INPUT
        # ========================================================

        level = level.lower().strip()
        topic = topic.lower().strip()


        # ========================================================
        # DEFAULT LEVEL
        # ========================================================

        if level not in {
            "beginner",
            "intermediate",
        }:
            level = "beginner"


        # ========================================================
        # TOPIC ALIASES
        # ========================================================

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

        topic = topic_aliases.get(
            topic,
            topic,
        )


        # ========================================================
        # FIND EXERCISE
        # ========================================================

        exercise = find_exercise(
            level=level,
            topic=topic,
        )


        # ========================================================
        # NO RESULT
        # ========================================================

        if exercise is None:

            logger.warning(
                "TOOL RESULT -> no exercise | level=%s | topic=%s",
                level,
                topic,
            )

            return (
                "NO_EXERCISE_FOUND. "
                "There is no suitable exercise in the local "
                "learning dataset for this level and topic. "
                "Do not invent an exercise. "
                "Tell the student that this topic is currently "
                "unavailable and suggest Python, English grammar, "
                "mathematics, or computer science."
            )


        # ========================================================
        # SUCCESS
        # ========================================================

        logger.info(
            "TOOL RESULT -> exercise found | level=%s | topic=%s",
            level,
            topic,
        )

        return (
            "EXERCISE_FOUND. "
            f"Topic: {exercise['topic']}. "
            f"Level: {exercise['level']}. "
            f"Question: {exercise['question']} "
            f"Answer: {exercise['answer']} "
            f"Explanation: {exercise['explanation']} "
            "Source: Bharat Buddy local learning dataset."
        )


    except Exception as error:

        logger.exception(
            "TOOL ERROR -> get_next_exercise failed: %s",
            error,
        )

        return (
            "TOOL_ERROR. "
            "The learning exercise could not be loaded right now. "
            "Tell the student that the exercise service is "
            "temporarily unavailable and ask them to try again."
        )


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

    # ========================================================
    # LOGGING
    # ========================================================

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    logger.info(
        "Bharat Buddy session starting | room=%s",
        ctx.room.name,
    )


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
        # LLM
        # ----------------------------------------------------

        llm=groq.LLM(
            model="llama-3.1-8b-instant",
        ),


        # ----------------------------------------------------
        # TEXT TO SPEECH
        # ----------------------------------------------------

        tts=murf.TTS(
            voice="Anisha",
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
        # TOOL LIMIT
        # ----------------------------------------------------

        max_tool_steps=3,


        # ----------------------------------------------------
        # PREEMPTIVE GENERATION
        # ----------------------------------------------------

        preemptive_generation=True,
    )


    # ========================================================
    # CREATE AGENT DIRECTLY
    # ========================================================
    #
    # IMPORTANT:
    # We intentionally do NOT use:
    #
    #     class Assistant(Agent)
    #
    # This avoids the Agent.__init__() instructions error.
    #
    # The tool is supplied directly through tools=[...].
    # ========================================================

    agent = Agent(
        instructions=SYSTEM_PROMPT,
        tools=[
            get_next_exercise,
        ],
    )


    # ========================================================
    # START SESSION
    # ========================================================

    await session.start(
        agent=agent,
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


    logger.info(
        "Bharat Buddy session started successfully."
    )


    # ========================================================
    # CONNECT TO LIVEKIT ROOM
    # ========================================================

    await ctx.connect()

    logger.info(
        "Bharat Buddy connected to room=%s",
        ctx.room.name,
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    cli.run_app(server)