import os
os.environ["OPENAI_API_KEY"] = "sk-FnkWOsdYrUaPc5t3PVs1zcp0w7ag5lOtn2EsrzULMpT3BlbkFJQaLK6EfGogyhHrSl3qEmgU8mDHHBcubT4s_RaHz0IA"
from openai import OpenAI
 
# Instantiate the OpenAI client
client = OpenAI()
 
def detect_emotion(sentence):
    # Send a request to GPT-4 for emotion detection
    completion = client.chat.completions.create(
        model="gpt-4",  # You can use "gpt-4-turbo" if you prefer
        messages=[
            {"role": "system", "content": "You are a Hindi/English emotion classifier. Classify the emotion as Happy, Calm, Sad, Celebration Preparation, discomfort or other relevant emotions."},
            {"role": "user", "content": f"Sentence: {sentence}"}
        ]
    )
    # Access the response content
    # Changed from completion.choices[0].message["content"] to completion.choices[0].message.content
    emotion = completion.choices[0].message.content.strip()
    return emotion