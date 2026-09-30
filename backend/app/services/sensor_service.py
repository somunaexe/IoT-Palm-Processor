from app.domain.models import SensorEvent, EnrichedSensorEvent
from app.ports.sensor_repository import SensorRepository
from app.services.prediction_service import PredictionService
from app.services.temperature_service import TemperatureAdvisorService


class SensorService:

    def __init__(
        self,
        sensor_repository: SensorRepository,
        prediction_service: PredictionService,
        temperature_service: TemperatureAdvisorService,
    ):
        self.sensor_repository = sensor_repository
        self.prediction_service = prediction_service
        self.temperature_service = temperature_service
        self.event_buffer = []
        self.BATCH_SIZE = 50

    def process_event(self, event: SensorEvent) -> EnrichedSensorEvent:
        prediction = self.prediction_service.predict(event)
        temperature_recommendation = self.temperature_service.recommend(event)

        enriched = EnrichedSensorEvent(
            machine_id=event.machine_id,
            temperature=event.temperature,
            vibration=event.vibration,
            pressure=event.pressure,
            timestamp=event.timestamp,
            risk_score=prediction.risk_score,
            status=prediction.status,
            optimal_temperature=temperature_recommendation.optimal_temperature,
            temperature_action=temperature_recommendation.action,
        )

        self.sensor_repository.save(enriched)

        return enriched
    
    def process_events(self, event: SensorEvent) -> list[EnrichedSensorEvent]:

        enriched_events = []
        self.event_buffer.append(event)
        
        if len(self.event_buffer) > self.BATCH_SIZE:
            for e in self.event_buffer:
                enriched = self.process_event(e)
                enriched_events.append(enriched)

        return enriched_events