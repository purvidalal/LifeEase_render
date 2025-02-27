import os
import json
from openai import OpenAI

# Set API key
os.environ["OPENAI_API_KEY"] = "sk-FnkWOsdYrUaPc5t3PVs1zcp0w7ag5lOtn2EsrzULMpT3BlbkFJQaLK6EfGogyhHrSl3qEmgU8mDHHBcubT4s_RaHz0IA"

# Instantiate the OpenAI client
client = OpenAI()

def generate_personalized_response(user_input, personal_info, history=[]):
    """
    Generate a personalized response while considering previous conversation history.
    """
    # Convert personal info to a JSON string
    personal_info_str = json.dumps(personal_info, ensure_ascii=False)

    # Extract last 3 user-bot interactions for context
    conversation_context = "\n".join([f"User: {entry['user']}\nBot: {entry['bot']}" for entry in history[-3:]]) if history else ""

    # Construct messages for GPT-4
    messages = [
        {"role": "system", "content": (
            "You are a helpful conversational companion for an elderly person. "
            "Use personal details to provide a tailored response. "
            "Do not be monotonous, and you do not have to always give a long answer. "
            "Keep asking questions whenever necessary as you are a conversational companion."
        )},
        {"role": "system", "content": f"Here is some information about the user: {personal_info_str}"},
    ]

    # Add conversation history if available
    if conversation_context:
        messages.append({"role": "system", "content": f"Here is the recent conversation context:\n{conversation_context}"})

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
