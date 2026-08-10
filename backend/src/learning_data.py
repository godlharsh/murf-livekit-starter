# ============================================================
# BHARAT BUDDY - LOCAL LEARNING DATA
# Day 5 - Tools
# ============================================================

EXERCISES = [
    {
        "level": "beginner",
        "topic": "python",
        "question": "What is a variable in Python?",
        "answer": "A variable is a name used to store a value.",
        "explanation": (
            "For example, age equals 19 stores the value 19 "
            "inside the variable age."
        ),
    },

    {
        "level": "beginner",
        "topic": "english grammar",
        "question": (
            "Choose the correct sentence: "
            "She go to school or She goes to school?"
        ),
        "answer": "She goes to school.",
        "explanation": (
            "With she, he, or it, we normally use goes instead of go."
        ),
    },

    {
        "level": "beginner",
        "topic": "mathematics",
        "question": "What is 12 multiplied by 5?",
        "answer": "60.",
        "explanation": (
            "12 multiplied by 5 equals 60."
        ),
    },

    {
        "level": "beginner",
        "topic": "computer science",
        "question": "What does CPU stand for?",
        "answer": "Central Processing Unit.",
        "explanation": (
            "The CPU is the main processor that executes "
            "instructions in a computer."
        ),
    },

    {
        "level": "intermediate",
        "topic": "python",
        "question": (
            "What is the difference between a list and a tuple in Python?"
        ),
        "answer": (
            "A list is mutable, while a tuple is immutable."
        ),
        "explanation": (
            "You can modify the contents of a list after creating it, "
            "but you cannot modify the contents of a tuple."
        ),
    },

    {
        "level": "intermediate",
        "topic": "english grammar",
        "question": (
            "Identify the tense in this sentence: "
            "I have completed my homework."
        ),
        "answer": "Present perfect tense.",
        "explanation": (
            "The structure 'have completed' is an example of "
            "the present perfect tense."
        ),
    },

    {
        "level": "intermediate",
        "topic": "mathematics",
        "question": "What is the square root of 144?",
        "answer": "12.",
        "explanation": (
            "12 multiplied by 12 equals 144."
        ),
    },

    {
        "level": "intermediate",
        "topic": "computer science",
        "question": "What is the purpose of an algorithm?",
        "answer": (
            "An algorithm is a step-by-step procedure used to solve "
            "a problem or perform a task."
        ),
        "explanation": (
            "Algorithms provide a structured sequence of steps "
            "for solving problems."
        ),
    },
]


# ============================================================
# FIND EXERCISE
# ============================================================

def find_exercise(level: str, topic: str):
    """
    Find an exercise from the local Bharat Buddy dataset.

    Returns:
        dict: Matching exercise.
        None: If no suitable exercise exists.
    """

    if not isinstance(level, str) or not isinstance(topic, str):
        return None

    level = level.lower().strip()
    topic = topic.lower().strip()

    # --------------------------------------------------------
    # Normalize common topic names
    # --------------------------------------------------------

    topic_aliases = {
        "math": "mathematics",
        "maths": "mathematics",
        "english": "english grammar",
        "grammar": "english grammar",
        "coding": "python",
        "programming": "python",
        "python programming": "python",
        "cs": "computer science",
        "computer": "computer science",
    }

    topic = topic_aliases.get(topic, topic)

    # --------------------------------------------------------
    # Exact level + exact topic
    # --------------------------------------------------------

    for exercise in EXERCISES:
        if (
            exercise["level"] == level
            and exercise["topic"] == topic
        ):
            return exercise

    # --------------------------------------------------------
    # Partial topic match
    # --------------------------------------------------------

    for exercise in EXERCISES:
        if exercise["level"] != level:
            continue

        exercise_topic = exercise["topic"]

        if (
            topic in exercise_topic
            or exercise_topic in topic
        ):
            return exercise

    # --------------------------------------------------------
    # No result
    # --------------------------------------------------------

    return None