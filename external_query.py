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
from datetime import datetime
import pytz

def get_time(location, timezone):
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

        # Return formatted time
        return f"{location} का वर्तमान समय {hours_12}:{minutes} {am_pm} है।"
    
    except Exception as e:
        print("Error fetching time:", e)
        return "समय का पता लगाने में समस्या हुई। कृपया पुनः प्रयास करें।"

# Function to get weather details
def get_weather(location_name, country_hint="India"):
    """
    Fetches current weather information for a given location using WeatherAPI and ensures accuracy by specifying a country.
    
    Args:
        location_name (str): The name of the location (e.g., "Delhi").
        country_hint (str): The country to narrow down the search (default: "India").
    
    Returns:
        str: A formatted weather report in Hindi or an error message.
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
        return weather_report
    
    except requests.exceptions.RequestException as e:
        return "क्षमा करें, मौसम की जानकारी प्राप्त करने में त्रुटि हुई।"
    except KeyError:
        return "क्षमा करें, स्थान का मौसम विवरण प्राप्त करने में असमर्थ। कृपया स्थान की जाँच करें।"

# Function to query Google Custom Search API for general knowledge questions
def handle_general_knowledge_query(query):
    url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'key': GOOGLE_API_KEY,
        'cx': GOOGLE_CX,
        'q': query,
        'hl': 'hi',  # Hindi results
    }
    try:
        response = requests.get(url, params=params)
        search_results = response.json()
        if 'items' in search_results:
            snippet = search_results['items'][0].get('snippet', 'No answer found.')
            cleaned_snippet = clean_snippet(snippet)
            return refine_answer(cleaned_snippet)
        return "कोई परिणाम नहीं मिला।"
    except Exception as e:
        return "Google खोज सेवा में समस्या है।"

def refine_answer(snippet):
    if len(snippet.split()) < 5:
        snippet += " कृपया अधिक जानकारी के लिए संबंधित स्रोतों से जांच करें।"
    return snippet

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
        if gpt_location !='None':
            # Use GPT-4's extracted location
            location_name = gpt_location
            location_coords = get_coordinates_from_name(gpt_location)  # Custom function to fetch coordinates
        elif lat!='None' and lng!='None':
            # Use client device location if available
            location_name = get_city_from_coordinates(lat, lng)  # Default label for client device's location
            location_coords = (lat,lng)
        else:
            # Default fallback if no location is provided
            location_name = "Pune"
            location_coords = None

        # Handle 'time' classification
        if classification == 'time':  # Ensure strict equality
            timezone = None

    # Fetch timezone using location coordinates if available
            if location_coords != "None":
                timezone = get_timezone_from_lat_lng(*location_coords)
            if not timezone:
                print("Timezone not found; using default.")  # Debugging
                timezone = "Asia/Kolkata"  # Default timezone fallback

            return get_time(location_name, timezone)

        # Handle 'weather' classification
        elif "weather" in classification:
            return get_weather(location_name)

        # Handle 'general knowledge' classification
        elif "general knowledge" in classification:
            return handle_general_knowledge_query(query)

        # If classification doesn't match any expected type
        else:
            return "प्रश्न समझ में नहीं आया। कृपया और स्पष्ट रूप से पूछें।"

    except Exception as e:
        print(f"Error during external query handling: {e}")
        return "प्रश्न का उत्तर देने में समस्या हुई।"

def clean_snippet(snippet):
    snippet = re.sub(r'\d{1,2} \w+ \d{4}', '', snippet)
    snippet = re.sub(r'http[s]?://\S+', '', snippet)
    snippet = re.sub(r'\|.*$', '', snippet)
    return snippet.strip()

def refine_answer(snippet):
    if len(snippet.split()) < 5:
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
        url = f'https://maps.googleapis.com/maps/api/geocode/json'
        params = {
            'address': location_name,
            'key': GOOGLE_API_KEY
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['status'] == 'OK' and 'results' in data:
            latitude = data['results'][0]['geometry']['location']['lat']
            longitude = data['results'][0]['geometry']['location']['lng']
            return latitude, longitude
        else:
            print("Error: Location not found.")
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