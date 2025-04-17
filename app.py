import base64
import logging
import os
import json
import PyPDF2
from flask import Flask, render_template, request, jsonify, Response
from stt_service import speech_to_text
from emotion_service import detect_emotion
from internal_query import generate_personalized_response
from personal_info import load_personal_info
from tts_service import text_to_speech
from external_query import handle_external_query
from query_service import detect_query
from medical_query import handle_medical_query
from openai import OpenAI

# Set OpenAI API Key
os.environ["OPENAI_API_KEY"] = "sk-FnkWOsdYrUaPc5t3PVs1zcp0w7ag5lOtn2EsrzULMpT3BlbkFJQaLK6EfGogyhHrSl3qEmgU8mDHHBcubT4s_RaHz0IA"
client = OpenAI()

app = Flask(__name__)
personal_info = load_personal_info()
latest_location = None
conversation_history = []
uploaded_pdf_context = None  # store last uploaded PDF text

def extract_text_from_pdf(path):
    try:
        text = ""
        with open(path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return ""

@app.route('/')
def index():
    return render_template('index.html')

def get_conversation_history():
    return conversation_history[-5:]

@app.route('/process-audio', methods=['POST'])
def process_audio():
    try:
        data = request.get_json()
        transcript = data.get('transcript', '').strip()

        if not transcript:
            return jsonify({"error": "Mic input not detected. Please try again."}), 400

        conversation_history.append({"user": transcript, "bot": None})
        history = get_conversation_history()
        query_type = detect_query(transcript, history).strip("'\"")

        if any(word in transcript.lower() for word in ['document', 'file', 'upload', 'pdf']):
            global uploaded_pdf_context
            if uploaded_pdf_context:
                prompt = f"""You are a medical assistant. Based on the document below, answer the user's question.\n\nDocument:\n{uploaded_pdf_context[:12000]}\n\nQuestion:\n{transcript}"""
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                response = completion.choices[0].message.content.strip()
            else:
                response = "Please upload a document first."
        elif query_type == 'external':
            response = handle_external_query(transcript, *latest_location, history) if latest_location else "Please enable location access."
        elif query_type == 'internal':
            emotion = detect_emotion(transcript)
            response = generate_personalized_response(f"{transcript} (Emotion detected: {emotion})", personal_info, history)
        elif query_type == 'medical':
            response = handle_medical_query(transcript, history)
        else:
            response = "I'm sorry, I couldn't understand your request."

        conversation_history[-1]["bot"] = response
        conversation_history[:] = conversation_history[-10:]

        audio_data = text_to_speech(response[:500])
        audio_base64 = base64.b64encode(audio_data).decode('utf-8') if audio_data else None

        return jsonify({"response": response, "audio": audio_base64, "history": history})

    except Exception as e:
        logging.error(f"Error processing audio: {e}")
        return jsonify({"error": "An internal error occurred."}), 500

@app.route('/process-location', methods=['POST'])
def process_location():
    try:
        global latest_location
        data = request.get_json()
        latest_location = (data.get('latitude'), data.get('longitude'))
        logging.info(f"Received location: {latest_location}")
        return jsonify({"status": "Location received", "latitude": latest_location[0], "longitude": latest_location[1]})
    except Exception as e:
        return jsonify({"error": "Failed to process location."}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400

        upload_folder = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        save_path = os.path.join(upload_folder, file.filename)
        file.save(save_path)

        global uploaded_pdf_context
        uploaded_pdf_context = extract_text_from_pdf(save_path)
        if not uploaded_pdf_context.strip():
            return jsonify({"error": "Could not extract text from PDF."}), 400

        return jsonify({"message": "File uploaded and document context stored.", "filename": file.filename})

    except Exception as e:
        logging.error(f"Upload error: {e}")
        return jsonify({"error": "Failed to upload file"}), 500

@app.route('/upload-image', methods=['POST'])
def upload_image():
    try:
        image_file = request.files.get('image')
        prompt = request.form.get('prompt', '')

        if not image_file or image_file.filename == '':
            return jsonify({"error": "No image file provided."}), 400

        # Convert image to base64
        image_bytes = image_file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        llama_client = OpenAI(
            base_url="https://infer.e2enetworks.net/project/p-5263/genai/llama_3_2_11b_vision_instruct/v1",
            api_key="f53d8d5f-6a96-45db-90e1-053dae14a012"
        )

        response = llama_client.chat.completions.create(
            model="llama_3_2_11b_vision_instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt or "Describe this image."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ],
            temperature=0.5,
            stream=False
        )

        if response and response.choices:
            result = response.choices[0].message.content
        else:
            result = "No response from LLaMA Vision."

        return jsonify({"response": result})

    except Exception as e:
        logging.error(f"Image processing error: {e}")
        return jsonify({"error": "Failed to process image."}), 500

@app.route('/qa', methods=['POST'])
def qa_from_uploaded_file():
    try:
        data = request.get_json()
        question = data.get('question', '').strip()

        global uploaded_pdf_context
        if not uploaded_pdf_context:
            return jsonify({"response": "Please upload a PDF document first."}), 400

        prompt = f"""You are a medical assistant. Based on the document below, answer the user's question.\n\nDocument:\n{uploaded_pdf_context[:12000]}\n\nQuestion:\n{question}"""

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = completion.choices[0].message.content.strip()

        audio_data = text_to_speech(answer[:500])
        audio_base64 = base64.b64encode(audio_data).decode('utf-8') if audio_data else None

        return jsonify({"response": answer, "audio": audio_base64})

    except Exception as e:
        logging.error(f"Error in /qa: {e}")
        return jsonify({"response": "Something went wrong answering your question."}), 500

# Basic Auth
USERNAME = "Boaient"
PASSWORD = "V@r#s*j$@2024"

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response('Access denied.\n', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

@app.before_request
def require_authentication():
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)