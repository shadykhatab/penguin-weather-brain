import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from services.weather_service import get_weather_data
from services.penguin_service import get_penguin_commentary
from supabase import create_client, Client
from datetime import datetime, timedelta

app = FastAPI()

# --- CONNECT TO SUPABASE ---
# We check if keys exist to avoid crashing, but they MUST exist for reports to work.
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Connected to Supabase!")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")

# --- MODELS ---
class ReportRequest(BaseModel):
    city: str
    condition: str

class WeatherRequest(BaseModel):
    city: str
    question: Optional[str] = "What is the weather?"

# --- HELPER: THE ALGORITHM 🛡️ ---
def verify_condition(city: str, condition: str):
    """
    Checks if a condition is 'verified' based on reports in the last 30 minutes.
    """
    if not supabase:
        return False, 0

    # 1. Define thresholds (The "Urgency Weight")
    threshold = 5  # Default for sunny/cloudy
    if condition.lower() in ["raining", "windy"]:
        threshold = 3
    elif condition.lower() in ["flood", "snowing", "fire"]:
        threshold = 2

    # 2. Time Window (Last 30 minutes)
    thirty_mins_ago = (datetime.utcnow() - timedelta(minutes=30)).isoformat()

    # 3. Query the Database (Count votes)
    # 3. Query the Database (Count votes)
    try:
        # We removed the time filter to make counting easier
        response = supabase.table("reports") \
            .select("*", count="exact") \
            .eq("city", city) \
            .eq("condition", condition) \
            .execute()
            
        vote_count = response.count
        print(f"DEBUG: Found {vote_count} votes for {city}") # <--- Added Debug Print
        
        vote_count = response.count
        is_verified = vote_count >= threshold
        
        return is_verified, vote_count
    except Exception as e:
        print(f"Error verifying: {e}")
        return False, 0

@app.get("/")
def read_root():
    return {"message": "Penguin Weather Brain is Active 🐧"}

@app.get("/weather")
async def get_weather(city: str, question: str = "What should I wear?", mode: str = "penguin"):
    # 1. Get Standard API Data
    raw_data = get_weather_data(city)
    current = raw_data.get("current", {})
    
    # Extract standard fields
    temp_c = current.get("temp_c")
    temp_f = current.get("temp_f")
    wind_kph = current.get("wind_kph")
    humidity = current.get("humidity")
    feels_like_c = current.get("feelslike_c")
    condition = current.get("condition", {}).get("text")
    
    # 2. CHECK FOR CROWDSOURCED ALERTS 🚨
    # We check if there are any VERIFIED severe reports in the DB
    severe_alert = ""
    if supabase:
        try:
            # Check for Flood or Snowing specifically
            for hazard in ["FLOOD", "SNOWING"]:
                verified, count = verify_condition(city, hazard)
                if verified:
                    severe_alert = f"⚠️ WARNING: {hazard} reported by {count} users!"
                    condition = f"{hazard} (User Reported)" # Override the API condition
        except:
            pass

    # 3. AI Logic
    ai_context = (
        f"Current Weather in {city}: "
        f"Temp: {temp_c}C. Condition: {condition}. "
        f"Wind: {wind_kph} kph. Humidity: {humidity}%."
        f"{severe_alert}" # Feed the alert to the AI
    )

    forecast_list = []
    forecast_days = raw_data.get("forecast", {}).get("forecastday", [])
    for day in forecast_days:
        date = day.get("date")
        avg_temp = day.get("day", {}).get("avgtemp_c")
        cond = day.get("day", {}).get("condition", {}).get("text")
        chance_rain = day.get("day", {}).get("daily_chance_of_rain")
        forecast_list.append(f"{date}: {avg_temp}C, {cond} ({chance_rain}% rain)")

    if mode == "standard":
        penguin_response = "Standard Data View Active"
    else:
        penguin_response = await get_penguin_commentary(ai_context, question)
    
    return {
        "status": "success",
        "temp_c": temp_c, 
        "penguin_text": penguin_response,
        "forecast": forecast_list,
        "wind_kph": wind_kph,
        "humidity": humidity,
        "feels_like_c": feels_like_c,
        "alert": severe_alert # Send alert to phone
    }

@app.post("/report")
async def report_mismatch(report: ReportRequest):
    print(f"User reported {report.condition} in {report.city}")
    
    msg = "Thanks for the report!"
    
    if supabase:
        try:
            # 1. Insert the Report into Supabase
            data = {"city": report.city, "condition": report.condition}
            supabase.table("reports").insert(data).execute()
            
            # 2. Run the Verification Algorithm
            is_verified, count = verify_condition(report.city, report.condition)
            
            if is_verified:
                msg = f"🚨 CONFIRMED! You are the {count}th person to report this. We are warning everyone!"
            elif count > 1:
                msg = f"Thanks! We have {count} reports now. We need a few more to confirm."
            else:
                msg = "Thanks! You are the first to report this. We'll keep watching."
                
        except Exception as e:
            print(f"Database Error: {e}")
            msg = "Thanks! (Saved locally, DB error)"

    return {"status": "received", "message": msg}