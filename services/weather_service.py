import os
import requests
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

def get_weather_data(city: str):
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Weather API Key not configured")
    
    # CHANGED: We now use the "forecast.json" endpoint
    # days=5 means we get today + next 4 days
    url = "http://api.weatherapi.com/v1/forecast.json"
    params = {
        "key": api_key,
        "q": city,
        "days": 5,
        "aqi": "no",
        "alerts": "no"
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="City not found")
        
    return response.json()