from app.domain.models import SensorEvent, TemperatureRecommendation
from app.ml.temperature_model import recommend_action, recommend_optimal_temperature


class TemperatureAdvisorService:

    def recommend(self, event: SensorEvent) -> TemperatureRecommendation:
        optimal_temperature = recommend_optimal_temperature(
            pressure=event.pressure,
            vibration=event.vibration,
        )
        action = recommend_action(event.temperature, optimal_temperature)

        return TemperatureRecommendation(
            optimal_temperature=optimal_temperature,
            action=action,
        )
