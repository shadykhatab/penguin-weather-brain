import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = os.environ.get("GEMINI_API_KEY")

# --- WEATHER TOOL ---
def get_live_weather(city):
    try:
        # Find City
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {"name": city, "count": 1, "language": "en", "format": "json"}
        geo_res = requests.get(geo_url, params=geo_params).json()
        
        if "results" not in geo_res: return None

        lat = geo_res["results"][0]["latitude"]
        lon = geo_res["results"][0]["longitude"]
        city_name = geo_res["results"][0]["name"]

        # Get Weather
        weather_url = "https://api.open-meteo.com/v1/forecast"
        w_params = {
            "latitude": lat, 
            "longitude": lon, 
            "current": "temperature_2m,weather_code,wind_speed_10m"
        }
        w_res = requests.get(weather_url, params=w_params).json()
        current = w_res["current"]

        # Decode Condition
        code = current["weather_code"]
        cond = "Clear"
        if code > 2: cond = "Cloudy"
        if code > 50: cond = "Rainy"
        if code > 70: cond = "Snowy"
        if code > 95: cond = "Stormy"

        return f"{city_name}: {current['temperature_2m']}°C, {cond}, Wind {current['wind_speed_10m']}km/h"
    except:
        return None

# --- DIRECT API CALL (No Library) ---
def talk_to_google_direct(prompt):
    if not API_KEY: return "I lost my API key!"
    
    # We use the raw REST API URL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        # Check if Google is happy
        if response.status_code == 200:
            result = response.json()
            # Extract the text from the complex JSON answer
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            # If it fails, print the REAL error from Google
            return f"Google Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return f"Connection Failed: {str(e)}"

# --- CHAT ENDPOINT ---
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message', '')
    
    # 1. Detect City
    city_context = "New York" 
    if "paris" in user_msg.lower(): city_context = "Paris"
    elif "london" in user_msg.lower(): city_context = "London"
    elif "tokyo" in user_msg.lower(): city_context = "Tokyo"
    elif "san francisco" in user_msg.lower(): city_context = "San Francisco"

    # 2. Get Real Weather
    weather_info = get_live_weather(city_context)
    if not weather_info: weather_info = "Weather unavailable."

    # 3. ASK GOOGLE DIRECTLY
    prompt = f"""
    You are a funny, sarcastic AI Penguin assistant. 
    The current weather is: {weather_info}.
    The user asks: "{user_msg}"
    Rules: Be short, sassy, and helpful.
    """
    
    reply = talk_to_google_direct(prompt)

    return jsonify({"reply": reply})

@app.route('/weather', methods=['GET'])
def weather():
    return jsonify({"temperature": "12", "condition": "Clear", "humidity": "50", "wind_speed": "10"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)