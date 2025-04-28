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
TIR_API_KEY = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJGSjg2R2NGM2pUYk5MT2NvNE52WmtVQ0lVbWZZQ3FvcXRPUWVNZmJoTmxFIn0.eyJleHAiOjE3NzY0MTQ0MDYsImlhdCI6MTc0NDg3ODQwNiwianRpIjoiMjA3NjAyMTctNmY3NC00NWJmLTliMDMtN2UzMTNmZTRhMDU4IiwiaXNzIjoiaHR0cDovL2dhdGV3YXkuZTJlbmV0d29ya3MuY29tL2F1dGgvcmVhbG1zL2FwaW1hbiIsImF1ZCI6ImFjY291bnQiLCJzdWIiOiJmZTk1YTdlMy1mYTIzLTRmYjgtYjkzMy00NWUwNGVkMGRjYjAiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJhcGltYW51aSIsInNlc3Npb25fc3RhdGUiOiI4OTIzZmYyNS1kMmRhLTQ3N2ItODI2YS0xNjVhZGJmZDMzMDYiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbIiJdLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImFwaXVzZXIiLCJkZWZhdWx0LXJvbGVzLWFwaW1hbiJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoicHJvZmlsZSBlbWFpbCIsInNpZCI6Ijg5MjNmZjI1LWQyZGEtNDc3Yi04MjZhLTE2NWFkYmZkMzMwNiIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwibmFtZSI6IlB1cnZpIERhbGFsIiwicHJpbWFyeV9lbWFpbCI6InN3YW1pQGJvYWllbnQuY29tIiwiaXNfcHJpbWFyeV9jb250YWN0IjpmYWxzZSwicHJlZmVycmVkX3VzZXJuYW1lIjoicHVydmkuZGFsYWxAYm9haWVudC5jb20iLCJnaXZlbl9uYW1lIjoiUHVydmkiLCJmYW1pbHlfbmFtZSI6IkRhbGFsIiwiZW1haWwiOiJwdXJ2aS5kYWxhbEBib2FpZW50LmNvbSIsImlzX2luZGlhYWlfdXNlciI6ZmFsc2V9.kVFGHjoq3LLo-mvEar25jejsrWZHa9RDt9FA9LvuIiIT6DpRjPrfdQh2CyuvXa3fGaelnDU3xYUiDpEjLZQb7CpWdXSNs2UF6pp26l-CApHiG8ty-ksYpYOtal_jp5tWrQNZg-aGNdqjRAhLmqOk5wjlEuyGMX0P4D9UfCZedVI"
TIR_BASE_URL = "https://infer.e2enetworks.net/project/p-5263/endpoint/is-4799/v1/"
TIR_MODEL_NAME = "peft-model"

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