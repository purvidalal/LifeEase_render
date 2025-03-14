import requests
import re
from datetime import datetime, timedelta
import pytz
import os
os.environ["OPENAI_API_KEY"] = "sk-FnkWOsdYrUaPc5t3PVs1zcp0w7ag5lOtn2EsrzULMpT3BlbkFJQaLK6EfGogyhHrSl3qEmgU8mDHHBcubT4s_RaHz0IA"
from openai import OpenAI

# Instantiate the OpenAI client
client = OpenAI()

# API Keys and Configurations
GOOGLE_API_KEY = 'AIzaSyD-3fOpAz4oO01d27GUuomrjqEAifbCYDU'  # Replace with your Google API key
GOOGLE_CX = '71a4cf86046244947'  # Replace with your Custom Search Engine ID

# Function to detect language of the query (Hindi if any Devanagari character is found; otherwise English)
def detect_language(query):
    if re.search('[\u0900-\u097F]', query):
        return "hi"
    else:
        return "en"

# Function to classify the query using GPT-4
def classify_query_with_gpt(query):
    try:
        # Modify the system message to include location extraction with a strict format
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[ 
                {
                    "role": "system", 
                    "content": (
                        "Please classify the following Hindi/English query into one of these categories: time, weather, general knowledge. "
                        "Additionally, if there is a location mentioned in the query, return the name of the location. If no location is mentioned, return 'None'. "
                        "The response should strictly follow the format: '<classification>: <location>'. For example: 'time: Delhi'. Return the location in English"
                    )
                },
                {"role": "user", "content": f"Query: {query}"}
            ],
        )

        # Extract GPT-4's response
        response_content = completion.choices[0].message.content.strip() if completion.choices else None
        if not response_content:
            print("Error: GPT-4 response content is empty or None.")
            return {"error": "Failed to classify query: No valid response from GPT-4."}

        # GPT-4 response should be in the format: "<classification>: <location>"
        classification, location = None, None

        # Try to split the response and extract classification and location
        parts = response_content.split(':')
        
        if len(parts) == 2:
            classification = parts[0].strip().lower()
            location = parts[1].strip()
        
        # Check if classification is valid
        if classification not in ['time', 'weather', 'general knowledge']:
            print(f"Unrecognized classification: {classification}. Attempting keyword extraction.")
            time_keywords = ['समय', 'वर्तमान समय', 'अब क्या समय है', 'अभी क्या समय हो रहा है', 'टाइम', 'कितना समय हुआ', 'क्या टाइम हो रहा है', 'अब कितना समय हुआ', 'घड़ी का समय', 'अभी घड़ी क्या कहती है']
            weather_keywords = ['मौसम', 'तापमान', 'मौसमी जानकारी', 'मौसम का हाल', 'बारिश', 'बर्फबारी', 'ठंडा है', 'गरम है', 'आज का मौसम', 'कितनी ठंड है', 'कितनी गर्मी है']
            general_knowledge_keywords = ['सामान्य ज्ञान', 'जानकारी', 'तथ्य', 'क्या है', 'कौन है', 'कैसे है', 'सामान्य जानकारी', 'पूछताछ', 'क्या है यह', 'किसके बारे में']

            # Check for time-related keywords
            if any(keyword in query for keyword in time_keywords):
                classification = 'time'
            # Check for weather-related keywords
            elif any(keyword in query for keyword in weather_keywords):
                classification = 'weather'
            # Otherwise, assume general knowledge
            elif any(keyword in query for keyword in general_knowledge_keywords):
                classification = 'general knowledge'
        
        # If no location is extracted by GPT-4, set it to 'None'
        if not location or location == '':
            location = 'None'

        # Return classification and location
        return {"classification": classification, "location": location}

    except Exception as e:
        print(f"Error during GPT-4 classification: {e}")
        return {"error": "Failed to classify query with GPT-4."}

# Function to get current time for a location
def get_time(location, timezone, lang="hi"):
    """
    Fetches the current time in a given timezone and formats it.
    Converts 24-hour time to 12-hour format and separates hours and minutes.
    """
    if location is None:
        location = "आपके स्थान"  # Default name if location is not explicitly set
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        # Extract time components
        hours_24 = now.strftime('%H')  # 24-hour format
        minutes = now.strftime('%M')  # Minutes
        seconds = now.strftime('%S')  # Optional: Seconds if needed

        # Convert to 12-hour format
        hours_12 = now.strftime('%I')  # 12-hour format
        am_pm = now.strftime('%p')    # AM/PM

        # Debugging output
        print(f"Time for timezone '{timezone}': {hours_24}:{minutes}:{seconds} ({hours_12} {am_pm})")

        # Return formatted time based on language
        if lang == "en":
            return f"The current time in {location} is {hours_12}:{minutes} {am_pm}."
        else:
            return f"{location} का वर्तमान समय {hours_12}:{minutes} {am_pm} है।"
    
    except Exception as e:
        print("Error fetching time:", e)
        if lang == "en":
            return "There was a problem fetching the time. Please try again."
        else:
            return "समय का पता लगाने में समस्या हुई। कृपया पुनः प्रयास करें।"

# Function to get weather details
def get_weather(location_name, country_hint="India", lang="hi"):
    """
    Fetches current weather information for a given location using WeatherAPI and ensures accuracy by specifying a country.
    
    Args:
        location_name (str): The name of the location (e.g., "Delhi").
        country_hint (str): The country to narrow down the search (default: "India").
    
    Returns:
        str: A formatted weather report in Hindi or English or an error message.
    """
    api_key = "7107fce10c2049fd808171110242511"
    base_url = "http://api.weatherapi.com/v1/current.json"
    
    # Combine location name with country hint for better accuracy
    full_location = f"{location_name}, {country_hint}"
    
    # API request parameters
    params = {
        "key": api_key,
        "q": full_location,
        "aqi": "no"  # Disable air quality information for simplicity
    }
    
    try:
        # Make the API call
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Extract relevant weather information
        location = data["location"]["name"]
        country = data["location"]["country"]
        temp_c = data["current"]["temp_c"]
        feels_like_c = data["current"]["feelslike_c"]
        condition = data["current"]["condition"]["text"]
        humidity = data["current"]["humidity"]
        wind_kph = data["current"]["wind_kph"]
        
        if lang == "hi":
            # Translate weather condition to Hindi (simple mapping for demo)
            condition_hindi = {
                "Clear": "स्पष्ट",
                "Partly cloudy": "आंशिक रूप से बादल",
                "Cloudy": "बादल",
                "Rain": "बारिश",
                "Thunderstorm": "आंधी",
                "Snow": "बर्फ",
                "Sunny": "धूप"
            }.get(condition, condition)  # Default to English if not found
            
            # Format the response in Hindi
            weather_report = (
                f"{location}, {country} का वर्तमान मौसम {condition_hindi} है। "
                f"तापमान {temp_c}°C है, जो {feels_like_c}°C जैसा महसूस होता है। "
                f"Humidity {humidity}% है और हवा की गति {wind_kph} kilometer per hour है।"
            )
        else:
            # Format the response in English
            weather_report = (
                f"The current weather in {location}, {country} is {condition}. "
                f"The temperature is {temp_c}°C, which feels like {feels_like_c}°C. "
                f"Humidity is {humidity}% and the wind speed is {wind_kph} km/h."
            )
        return weather_report
    
    except requests.exceptions.RequestException as e:
        if lang == "en":
            return "Sorry, there was an error fetching the weather information."
        else:
            return "क्षमा करें, मौसम की जानकारी प्राप्त करने में त्रुटि हुई।"
    except KeyError:
        if lang == "en":
            return "Sorry, unable to retrieve weather details for the location. Please check the location."
        else:
            return "क्षमा करें, स्थान का मौसम विवरण प्राप्त करने में असमर्थ। कृपया स्थान की जाँच करें।"

# Function to query Google Custom Search API for general knowledge questions
def handle_general_knowledge_query(query, lang="hi"):
    url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'key': GOOGLE_API_KEY,
        'cx': GOOGLE_CX,
        'q': query,
        'hl': lang,  # Set the language for the search
    }
    try:
        response = requests.get(url, params=params)
        search_results = response.json()
        if 'items' in search_results:
            # Aggregate snippets from the top 3 results for a more robust context
            snippets = [item.get('snippet', '') for item in search_results['items'][:3]]
            combined_snippets = " ".join(snippets)
            
            # Use GPT-4 to refine the combined answer based on the query context
            refined_answer = refine_answer_with_gpt(combined_snippets, query, lang)
            return refined_answer
        else:
            return "No results found." if lang == "en" else "कोई परिणाम नहीं मिला।"
    except Exception as e:
        return "There was a problem with the Google search service." if lang == "en" else "Google खोज सेवा में समस्या है।"

def refine_answer_with_gpt(snippet_text, query, lang="hi"):
    """
    Uses GPT-4 to refine and summarize the provided snippet text into a coherent answer.
    """
    try:
        # Create a prompt that includes both the snippet and the original query for context.
        # Adjust the instructions based on the language.
        if lang == "en":
            prompt = (
                f"Given the following information from various sources:\n\"{snippet_text}\"\n\n"
                f"Provide a clear, concise, and well-organized answer to the question: \"{query}\""
            )
        else:
            prompt = (
                f"निम्नलिखित स्रोतों से प्राप्त जानकारी के आधार पर:\n\"{snippet_text}\"\n\n"
                f"कृपया प्रश्न \"{query}\" का स्पष्ट, संक्षिप्त, और सुव्यवस्थित उत्तर दें।"
            )
        # Call GPT-4 (using your existing client) to get a refined answer.
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a knowledgeable assistant that provides precise and concise answers."},
                {"role": "user", "content": prompt}
            ],
        )
        refined_response = completion.choices[0].message.content.strip() if completion.choices else snippet_text
        return refined_response

    except Exception as e:
        # If GPT-4 call fails, return the original snippet with a note.
        fallback_note = " Please verify with reliable sources." if lang == "en" else " कृपया विश्वसनीय स्रोतों से पुष्टि करें।"
        return snippet_text + fallback_note

# Unified query handler
def handle_external_query(query, lat, lng, history=[]):
    """
    Handles external queries by processing the classification and location information.
    
    Parameters:
    - query: User's query string.
    - lat: Latitude of the client device (if available).
    - lng: Longitude of the client device (if available).
    
    Returns:
    - A response string or error message.
    """
    # Detect language based on the query
    lang = detect_language(query)
    
    # Classify query and extract location using GPT-4
    classification_response = classify_query_with_gpt(query)
    print("GPT-4 Response:", classification_response)
    if isinstance(classification_response, dict) and "error" in classification_response:
        return classification_response["error"]

    try:
        # Extract classification and location
        classification = classification_response.get('classification', None)
        gpt_location = classification_response.get('location', None)
        # Determine the final location to use
        if gpt_location != 'None':
            # Use GPT-4's extracted location
            location_name = gpt_location
            location_coords = get_coordinates_from_name(gpt_location)  # Custom function to fetch coordinates
        elif lat != 'None' and lng != 'None':
            # Use client device location if available
            location_name = get_city_from_coordinates(lat, lng)  # Default label for client device's location
            location_coords = (lat, lng)
        else:
            # Default fallback if no location is provided
            location_name = "Pune"
            location_coords = None

        # Handle 'time' classification
        if classification == 'time':  # Ensure strict equality
            # Fetch timezone using location coordinates if available
            if location_coords is not None:
                timezone = get_timezone_from_lat_lng(*location_coords)
            else:
                print("Location coordinates not found; using default timezone.")
                timezone = "Asia/Kolkata"  # Default timezone fallback

            return get_time(location_name, timezone, lang)

        # Handle 'weather' classification
        elif "weather" in classification:
            return get_weather(location_name, lang=lang)

        # Handle 'general knowledge' classification
        elif "general knowledge" in classification:
            return handle_general_knowledge_query(query, lang)

        # If classification doesn't match any expected type
        else:
            if lang == "en":
                return "Query not understood. Please ask more clearly."
            else:
                return "प्रश्न समझ में नहीं आया। कृपया और स्पष्ट रूप से पूछें।"

    except Exception as e:
        print(f"Error during external query handling: {e}")
        if lang == "en":
            return "There was a problem providing the answer."
        else:
            return "प्रश्न का उत्तर देने में समस्या हुई।"

def clean_snippet(snippet):
    snippet = re.sub(r'\d{1,2} \w+ \d{4}', '', snippet)
    snippet = re.sub(r'http[s]?://\S+', '', snippet)
    snippet = re.sub(r'\|.*$', '', snippet)
    return snippet.strip()

def refine_answer(snippet, lang="hi"):
    if len(snippet.split()) < 5:
        if lang == "en":
            snippet += " Please check the related sources for more information."
        else:
            snippet += " कृपया अधिक जानकारी के लिए संबंधित स्रोतों से जांच करें।"
    return snippet

# Function to get timezone from latitude and longitude
def get_timezone_from_lat_lng(lat, lng):
    try:
        url = f"https://maps.googleapis.com/maps/api/timezone/json?location={lat},{lng}&timestamp={int(datetime.now().timestamp())}&key={GOOGLE_API_KEY}"
        response = requests.get(url)
        timezone_data = response.json()
        if timezone_data['status'] == 'OK':
            print(f"Timezone fetched: {timezone_data['timeZoneId']}")  # Debug statement
            return timezone_data['timeZoneId']
        else:
            print("Timezone fetch failed with status:", timezone_data['status'])  # Debug statement
            return "Asia/Kolkata"
    except Exception as e:
        print("Error fetching timezone:", e)
        return "Asia/Kolkata"

def get_coordinates_from_name(location_name):
    """
    Fetch coordinates (latitude, longitude) from a location name using Google Maps Geocoding API.
    """
    try:
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {
            'address': location_name,
            'key': GOOGLE_API_KEY
        }
        print(f"Requesting geocoding for: {location_name}")
        print(f"URL: {url}")
        print(f"Params: {params}")
        
        response = requests.get(url, params=params)
        data = response.json()
        print("Geocoding API response:", data)  # Debug print to inspect full response
        
        if data.get('status') == 'OK' and data.get('results'):
            latitude = data['results'][0]['geometry']['location']['lat']
            longitude = data['results'][0]['geometry']['location']['lng']
            return latitude, longitude
        else:
            print("Error: Location not found. Status:", data.get('status'))
            if 'error_message' in data:
                print("Error message:", data['error_message'])
            return None
    except Exception as e:
        print(f"Error during geocoding: {e}")
        return None

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

def get_city_from_coordinates(lat, lon):
    """
    Fetch the city name based on latitude and longitude using Geopy's Nominatim service.
    Handles common geocoding errors gracefully.
    """
    try:
        # Use a valid user agent to prevent 403 errors
        geolocator = Nominatim(user_agent="your_email_or_app_name")
        location = geolocator.reverse((lat, lon), language='en')

        if location:
            # Extract address components
            address = location.raw.get('address', {})
            return address.get('city', "City not found")
        return "City not found"
    
    except GeocoderTimedOut:
        print("Geocoder timed out. Retrying...")
        return "Geocoding service timed out. Please try again later."
    
    except GeocoderUnavailable:
        print("Geocoding service is unavailable.")
        return "Geocoding service unavailable."
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "An unexpected error occurred during geocoding."