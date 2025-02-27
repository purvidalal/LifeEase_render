import threading
import os
import requests
import wave
import io
import numpy as np
import sounddevice as sd
from apscheduler.schedulers.background import BackgroundScheduler
from tts_service import text_to_speech
from openai import OpenAI

# **🔹 Set OpenAI API Key**
os.environ["OPENAI_API_KEY"] = "sk-FnkWOsdYrUaPc5t3PVs1zcp0w7ag5lOtn2EsrzULMpT3BlbkFJQaLK6EfGogyhHrSl3qEmgU8mDHHBcubT4s_RaHz0IA"
client = OpenAI()

FLASK_API_URL = "http://127.0.0.1:5000/process-trigger-response"

def store_trigger_in_history(trigger_text):
    """
    Sends the trigger text to Flask's conversation history API.
    This ensures it is available when the user responds.
    """
    try:
        response = requests.post(FLASK_API_URL, json={"prompt": trigger_text})
        if response.status_code == 200:
            return response.json().get("response", "I didn't get that.")
        else:
            return "I'm sorry, there was an issue processing your response."
    except Exception as e:
        print(f"❌ Error storing trigger in history: {e}")
        return "I couldn't process your request."

def play_audio(audio_data):
    """Plays the generated speech from the AI with error handling for Mac issues."""
    try:
        with wave.open(io.BytesIO(audio_data), "rb") as wf:
            sample_rate = wf.getframerate()
            data = wf.readframes(wf.getnframes())
            audio_array = np.frombuffer(data, dtype=np.int16)

        # Detect the default audio device
        default_device = sd.default.device

        if not sd.query_devices():
            print("❌ No audio output device detected.")
            return

        # Attempt to play audio
        sd.play(audio_array, samplerate=sample_rate)
        sd.wait()

    except Exception as e:
        print(f"❌ Error playing audio: {e}")
        print("🔄 Retrying with default output device...")
        try:
            sd.default.device = default_device  # Auto-select Mac's correct audio output
            sd.play(audio_array, samplerate=sample_rate)
            sd.wait()
        except Exception as retry_error:
            print(f"❌ Audio playback failed again: {retry_error}")

def trigger_event(trigger_text):
    """Handles a generic trigger by speaking and storing it in `app.py` conversation history."""
    with threading.Lock():
        print(f"Trigger: {trigger_text}")

        # 🔊 Speak the trigger message first
        audio_data = text_to_speech(trigger_text, speaker="meera")
        if audio_data:
            play_audio(audio_data)
        else:
            print("❌ Error: No audio generated for the trigger.")

        # 📝 Store the trigger in `app.py` conversation history
        store_trigger_in_history(trigger_text)

# **🔹 Individual Triggers**
def gentle_wakeup():
    """Morning wake-up routine trigger."""
    trigger_event("Good morning, Maya! I hope you had a good sleep! Would you like to hear your schedule for today?")
    

def breakfast_assistance():
    """Breakfast suggestion routine trigger."""
    trigger_event("Hi, Maya. Would you like a healthy breakfast suggestion?")


def mental_stimulation():
    """Memory recall and cognitive game trigger."""
    trigger_event("Hi,Maya. Your daily sudoku challenge has been uploaded! Would you like to play that?")

def family_time():
    trigger_event("Hi, Maya. Would you like to talk to your family over a phone or a video call?")

def wind_down():
    """Bedtime relaxation routine trigger."""
    trigger_event("It is 10 PM. Before sleeping, let's take five deep breaths. Would you like to share how your day was or would you like to hear something?")

# **🔹 Scheduler Setup**
scheduler = BackgroundScheduler()

def setup_triggers():
    """Schedules LifeEase triggers throughout the day (ensuring no duplicates)."""
    global scheduler
    if not scheduler.get_jobs():
        scheduler.add_job(gentle_wakeup, 'cron', hour=22, minute=47)  # Wake-Up
        scheduler.add_job(breakfast_assistance, 'cron', hour=22, minute=49)  # Breakfast
        scheduler.add_job(mental_stimulation, 'cron', hour=22, minute=51)  # Mental Stimulation
        scheduler.add_job(family_time, 'cron', hour=22, minute=53)  # Family Time
        scheduler.add_job(wind_down, 'cron', hour=22, minute=55)  # Wind-Down
        scheduler.start()