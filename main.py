from flask import Flask, request, jsonify
import requests
import random

app = Flask(__name__)

# --- 1. THE BRAIN'S TOOLS (Functions) ---

def get_live_weather(city):
    """Fetches real weather data from Open-Meteo."""
    try:
        # 1. Find the city
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_data = requests.get(geo_url).json()
        
        if "results" not in geo_data:
            return None # City not found

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        city_name = geo_data["results"][0]["name"]

        # 2. Get the weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
        data = requests.get(weather_url).json()
        current = data["current"]

        # 3. Decode the weather code
        w_code = current["weather_code"]
        condition = "Clear"
        if w_code in [1, 2, 3]: condition = "Cloudy"
        if w_code in [45, 48]: condition = "Foggy"
        if w_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: condition = "Rainy"
        if w_code in [71, 73, 75, 77, 85, 86]: condition = "Snowy"
        if w_code in [95, 96, 99]: condition = "Stormy"

        return {
            "city": city_name,
            "temp": current["temperature_2m"],
            "wind": current["wind_speed_10m"],
            "condition": condition
        }
    except:
        return None

def get_clothing_advice(temp, condition):
    """Decides what you should wear based on numbers."""
    advice = ""
    
    # TEMPERATURE LOGIC
    if temp >= 30:
        advice += "It is boiling hot! 🔥 Wear shorts, sandals, and a thin cotton t-shirt. Do NOT wear jeans unless you want to melt."
    elif temp >= 20:
        advice += "It's actually nice. Jeans and a t-shirt are perfect. Maybe bring sunglasses so you look cool. 😎"
    elif temp >= 10:
        advice += "It's a bit chilly. You definitely need a jacket or a hoodie. Don't be a hero, cover up."
    elif temp >= 0:
        advice += "Okay, it's cold. heavy coat time. Scarf, gloves, the whole deal. 🧣"
    else:
        advice += "It is FREEZING! ❄️ Wear 7 layers. Wear everything you own. Look like a marshmallow."

    # CONDITION LOGIC
    if condition == "Rainy" or condition == "Stormy":
        advice += " Also, take an umbrella or you'll look like a drowned rat."
    
    return advice

def get_travel_verdict(condition, wind):
    """Decides if it is safe to travel/school."""
    if condition == "Stormy" or wind > 60:
        return "Honestly? Stay home. It's nasty out there. 🚨 Not a good time for travel or school runs."
    elif condition == "Snowy":
        return "Roads might be slippery. Drive like a grandma or just stay in bed with hot cocoa. ☕"
    elif condition == "Rainy":
        return "It's wet, but you'll survive. Just drive slow and don't splash anyone."
    else:
        return "Conditions are perfect! Go explore the world! (Or just go to work, sorry). 🌍"

# --- 2. THE SERVER ENDPOINTS ---

@app.route('/weather', methods=['GET'])
def weather_endpoint():
    # Simple endpoint for the Home Screen numbers
    city = request.args.get('city', 'New York')
    data = get_live_weather(city)
    if data:
        return jsonify({
            "temperature": str(data['temp']),
            "condition": data['condition'],
            "humidity": "50", # Simplified for now
            "wind_speed": str(data['wind'])
        })
    return jsonify({"error": "City not found"}), 404

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    data = request.json
    user_text = data.get('message', '').lower()
    
    # 1. DETECT CITY (Basic logic: look for common cities or assume "New York" for demo)
    # In a real app, we would use NLP to extract the city name dynamically.
    # For this demo, we will check if the user typed a specific city, otherwise default to "local".
    target_city = "New York" # Default
    if "paris" in user_text: target_city = "Paris"
    elif "london" in user_text: target_city = "London"
    elif "tokyo" in user_text: target_city = "Tokyo"
    elif "dubai" in user_text: target_city = "Dubai"
    elif "cairo" in user_text: target_city = "Cairo"
    elif "sunnyvale" in user_text: target_city = "Sunnyvale"
    
    # 2. GET REAL DATA
    weather = get_live_weather(target_city)
    
    if not weather:
        return jsonify({"reply": "I couldn't find that city. Check your spelling, I'm a penguin, not a dictionary! 🐧"})

    # 3. ANALYZE USER QUESTION (The Decision Maker)
    
    # CATEGORY: CLOTHING 👗👔
    if any(word in user_text for word in ["wear", "clothes", "jacket", "jeans", "shirt", "coat", "dress", "sandals"]):
        verdict = get_clothing_advice(weather['temp'], weather['condition'])
        reply = f"In {weather['city']}, it is {weather['temp']}°C. {verdict}"

    # CATEGORY: TRAVEL / DRIVING 🚗✈️
    elif any(word in user_text for word in ["travel", "drive", "fly", "trip", "visit", "go to"]):
        verdict = get_travel_verdict(weather['condition'], weather['wind'])
        reply = f"Thinking of going to {weather['city']}? {verdict} (Temp: {weather['temp']}°C)"

    # CATEGORY: KIDS / SCHOOL 🏫👶
    elif any(word in user_text for word in ["kids", "school", "safe", "baby"]):
        if weather['condition'] in ["Stormy", "Snowy"] or weather['wind'] > 50:
            reply = f"⚠️ Safety Alert: It is {weather['condition']} in {weather['city']} with high winds. Maybe keep the little ones inside today."
        else:
            reply = f"It's {weather['temp']}°C and {weather['condition']}. Totally fine for school! Kick them out the door! 🎓"

    # CATEGORY: GENERAL WEATHER ☁️
    elif any(word in user_text for word in ["weather", "forecast", "look like", "outside", "hot", "cold"]):
        sarcasm = ""
        if weather['temp'] > 30: sarcasm = "Start sweating."
        elif weather['temp'] < 5: sarcasm = "Hope you like shivering."
        else: sarcasm = "Pretty boring, actually."
        
        reply = f"Current situation in {weather['city']}: {weather['temp']}°C and {weather['condition']}. {sarcasm}"

    # CATCH-ALL (If I don't understand)
    else:
        reply = f"I'm listening, but I only know about weather, clothes, and safety. Ask me if you should wear a jacket in {target_city}! 🐧"

    return jsonify({"reply": reply})

@app.route('/report', methods=['POST'])
def report_flood():
    return jsonify({"status": "confirmed", "message": "Alert received!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)