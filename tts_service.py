import requests
import base64
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def text_to_speech(text, speaker="meera"):
    """
    Convert text to speech using the Sarvam.ai API.
    """
    url = "https://api.sarvam.ai/text-to-speech"
    payload = {
        "inputs": [text], 
        "target_language_code": "hi-IN",
        "speaker": speaker,
        "speech_sample_rate": 8000,
        "enable_preprocessing": True,
        "model": "bulbul:v1"
    }
    headers = {'api-subscription-key': 'e8aeedfc-f86d-4f4d-995f-3b551545f7be'}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            audio_base64 = response.json()["audios"][0]  
            audio_data = base64.b64decode(audio_base64)
            logging.info("Text-to-speech conversion successful.")
            return audio_data
        else:
            logging.error(f"TTS API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logging.error(f"An error occurred during text-to-speech conversion: {e}")
        return None