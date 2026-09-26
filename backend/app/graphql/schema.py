import strawberry
from typing import List
from app.domain.models import EnrichedSensorEvent
from app.adapters.database.database import SessionLocal
from app.adapters.database.sql_repository import SqlSensorRepository

@strawberry.type
class SensorEventType:
    machine_id: str
    temperature: float
    vibration: float
    pressure: float
    timestamp: str
    risk_score: float
    status: str
    optimal_temperature: float
    temperature_action: str

@strawberry.type
class Query:

    @strawberry.field
    def latest_events(self, limit: int = 50) -> List[SensorEventType]:
        db = SessionLocal()
        repo = SqlSensorRepository(db)

        events = repo.get_latest(limit)

        return [
            SensorEventType(
                machine_id=e.machine_id,
                temperature=e.temperature,
                vibration=e.vibration,
                pressure=e.pressure,
                timestamp=str(e.timestamp),
                risk_score=e.risk_score,
                status=e.status,
                optimal_temperature=e.optimal_temperature,
                temperature_action=e.temperature_action
            )
            for e in events
        ]