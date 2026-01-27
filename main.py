import os
from flask import Flask, request, jsonify
import requests
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = os.environ.get("GEMINI_API_KEY")

# Configure AI with a Fail-Safe Mechanism
model = None
if API_KEY:
    genai.configure(api_key=API_KEY)
    try:
        # Try the super fast Flash model first
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        # If that fails, use the stable Pro model
        print("Flash model failed, switching to Pro")
        model = genai.GenerativeModel('gemini-pro')
else:
    print("WARNING: No API Key found! AI features will be disabled.")

# --- WEATHER TOOL ---
def get_live_weather(city):
    try:
        # 1. Find City
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {"name": city, "count": 1, "language": "en", "format": "json"}
        geo_res = requests.get(geo_url, params=geo_params).json()
        
        if "results" not in geo_res: return None

        lat = geo_res["results"][0]["latitude"]
        lon = geo_res["results"][0]["longitude"]
        city_name = geo_res["results"][0]["name"]

        # 2. Get Weather
        weather_url = "https://api.open-meteo.com/v1/forecast"
        w_params = {
            "latitude": lat, 
            "longitude": lon, 
            "current": "temperature_2m,weather_code,wind_speed_10m"
        }
        w_res = requests.get(weather_url, params=w_params).json()
        current = w_res["current"]

        # 3. Simple Condition Map
        code = current["weather_code"]
        cond = "Clear"
        if code > 2: cond = "Cloudy"
        if code > 50: cond = "Rainy"
        if code > 70: cond = "Snowy"
        if code > 95: cond = "Stormy"

        return f"{city_name}: {current['temperature_2m']}°C, {cond}, Wind {current['wind_speed_10m']}km/h"
    except:
        return None

# --- CHAT ENDPOINT ---
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message', '')
    
    # 1. Detect City context
    city_context = "New York" 
    if "paris" in user_msg.lower(): city_context = "Paris"
    elif "london" in user_msg.lower(): city_context = "London"
    elif "tokyo" in user_msg.lower(): city_context = "Tokyo"
    elif "san francisco" in user_msg.lower(): city_context = "San Francisco"

    # 2. Get Real Weather Data
    weather_info = get_live_weather(city_context)
    if not weather_info: weather_info = "Weather data unavailable."

    # 3. ASK GEMINI (With error handling)
    reply = "My brain is frozen! 🐧"
    
    if model:
        try:
            prompt = f"""
            You are a funny, sarcastic AI Penguin assistant. 
            The current weather is: {weather_info}.
            The user asks: "{user_msg}"
            Rules: Use the real weather data. Be sassy but helpful. Keep it short.
            """
            response = model.generate_content(prompt)
            reply = response.text.strip()
        except Exception as e:
            # If the specific model crashes during chat, try one last fallback
            try:
                backup_model = genai.GenerativeModel('gemini-pro')
                response = backup_model.generate_content(prompt)
                reply = response.text.strip()
            except:
                reply = f"I'm having a bad hair day. (Error: {str(e)})"
    else:
        reply = "I lost my API key! Check server settings."

    return jsonify({"reply": reply})

@app.route('/weather', methods=['GET'])
def weather():
    return jsonify({"temperature": "12", "condition": "Clear", "humidity": "50", "wind_speed": "10"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)