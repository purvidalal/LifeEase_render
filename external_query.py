import requests
import re
from datetime import datetime
import pytz
import os
import certifi
import ssl
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from openai import OpenAI

# Environment Setup
os.environ["OPENAI_API_KEY"] = 

# Instantiate OpenAI client
client = OpenAI()

# API Keys
GOOGLE_API_KEY = 
GOOGLE_CX = 

# Language Detection
def detect_language(query):
    return "hi" if re.search('[\u0900-\u097F]', query) else "en"

# Classify Query with GPT-4
def classify_query_with_gpt(query):
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Classify into time, weather, general knowledge. If user asks outside then also understand it correctly. Extract location if any, else 'None'. Format: '<classification>: <location>'."},
                {"role": "user", "content": f"Query: {query}"}
            ],
        )
        response_content = completion.choices[0].message.content.strip()
        parts = response_content.split(':')
        if len(parts) == 2:
            classification = parts[0].strip().lower()
            location = parts[1].strip()
        else:
            classification, location = None, None
        if not location:
            location = 'None'
        return {"classification": classification, "location": location}
    except Exception as e:
        print(f"Error during GPT-4 classification: {e}")
        return {"error": "Failed to classify query with GPT-4."}

# Time Fetcher
def get_time(location, timezone, lang="hi"):
    if location is None:
        location = "आपके स्थान"
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        hours_12 = now.strftime('%I')
        minutes = now.strftime('%M')
        am_pm = now.strftime('%p')
        return (f"The current time in {location} is {hours_12}:{minutes} {am_pm}." if lang == "en" 
                else f"{location} का वर्तमान समय {hours_12}:{minutes} {am_pm} है।")
    except Exception:
        return "There was a problem fetching the time." if lang == "en" else "समय का पता लगाने में समस्या हुई।"

# Weather Fetcher
def get_weather(location_name, lang="hi"):
    api_key = "7107fce10c2049fd808171110242511"
    base_url = "http://api.weatherapi.com/v1/current.json"
    params = {"key": api_key, "q": location_name, "aqi": "no"}
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        location = data["location"]["name"]
        country = data["location"]["country"]
        temp_c = data["current"]["temp_c"]
        feels_like_c = data["current"]["feelslike_c"]
        condition = data["current"]["condition"]["text"]
        humidity = data["current"]["humidity"]
        wind_kph = data["current"]["wind_kph"]

        if lang == "hi":
            condition_hindi = {"Clear": "स्पष्ट", "Partly cloudy": "आंशिक रूप से बादल", "Cloudy": "बादल", "Rain": "बारिश", "Thunderstorm": "आंधी", "Snow": "बर्फ", "Sunny": "धूप"}.get(condition, condition)
            return f"{location}, {country} का वर्तमान मौसम {condition_hindi} है। तापमान {temp_c}°C है, जो {feels_like_c}°C जैसा महसूस होता है। Humidity {humidity}% है और हवा की गति {wind_kph} किलोमीटर/घंटा है।"
        else:
            return f"The current weather in {location}, {country} is {condition}. The temperature is {temp_c}°C, feels like {feels_like_c}°C. Humidity {humidity}%. Wind speed {wind_kph} km/h."

    except Exception:
        return "Weather information fetch error."

# Google Search API
def handle_general_knowledge_query(query, lang="hi"):
    url = 'https://www.googleapis.com/customsearch/v1'
    params = {'key': GOOGLE_API_KEY, 'cx': GOOGLE_CX, 'q': query, 'hl': lang}
    try:
        response = requests.get(url, params=params)
        search_results = response.json()
        if 'items' in search_results:
            snippets = [item.get('snippet', '') for item in search_results['items'][:3]]
            combined_snippets = " ".join(snippets)
            return refine_answer_with_gpt(combined_snippets, query, lang)
        else:
            return "No results found." if lang == "en" else "कोई परिणाम नहीं मिला।"
    except Exception:
        return "Google search service error."

# Refine with GPT
def refine_answer_with_gpt(snippet_text, query, lang="hi"):
    try:
        prompt = (f"Given info:\n\"{snippet_text}\"\n\nAnswer the question: \"{query}\" clearly and concisely." if lang == "en"
                  else f"सूचना:\n\"{snippet_text}\"\n\nप्रश्न \"{query}\" का स्पष्ट और संक्षिप्त उत्तर दें।")
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
        )
        return completion.choices[0].message.content.strip()
    except Exception:
        return snippet_text

# External Query Handler
def handle_external_query(query, lat, lng, history=[]):
    lang = detect_language(query)
    classification_response = classify_query_with_gpt(query)
    print("GPT-4 Response:", classification_response)

    if "error" in classification_response:
        return classification_response["error"]

    try:
        classification = classification_response.get('classification')
        gpt_location = classification_response.get('location')

        if gpt_location and gpt_location.lower() != 'none':
            location_name = gpt_location
        elif lat != 'None' and lng != 'None':
            city_name, country_name = get_city_and_country_from_coordinates(lat, lng)
            location_name = f"{city_name}, {country_name}" if city_name != "City not found" else "Pune, India"
        else:
            location_name = "Pune, India"

        if classification == 'time':
            timezone = get_timezone_from_lat_lng(lat, lng) if lat != 'None' else "Asia/Kolkata"
            return get_time(location_name, timezone, lang)

        elif classification and "weather" in classification:
            return get_weather(location_name, lang=lang)

        elif classification and "general knowledge" in classification:
            return handle_general_knowledge_query(query, lang)

        else:
            return "Query not understood." if lang == "en" else "प्रश्न समझ में नहीं आया।"

    except Exception as e:
        print(f"External query handling error: {e}")
        return "An error occurred."

# Get City and Country from Coordinates
def get_city_and_country_from_coordinates(lat, lon):
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        geolocator = Nominatim(user_agent="lifecare-app-prod", ssl_context=ssl_context)
        location = geolocator.reverse((lat, lon), language='en')
        if location:
            address = location.raw.get('address', {})
            city = address.get('city') or address.get('town') or address.get('village') or "City not found"
            country = address.get('country', "Country not found")
            return city, country
        return "City not found", "Country not found"
    except Exception:
        return "City not found", "Country not found"

# Get Coordinates from Location Name
def get_coordinates_from_name(location_name):
    try:
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {'address': location_name, 'key': GOOGLE_API_KEY}
        response = requests.get(url, params=params)
        data = response.json()
        if data.get('status') == 'OK' and data.get('results'):
            latitude = data['results'][0]['geometry']['location']['lat']
            longitude = data['results'][0]['geometry']['location']['lng']
            return latitude, longitude
        else:
            return None
    except Exception:
        return None

# Get Timezone from LatLng
def get_timezone_from_lat_lng(lat, lng):
    try:
        url = f"https://maps.googleapis.com/maps/api/timezone/json?location={lat},{lng}&timestamp={int(datetime.now().timestamp())}&key={GOOGLE_API_KEY}"
        response = requests.get(url)
        timezone_data = response.json()
        if timezone_data['status'] == 'OK':
            return timezone_data['timeZoneId']
        else:
            return "Asia/Kolkata"
    except Exception:
        return "Asia/Kolkata"

