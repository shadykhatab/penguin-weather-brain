import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = os.environ.get("GEMINI_API_KEY")

# --- 1. SHARED WEATHER TOOL (Returns Data) ---
def get_weather_data(city):
    try:
        # Geocoding
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_params = {"name": city, "count": 1, "language": "en", "format": "json"}
        geo_res = requests.get(geo_url, params=geo_params).json()
        
        if "results" not in geo_res: return None

        lat = geo_res["results"][0]["latitude"]
        lon = geo_res["results"][0]["longitude"]
        city_name = geo_res["results"][0]["name"]

        # Get Real Weather (Added Humidity!)
        weather_url = "https://api.open-meteo.com/v1/forecast"
        w_params = {
            "latitude": lat, 
            "longitude": lon, 
            "current": "temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m"
        }
        w_res = requests.get(weather_url, params=w_params).json()
        current = w_res["current"]

        # Decode Condition
        code = current["weather_code"]
        cond = "Clear"
        if code > 2: cond = "Cloudy"
        if code > 40: cond = "Foggy"
        if code > 50: cond = "Rainy"
        if code > 70: cond = "Snowy"
        if code > 95: cond = "Stormy"

        # Return a Dictionary (Perfect for Home Screen)
        return {
            "city": city_name,
            "temperature": str(current['temperature_2m']),
            "condition": cond,
            "wind_speed": str(current['wind_speed_10m']),
            "humidity": str(current.get('relative_humidity_2m', '50')) 
        }
    except:
        return None

# --- 2. AI FUNCTION (Using Gemini 2.5) ---
def talk_to_google(prompt, weather_text):
    if not API_KEY: return "I lost my API key!"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    full_prompt = f"""
    System: You are a funny, sarcastic AI Penguin assistant.
    Context: The user is in a location where the weather is: {weather_text}.
    User Question: "{prompt}"
    Instruction: Answer the user. Be short, sassy, and helpful. Do not mention that you are an AI.
    """
    
    payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Google Error {response.status_code}"
    except Exception as e:
        return f"Connection Failed: {str(e)}"

# --- 3. ENDPOINTS ---

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message', '')
    
    # Simple Context Detection
    city_context = "New York"
    if "paris" in user_msg.lower(): city_context = "Paris"
    elif "london" in user_msg.lower(): city_context = "London"
    elif "tokyo" in user_msg.lower(): city_context = "Tokyo"
    elif "san francisco" in user_msg.lower(): city_context = "San Francisco"

    # Get Data for the AI
    w_data = get_weather_data(city_context)
    
    if w_data:
        w_text = f"{w_data['city']}: {w_data['temperature']}C, {w_data['condition']}, Wind {w_data['wind_speed']}"
    else:
        w_text = "Weather unavailable"
        
    reply = talk_to_google(user_msg, w_text)
    return jsonify({"reply": reply})

@app.route('/weather', methods=['GET'])
def weather():
    # THIS is the fix for the Home Screen
    city = request.args.get('city', 'New York')
    w_data = get_weather_data(city)
    
    if w_data:
        return jsonify(w_data) # Return REAL data
    else:
        return jsonify({"temperature": "--", "condition": "Error", "humidity": "--", "wind_speed": "--"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)