from pydantic import BaseModel
from typing import Optional


class WeatherCondition(BaseModel):
    text: str
    icon: str


class CurrentWeather(BaseModel):
    temperature_f: float
    temperature_c: float
    feels_like_f: float
    feels_like_c: float
    humidity: int
    wind_mph: float
    wind_direction: str
    condition: WeatherCondition
    uv_index: float
    is_day: bool


class Location(BaseModel):
    name: str
    region: str
    country: str
    local_time: str


class WeatherResponse(BaseModel):
    location: Location
    current: CurrentWeather
    penguin_says: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: str
