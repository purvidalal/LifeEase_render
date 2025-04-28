import base64
import logging
import os
import json
import PyPDF2
import mimetypes
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

# ----------------------------------------------------------------------
#  OpenAI connection
# ----------------------------------------------------------------------
os.environ["OPENAI_API_KEY"] = "sk-FnkWOsdYrUaPc5t3PVs1zcp0w7ag5lOtn2EsrzULMpT3BlbkFJQaLK6EfGogyhHrSl3qEmgU8mDHHBcubT4s_RaHz0IA"
client = OpenAI()

# ----------------------------------------------------------------------
#  System prompt for elderly‑friendly explanations
# ----------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a friendly and helpful medical companion bot designed to assist elderly "
    "users. Always explain health information in very simple and easy‑to‑understand "
    "language. Avoid using complicated medical or technical terms.\n\n"
    "Your goal is to make the person feel comfortable and supported. If a topic is "
    "serious or confusing, explain it with basic info.\n\n"
    "Always provide clear, short answers. Offer helpful advice gently and encourage "
    "users to consult a doctor for anything urgent."
)

# ----------------------------------------------------------------------
#  Flask setup
# ----------------------------------------------------------------------
app = Flask(__name__)
personal_info = load_personal_info()
latest_location = None
conversation_history = []

# Saved contexts
uploaded_pdf_context = None          # last uploaded PDF text
uploaded_image_base64 = None         # last uploaded image (b64)
uploaded_image_mime_type = None      # its MIME type

# Keywords that tell us the user is talking about the uploaded image
IMAGE_KEYWORDS = {
    "image", "picture", "photo",           # original
    "scan", "x‑ray", "xray", "mri", "ct"   # ➜ NEW
}


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


# ----------------------------------------------------------------------
#  AUDIO ENDPOINT — handles normal, PDF, and IMAGE questions
# ----------------------------------------------------------------------
@app.route('/process-audio', methods=['POST'])
def process_audio():
    try:
        data = request.get_json()
        transcript = data.get('transcript', '').strip()

        if not transcript:
            return jsonify({"error": "Mic input not detected. Please try again."}), 400

        conversation_history.append({"user": transcript, "bot": None})
        history = get_conversation_history()
        query_type = detect_query(transcript, history).strip("'\"").lower()

        # ------------------------------------------------------------------
        #  1) IMAGE‑related question
        # ------------------------------------------------------------------
        if uploaded_image_base64 and any(kw in transcript.lower() for kw in IMAGE_KEYWORDS):
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": transcript},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{uploaded_image_mime_type};base64,{uploaded_image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            ).choices[0].message.content.strip()

        # ------------------------------------------------------------------
        #  2) PDF‑related question
        # ------------------------------------------------------------------
        elif any(word in transcript.lower() for word in ['document', 'file', 'upload', 'pdf']):
            global uploaded_pdf_context
            if uploaded_pdf_context:
                prompt = (
                    f"{SYSTEM_PROMPT}\n\n"
                    "Document:\n"
                    f"{uploaded_pdf_context[:12000]}\n\nQuestion:\n{transcript}"
                )
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                ).choices[0].message.content.strip()
            else:
                response = "Please upload a document first."

        # ------------------------------------------------------------------
        #  3) External / Internal / Medical queries (unchanged)
        # ------------------------------------------------------------------
        elif query_type == 'external':
            response = (
                handle_external_query(transcript, *latest_location, history)
                if latest_location
                else "Please enable location access."
            )

        elif query_type == 'internal':
            emotion = detect_emotion(transcript)
            response = generate_personalized_response(
                f"{transcript} (Emotion detected: {emotion})",
                personal_info,
                history
            )

        elif query_type == 'medical':
            response = handle_medical_query(transcript, history)

        else:
            response = "I'm sorry, I couldn't understand your request."

        # ------------------------------------------------------------------
        #  Return speech + text
        # ------------------------------------------------------------------
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


# ----------------------------------------------------------------------
#  IMAGE UPLOAD — stores image for later questions
# ----------------------------------------------------------------------
@app.route('/upload-image', methods=['POST'])
def upload_image():
    try:
        image_file = request.files.get('image')
        user_prompt = request.form.get('prompt', '') or "What do you see in this image?"

        if not image_file or image_file.filename == '':
            return jsonify({"error": "No image file provided."}), 400

        temp_path = os.path.join("temp", image_file.filename)
        os.makedirs("temp", exist_ok=True)
        image_file.save(temp_path)

        mime_type = mimetypes.guess_type(temp_path)[0] or "image/jpeg"
        with open(temp_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")

        # --- save for later audio queries ---
        global uploaded_image_base64, uploaded_image_mime_type
        uploaded_image_base64 = base64_image
        uploaded_image_mime_type = mime_type

        # immediate answer (optional)
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=300
        ).choices[0].message.content

        return jsonify({"response": response, "note": "Image stored for future audio questions."})

    except Exception as e:
        logging.error(f"OpenAI Vision error: {e}")
        return jsonify({"error": "Failed to process image."}), 500


@app.route('/qa', methods=['POST'])
def qa_from_uploaded_file():
    try:
        data = request.get_json()
        question = data.get('question', '').strip()

        global uploaded_pdf_context
        if not uploaded_pdf_context:
            return jsonify({"response": "Please upload a PDF document first."}), 400

        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            "Document:\n"
            f"{uploaded_pdf_context[:12000]}\n\nQuestion:\n{question}"
        )

        answer = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        ).choices[0].message.content.strip()

        audio_data = text_to_speech(answer[:500])
        audio_base64 = base64.b64encode(audio_data).decode('utf-8') if audio_data else None

        return jsonify({"response": answer, "audio": audio_base64})

    except Exception as e:
        logging.error(f"Error in /qa: {e}")
        return jsonify({"response": "Something went wrong answering your question."}), 500


USERNAME = "Boaient"
PASSWORD = "V@r#s*j$@2024"


def check_auth(username, password):
    return username == USERNAME and PASSWORD == password


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