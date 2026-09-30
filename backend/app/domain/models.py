from datetime import datetime
from pydantic import BaseModel


class SensorEvent(BaseModel):
    machine_id: str
    temperature: float
    vibration: float
    pressure: float
    timestamp: datetime


class Prediction(BaseModel):
    risk_score: float
    status: str


class TemperatureRecommendation(BaseModel):
    optimal_temperature: float
    action: str


class EnrichedSensorEvent(SensorEvent):
    risk_score: float
    status: str
    optimal_temperature: float
    temperature_action: str