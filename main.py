from fastapi import FastAPI, HTTPException
from services.weather_service import get_weather_data
from services.penguin_service import get_penguin_commentary
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class ReportRequest(BaseModel):
    city: str
    condition: str

@app.get("/")
def read_root():
    return {"message": "Penguin Weather Brain is Active 🐧"}

@app.get("/weather")
async def get_weather(city: str, question: str = "What should I wear?", mode: str = "penguin"):
    raw_data = get_weather_data(city)
    
    current = raw_data.get("current", {})
    temp_c = current.get("temp_c")
    temp_f = current.get("temp_f")
    feels_like_c = current.get("feelslike_c") # <--- Get Feels Like
    wind_kph = current.get("wind_kph")        # <--- Get Wind
    humidity = current.get("humidity")        # <--- Get Humidity
    condition = current.get("condition", {}).get("text")
    is_day = current.get("is_day")

    # Context for AI
    ai_context = (
        f"Current Weather in {city}: "
        f"Temp: {temp_c}C. Condition: {condition}. "
        f"Wind: {wind_kph} kph. Humidity: {humidity}%."
    )

    forecast_list = []
    forecast_days = raw_data.get("forecast", {}).get("forecastday", [])
    for day in forecast_days:
        date = day.get("date")
        avg_temp = day.get("day", {}).get("avgtemp_c")
        cond = day.get("day", {}).get("condition", {}).get("text")
        chance_rain = day.get("day", {}).get("daily_chance_of_rain")
        forecast_list.append(f"{date}: {avg_temp}C, {cond} ({chance_rain}% rain)")

    # LOGIC: If Standard, we send a boring message. If Penguin, we ask AI.
    if mode == "standard":
        penguin_response = "Standard Data View Active" # Placeholder text
    else:
        penguin_response = await get_penguin_commentary(ai_context, question)
    
    return {
        "status": "success",
        "temp_c": temp_c, 
        "penguin_text": penguin_response,
        "forecast": forecast_list,
        # --- NEW DATA FIELDS ---
        "wind_kph": wind_kph,
        "humidity": humidity,
        "feels_like_c": feels_like_c
    }

@app.post("/report")
async def report_mismatch(report: ReportRequest):
    print(f"User reported {report.condition} in {report.city}")
    thank_you_msg = f"Thanks! Noted that it is {report.condition}."
    return {"status": "received", "message": thank_you_msg}