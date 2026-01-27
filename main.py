import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- CONFIGURATION ---
API_KEY = os.environ.get("GEMINI_API_KEY")

# --- WEATHER TOOL ---
def get_live_weather(city):
    return "15°C and Sunny" # Simplified for this test

# --- DIRECT API CALL (DIAGNOSTIC MODE) ---
def talk_to_google_direct(prompt):
    if not API_KEY: return "I lost my API key!"
    
    # 1. THE TRICK: We are asking for the LIST of models first
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    
    try:
        # Step A: Ask Google what models exist
        list_response = requests.get(list_url)
        
        if list_response.status_code == 200:
            data = list_response.json()
            # We look for any model that has "generateContent" capability
            valid_models = []
            for m in data.get('models', []):
                if "generateContent" in m.get('supportedGenerationMethods', []):
                    valid_models.append(m['name'])
            
            # Step B: Try the first valid model we found
            if not valid_models:
                return "CRITICAL: Google says you have NO valid models available! (Check API Key permissions)"
                
            best_model = valid_models[0] # Just pick the first one that works
            
            # NOW we use that specific name to generate the text
            generate_url = f"https://generativelanguage.googleapis.com/v1beta/{best_model}:generateContent?key={API_KEY}"
            
            headers = {'Content-Type': 'application/json'}
            payload = {
                "contents": [{
                    "parts": [{"text": f"SYSTEM: You are a penguin. USER: {prompt}"}]
                }]
            }
            
            gen_response = requests.post(generate_url, headers=headers, json=payload)
            
            if gen_response.status_code == 200:
                result = gen_response.json()
                text = result['candidates'][0]['content']['parts'][0]['text']
                return f"{text} (Powered by {best_model})"
            else:
                return f"Model {best_model} failed: {gen_response.text}"
                
        else:
            return f"List Failed {list_response.status_code}: {list_response.text}"
            
    except Exception as e:
        return f"Connection Failed: {str(e)}"

# --- CHAT ENDPOINT ---
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message', '')
    reply = talk_to_google_direct(user_msg)
    return jsonify({"reply": reply})

@app.route('/weather', methods=['GET'])
def weather():
    return jsonify({"temperature": "12", "condition": "Clear", "humidity": "50", "wind_speed": "10"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)