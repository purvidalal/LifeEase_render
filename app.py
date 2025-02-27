import base64
import threading
import logging
import os
import re
from flask import Flask, render_template, request, jsonify
from stt_service import speech_to_text
from emotion_service import detect_emotion
from internal_query import generate_personalized_response
from personal_info import load_personal_info
from tts_service import text_to_speech
from trigger import setup_triggers
from external_query import handle_external_query
from query_service import detect_query
from medical_query import handle_medical_query
from openai import OpenAI

# **🔹 Set OpenAI API Key**
os.environ["OPENAI_API_KEY"] = "sk-FnkWOsdYrUaPc5t3PVs1zcp0w7ag5lOtn2EsrzULMpT3BlbkFJQaLK6EfGogyhHrSl3qEmgU8mDHHBcubT4s_RaHz0IA"
client = OpenAI()

app = Flask(__name__)

# **🔹 Load Personal Information**
personal_info = load_personal_info()

# **🔹 Global Variables**
latest_location = None
conversation_history = []  # Centralized conversation history
scheduler_started = False  # Ensure scheduler runs only once

# **🔹 Start Triggers in a Separate Thread**
def start_triggers():
    global scheduler_started
    if not scheduler_started and os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        scheduler_started = True
        setup_triggers()

if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':  
    trigger_thread = threading.Thread(target=start_triggers, daemon=True)
    trigger_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

def get_conversation_history():
    return conversation_history[-5:]  # Keep last 5 interactions

@app.route('/process-audio', methods=['POST'])
def process_audio():
    """
    Process the speech-to-text transcript sent from the front-end.
    """
    try:
        data = request.get_json()
        transcript = data.get('transcript', '').strip()

        if not transcript:
            logging.error("Mic input not detected. Please check microphone permissions.")
            return jsonify({"error": "Mic input not detected. Please try again."}), 400

        logging.info(f"Processed transcript: {transcript}")

        # Ensure no None values in conversation history
        for entry in conversation_history:
            if entry["user"] is None:
                entry["user"] = ""
            if entry["bot"] is None:
                entry["bot"] = ""

        # Attach user response to the latest bot message (if the last message was a trigger)
        if conversation_history and conversation_history[-1]["user"] is None:
            conversation_history[-1]["user"] = transcript
        else:
            conversation_history.append({"user": transcript, "bot": None})

        history = get_conversation_history()
        query_type = detect_query(transcript, history).strip("'\"")

        if query_type == 'external':
            response = handle_external_query(transcript, *latest_location, history) if latest_location else "Please enable location access."
        elif query_type == 'internal':
            emotion = detect_emotion(transcript)
            response = generate_personalized_response(f"{transcript} (Emotion detected: {emotion})", personal_info, history)
        elif query_type == 'medical':
            response = handle_medical_query(transcript, history)
        else:
            response = "I'm sorry, I couldn't understand your request."

        conversation_history[-1]["bot"] = response  # Attach AI response to last user message
        conversation_history[:] = conversation_history[-10:]

        audio_data = text_to_speech(response[:500])
        audio_base64 = base64.b64encode(audio_data).decode('utf-8') if audio_data else None

        return jsonify({"response": response, "audio": audio_base64, "history": history})

    except Exception as e:
        logging.error(f"Error processing audio: {e}")
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/process-trigger-response', methods=['POST'])
def process_trigger_response():
    """
    Stores trigger events in conversation history and generates natural responses.
    """
    try:
        data = request.get_json()
        trigger_message = data.get("prompt", "").strip()

        if not trigger_message:
            return jsonify({"response": "I didn't hear anything."}), 400

        # Store the trigger event in the conversation history
        conversation_history.append({"user": None, "bot": trigger_message})  # Store bot message


        # Build conversation context
        messages = [{"role": "system", "content": "You are LifeEase, a friendly AI assistant for elderly care."}]
        for entry in conversation_history:
            if entry["user"]:
                messages.append({"role": "user", "content": entry["user"]})
            if entry["bot"]:
                messages.append({"role": "assistant", "content": entry["bot"]})

        # Ensure no `None` values are sent
        messages = [msg for msg in messages if msg["content"]]

        logging.info(f"GPT-4 Request Messages: {messages}")

        completion = client.chat.completions.create(model="gpt-4", messages=messages)
        gpt_response = completion.choices[0].message.content.strip()

        # Update conversation history with AI response
        conversation_history[-1]["bot"] = gpt_response  # Attach response to the latest trigger

        return jsonify({"response": gpt_response})

    except Exception as e:
        logging.error(f"❌ Error processing trigger response: {e}")
        return jsonify({"error": "An error occurred."}), 500


@app.route('/process-location', methods=['POST'])
def process_location():
    """
    Process the location data sent from the front-end (latitude, longitude).
    """
    try:
        global latest_location
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        latest_location = (latitude, longitude)
        logging.info(f"Received location: Latitude = {latitude}, Longitude = {longitude}")

        return jsonify({
            "status": "Location received",
            "latitude": latitude,
            "longitude": longitude,
        })
    except Exception as e:
        logging.error(f"An error occurred while processing location: {e}")
        return jsonify({"error": "Failed to process location."}), 500

if __name__ == "__main__":
    app.run(debug=True)