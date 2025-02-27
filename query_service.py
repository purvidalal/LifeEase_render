import os
os.environ["OPENAI_API_KEY"] = "sk-FnkWOsdYrUaPc5t3PVs1zcp0w7ag5lOtn2EsrzULMpT3BlbkFJQaLK6EfGogyhHrSl3qEmgU8mDHHBcubT4s_RaHz0IA"
from openai import OpenAI
 
# Instantiate the OpenAI client
client = OpenAI()

def detect_query(user_message, history=[]):
    """
    Classify the user's input as 'internal', 'external', or 'medical', considering past interactions.
    """
    # Use last 3 user inputs for context
    conversation_context = " ".join([entry["user"] for entry in history[-3:]]) if history else ""

    # Send a request to GPT-4 for query detection
    completion = client.chat.completions.create(
        model="gpt-4",  # Use "gpt-4-turbo" if preferred for cost efficiency
        messages=[
            {"role": "system", "content": (
                "You are a helpful conversational bot for the elderly. "
                "Classify the user's input into one of the following categories: 'internal' (e.g., personal or daily life-related queries),'external' (e.g., queries requiring online information like time, weather, or Google search), or 'medical' (e.g., health-related questions). "
                "Consider the user's conversation history for context. "
                "Respond with only one word: 'internal', 'external', or 'medical'."
            )},
            {"role": "user", "content": f"Previous context: {conversation_context}"},
            {"role": "user", "content": f"Query: {user_message}"}
        ]
    )

    # Access the response content and return the classification
    query_type = completion.choices[0].message.content.strip().lower()
    query_type = query_type.strip("'\"")
    return query_type
