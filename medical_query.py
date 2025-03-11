import os
import logging
import re
from openai import OpenAI

# Set up logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up the OpenAI API key
os.environ["OPENAI_API_KEY"] = "sk-FnkWOsdYrUaPc5t3PVs1zcp0w7ag5lOtn2EsrzULMpT3BlbkFJQaLK6EfGogyhHrSl3qEmgU8mDHHBcubT4s_RaHz0IA"

# Instantiate the OpenAI client
client = OpenAI()

MAX_CHARS = 500  # API input character limit

def handle_medical_query(user_message, history=[]):
    """
    Process medical-related queries using GPT-4, while considering previous interactions.
    Force the final output to only two sentences to keep responses short and step-by-step.
    """
    try:
        # Truncate the input if it exceeds the character limit
        if len(user_message) > MAX_CHARS:
            logging.warning("Input exceeds maximum character limit. Truncating input.")
            user_message = user_message[:MAX_CHARS]

        # Extract last few interactions for context
        conversation_context = "\n".join(
            [f"User: {entry['user']}\nBot: {entry['bot']}" for entry in history[-3:]]
        ) if history else ""

        # Construct messages for GPT-4
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a medical assistant specialized in helping elderly users. "
                    "You must keep your response to two-three short sentences for any medical question. "
                    "Briefly acknowledge the user's concern, then always ask clarifying questions to better understand, but no more than 3 questions and then give suggestions. "
                    "Do not provide more than four sentences under any circumstance. "
                    "If additional professional consultation is needed, mention it clearly, but still remain within two sentences. "
                    "If symptoms were previously mentioned, recall them before answering. "
                    "Always be empathetic and concise."
                )
            }
        ]

        # Include previous conversation history
        if conversation_context:
            messages.append({
                "role": "system",
                "content": f"Previous medical discussion:\n{conversation_context}"
            })

        # Add current medical query
        messages.append({"role": "user", "content": f"Medical Question: {user_message}"})

        # Call GPT-4 for response generation
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=60,   # Keep this small to discourage lengthy responses
            temperature=0.7
        )

        # Extract the raw response
        raw_response = completion.choices[0].message.content.strip()

        # -- POST-PROCESSING: Forcibly truncate to TWO sentences --
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.?!])\s+', raw_response)
        # Take only the first two sentences
        truncated_sentences = sentences[:2]
        # Rejoin them
        medical_answer = " ".join(truncated_sentences).strip()

        logging.info("Medical query processed successfully.")
        return medical_answer

    except Exception as e:
        logging.error(f"An error occurred while processing the query: {e}")
        return (
            "I'm sorry, I couldn't process your request. "
            "Please try again or consult a healthcare professional."
        )