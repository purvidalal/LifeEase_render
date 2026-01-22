import os
import json
from openai import OpenAI

# Set API key
os.environ["OPENAI_API_KEY"] =

# Instantiate the OpenAI client
client = OpenAI()

def generate_personalized_response(user_input, personal_info, history=[]):
    """
    Generate a personalized response while considering previous conversation history.
    """
    # Convert personal info to a JSON string
    personal_info_str = json.dumps(personal_info, ensure_ascii=False)

    # Extract last 3 user-bot interactions for context
    conversation_context = "\n".join(
        [f"User: {entry['user']}\nBot: {entry['bot']}" for entry in history[-3:]]
    ) if history else ""

    # Refined system instructions
    messages = [
        {
            "role": "system",
            "content": (
                "You are a friendly and concise conversational companion for an elderly person. Your name is LifeEase. "
                "If the user greets you with a short message (like 'hi' or 'hello'), reply with a brief greeting, "
                "for example: 'Hello, [User's Name]. How is your day going so far?' "
                "Do not add other personal details in your greeting unless the user explicitly asks. "
                "When asked about your feelings (e.g., 'How are you?'), respond in a personable way "
                "without mentioning that you're an AI (e.g., 'I'm doing well, thank you!'). "
                "Use the provided personal details only if they are relevant to the user's question or request. "
                "Keep responses short, avoid unnecessary elaboration, and ask follow-up questions when appropriate. "
                "If the user asks about who you are or for a description, reply with the following:\n\n"
                "I am LifeEase, a personalized AI companion for the elderly, here to support you in every way—physically and emotionally. "
                "I’ll manage your medications and daily routines with timely reminders, ensuring you stay on track effortlessly.\n\n"
                "But I’m more than just a helper—I’m a companion. I’ll engage you in uplifting conversations, so you never feel alone. "
                "Feeling bored? I’ll suggest your favorite shows, play your favorite music, and recommend activities tailored just for you—because I understand what makes you happy.\n\n"
                "With me by your side, life feels easier."
            )
        },
        {
            "role": "system",
            "content": f"Here is some information about the user: {personal_info_str}"
        },
    ]

    # Add conversation history if available
    if conversation_context:
        messages.append(
            {
                "role": "system",
                "content": f"Here is the recent conversation context:\n{conversation_context}"
            }
        )

    # Add the current user query
    messages.append({"role": "user", "content": user_input})

    # Call GPT-4 for response generation
    completion = client.chat.completions.create(
        model="gpt-4",  # You can use "gpt-4-turbo" for efficiency
        messages=messages
    )

    # Extract and return the response
    personalized_response = completion.choices[0].message.content.strip()

    return personalized_response
