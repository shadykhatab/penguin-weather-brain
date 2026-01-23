from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- WEATHER ENDPOINT ---
@app.route('/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city')
    # Use a free weather API (Open-Meteo) that doesn't require a key for this demo
    # We search for the city to get lat/long
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_response = requests.get(geo_url).json()
        
        if "results" not in geo_response:
            return jsonify({"error": "City not found"}), 404
            
        lat = geo_response["results"][0]["latitude"]
        lon = geo_response["results"][0]["longitude"]
        
        # Now get the weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
        weather_data = requests.get(weather_url).json()
        
        current = weather_data["current"]
        
        # Simple code to text map
        w_code = current["weather_code"]
        condition = "Clear"
        if w_code > 2: condition = "Cloudy"
        if w_code > 50: condition = "Rainy"
        if w_code > 70: condition = "Snowy"
        if w_code > 95: condition = "Stormy"

        return jsonify({
            "temperature": str(current["temperature_2m"]),
            "condition": condition,
            "humidity": str(current["relative_humidity_2m"]),
            "wind_speed": str(current["wind_speed_10m"])
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- REPORT ENDPOINT ---
@app.route('/report', methods=['POST'])
def report_flood():
    data = request.json
    city = data.get('city')
    print(f"ALARM: Flood reported in {city}!")
    return jsonify({"status": "confirmed", "message": f"Alert received for {city}"})

# --- NEW: PENGUIN CHAT LOGIC ---
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '').lower()

    # This is the "Brain" deciding what to say
    if "weather" in user_message:
        reply = "I can't look outside right now, but you can check the Home screen for the live forecast! ☁️"
    elif "hello" in user_message or "hi" in user_message:
        reply = "Waddle waddle! I am listening. 🐧"
    elif "food" in user_message or "fish" in user_message:
        reply = "Did someone say fish?! 🐟 I am hungry!"
    elif "flood" in user_message or "danger" in user_message:
        reply = "Stay safe! Please use the big Red Button to warn others! 🚨"
    elif "joke" in user_message:
        reply = "How does a penguin build its house? Igloos it together! 😂"
    else:
        reply = "Noot noot! I am just a simple penguin. Ask me about weather, food, or jokes!"

    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)