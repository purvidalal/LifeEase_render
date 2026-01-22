import os
import logging
import re
from openai import OpenAI

# ----------------------------------------------------------------------
# Setup logging
# ----------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ----------------------------------------------------------------------
# TIR API Setup
# ----------------------------------------------------------------------
# You can edit your token, URL, and model here
TIR_API_KEY = 
TIR_BASE_URL = 
TIR_MODEL_NAME = 

# Connect to TIR
client = OpenAI(
    base_url=TIR_BASE_URL,
    api_key=TIR_API_KEY
)

MAX_CHARS = 500

# ----------------------------------------------------------------------
# Medical Query Handler
# ----------------------------------------------------------------------
def handle_medical_query(user_message, history=[]):
    """
    Handle elderly-friendly medical queries using fine-tuned LLaMA model hosted on TIR.
    Provides very short, empathetic responses (2-3 sentences).
    """
    try:
        if len(user_message) > MAX_CHARS:
            logging.warning("Input exceeds max length. Truncating.")
            user_message = user_message[:MAX_CHARS]

        # Prepare conversation history if exists
        conversation_context = "\n".join(
            [f"User: {entry['user']}\nBot: {entry['bot']}" for entry in history[-3:]]
        ) if history else ""

        # System prompt for elderly medical assistance
        system_prompt = (
            "You are a medical assistant specialized in helping elderly users. "
            "Keep your answer very short (2-3 sentences maximum). "
            "First acknowledge the concern, then gently suggest actions. "
            "If medication is discussed, first ask if they took anything before. "
            "Always be simple, supportive, and avoid medical jargon."
        )

        # Construct messages
        messages = [{"role": "system", "content": system_prompt}]

        if conversation_context:
            messages.append({"role": "system", "content": f"Previous conversation:\n{conversation_context}"})

        messages.append({"role": "user", "content": f"Medical Question: {user_message}"})

        # API call with streaming
        streamer = client.chat.completions.create(
            model=TIR_MODEL_NAME,
            messages=messages,
            max_tokens=60,
            temperature=0.7,
            stream=True
        )

        # Reconstruct full streamed response
        full_response = ""
        for chunk in streamer:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content

        raw_response = full_response.strip()

        # Take only first two sentences
        sentences = re.split(r'(?<=[.?!])\s+', raw_response)
        medical_answer = " ".join(sentences[:2]).strip()

        logging.info("Medical query processed successfully.")
        return medical_answer

    except Exception as e:
        logging.error(f"Error handling medical query: {e}")
        return (
            "I'm sorry, I couldn't process your request. "
            "Please try again or consult a healthcare professional."
        )
