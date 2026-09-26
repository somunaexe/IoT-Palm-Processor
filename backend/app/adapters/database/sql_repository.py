from sqlalchemy.orm import Session

from app.adapters.database.models import SensorEventTable
from app.domain.models import EnrichedSensorEvent
from app.ports.sensor_repository import SensorRepository

class SqlSensorRepository(SensorRepository):


    def __init__(self, db: Session):
        self.db = db

    def _to_table(self, event: EnrichedSensorEvent) -> SensorEventTable:
        return SensorEventTable(
            machine_id=event.machine_id,
            temperature=event.temperature,
            vibration=event.vibration,
            pressure=event.pressure,
            timestamp=event.timestamp,
            risk_score=event.risk_score,
            status=event.status,
            optimal_temperature=event.optimal_temperature,
            temperature_action=event.temperature_action,
        )


    def _to_domain(self, row: SensorEventTable) -> EnrichedSensorEvent:
        return EnrichedSensorEvent(
            machine_id=row.machine_id,
            temperature=row.temperature,
            vibration=row.vibration,
            pressure=row.pressure,
            timestamp=row.timestamp,
            risk_score=row.risk_score,
            status=row.status,
            optimal_temperature=row.optimal_temperature,
            temperature_action=row.temperature_action,
        )

    def save(self, event: EnrichedSensorEvent) -> None:
        db_event = SensorEventTable(
            machine_id=event.machine_id,
            temperature=event.temperature,
            vibration=event.vibration,
            pressure=event.pressure,
            timestamp=event.timestamp,
            risk_score=event.risk_score,
            status=event.status,
            optimal_temperature=event.optimal_temperature,
            temperature_action=event.temperature_action,
        )

        self.db.add(db_event)
        print("INSERTING EVENT:", db_event)
        self.db.commit()
        self.db.refresh(db_event)

    def save_many(self, events: list[EnrichedSensorEvent]) -> None:
        rows = [
            self._to_table(e)
            for e in events
        ]

        self.db.add_all(rows)
        print("INSERTING EVENT:", rows)
        self.db.commit()

    def get_latest(self, limit: int = 100) -> list[EnrichedSensorEvent]:
        events = (
            self.db.query(SensorEventTable)
            .order_by(SensorEventTable.timestamp.desc())
            .limit(limit)
            .all()
        )
        print(self.db)
        print(events)
        return [
            self._to_domain(e)
            for e in events
        ]
    
    def get_machine_history(self, machine_id: str,) -> list[EnrichedSensorEvent]:
        rows = (
            self.db.query(SensorEventTable)
            .filter(SensorEventTable.machine_id == machine_id)
            .order_by(SensorEventTable.timestamp.desc())
            .all()
        )

        return [
            self._to_domain(rows)
            for row in rows
        ]