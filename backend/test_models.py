from datetime import datetime

from app.domain.models import SensorEvent
from app.services.prediction_service import PredictionService
from app.services.temperature_service import TemperatureAdvisorService

event = SensorEvent(
    machine_id="M-101",
    temperature=82.4,
    vibration=1.2,
    pressure=53.7,
    timestamp=datetime.now()
)

print(event)

prediction = PredictionService().predict(event)
print(prediction)

temperature_recommendation = TemperatureAdvisorService().recommend(event)
print(temperature_recommendation)