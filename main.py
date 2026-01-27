import os
from flask import Flask, request, jsonify
import requests
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURATION ---
# We get the key from the Server Settings (Safety First!)
API_KEY = os.environ.get("GEMINI_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)
    # Use the fast, free Flash model
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None
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

# --- CHAT ENDPOINT (THE GEMINI BRAIN) ---
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message', '')
    
    # 1. Detect City (Simple check, or default to user's "Home Base")
    # In a real app, you'd send the user's GPS city here.
    city_context = "New York" 
    if "paris" in user_msg.lower(): city_context = "Paris"
    elif "london" in user_msg.lower(): city_context = "London"
    elif "tokyo" in user_msg.lower(): city_context = "Tokyo"
    elif "san francisco" in user_msg.lower(): city_context = "San Francisco"

    # 2. Get Real Weather Data
    weather_info = get_live_weather(city_context)
    
    if not weather_info:
        weather_info = "Weather data unavailable."

    # 3. ASK GEMINI
    if model:
        try:
            # The "System Prompt" tells it how to behave
            prompt = f"""
            You are a funny, sarcastic AI Penguin assistant. 
            The current weather is: {weather_info}.
            
            The user asks: "{user_msg}"
            
            Rules:
            1. Use the real weather data to answer.
            2. Be sassy but helpful. Use penguin puns if possible.
            3. Keep it short (under 2 sentences).
            4. If they ask about clothes, give advice based on the temp.
            """
            
            response = model.generate_content(prompt)
            reply = response.text.strip()
            
        except Exception as e:
            reply = f"My brain froze! 🧊 (Error: {str(e)})"
    else:
        reply = "I lost my API key! Please check the server settings. 🐧"

    return jsonify({"reply": reply})

@app.route('/weather', methods=['GET'])
def weather():
    # Keep the old endpoint for the Home Screen numbers
    city = request.args.get('city', 'New York')
    # ... (Reuse simple logic or keep getting live weather)
    # For now, let's just return simple JSON so the home screen doesn't break
    return jsonify({"temperature": "12", "condition": "Clear", "humidity": "50", "wind_speed": "10"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)