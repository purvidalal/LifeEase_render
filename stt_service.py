import requests

def speech_to_text(audio_file):
    url = "https://api.sarvam.ai/speech-to-text"
    payload = {'model': 'saarika:v1', 'language_code': 'hi-IN', 'with_timesteps': 'false'}
    
    with open(audio_file, 'rb') as audio:
        files = [('file', (audio_file, audio, 'audio/wav'))]
        headers = {'api-subscription-key': 'e8aeedfc-f86d-4f4d-995f-3b551545f7be'}
        response = requests.post(url, headers=headers, data=payload, files=files)
        return response.json()['transcript']