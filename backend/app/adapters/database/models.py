from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class SensorEventTable(Base):
    __tablename__ = "sensor_events"

    id = Column(Integer, primary_key=True, autoincrement=True)

    machine_id = Column(String(50), nullable=False)

    temperature = Column(Float, nullable=False)

    vibration = Column(Float, nullable=False)

    pressure = Column(Float, nullable=False)

    timestamp = Column(DateTime, nullable=False)

    risk_score = Column(Float, nullable=False)

    status = Column(String(20), nullable=False)

    optimal_temperature = Column(Float, nullable=False)

    temperature_action = Column(String(20), nullable=False)