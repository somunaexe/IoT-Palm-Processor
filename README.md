# IoT Palm Processor

A small event-driven pipeline that ingests IoT sensor readings from palm fruit
processing equipment (sterilizers/digesters), enriches them with a risk score
and an optimal-temperature recommendation, persists them, and visualizes them
on a live dashboard.

## Architecture

```
simulator ──▶ Azure Event Hub ──▶ backend (FastAPI consumer) ──▶ SQL database
                                        │
                                        ├─ REST  /events/latest
                                        └─ GraphQL /graphql
                                              │
                                              ▼
                                        streamlit dashboard
```

- **`simulator/`** — generates fake sensor readings (`temperature`, `vibration`,
  `pressure` per machine) and publishes them to an Azure Event Hub every 15s.
- **`backend/`** — FastAPI service that consumes events from the Event Hub,
  enriches each one, and stores it. Exposes the data over REST and GraphQL.
- **`streamlit/`** — a live dashboard that polls the REST API and renders
  KPIs, charts, and alerts.
- **`terraform/`** and **`k8s/`** — infrastructure for provisioning the Azure
  resources (Event Hub, SQL, storage, networking) and deploying the backend
  to Kubernetes.

## Enrichment pipeline

Each incoming `SensorEvent` is run through two independent services inside
`SensorService.process_event` (`backend/app/services/sensor_service.py`),
and the results are combined into an `EnrichedSensorEvent` before being saved:

1. **`PredictionService`** (`backend/app/services/prediction_service.py`) —
   a heuristic risk score/status (`HIGH` / `NORMAL`) from temperature,
   vibration, and pressure.
2. **`TemperatureAdvisorService`** (`backend/app/services/temperature_service.py`)
   — recommends the optimal sterilizer temperature and an action
   (`MAINTAIN` / `INCREASE_HEAT` / `DECREASE_HEAT`).

### How the temperature recommendation works

Palm fruit bunches are sterilized with saturated steam before pressing. The
logic in `backend/app/ml/temperature_model.py` encodes two real constraints
from that process, since there's no labeled outcome data yet to train a
model on:

1. **Steam must stay saturated.** For saturated steam, temperature and
   pressure are locked together by the steam tables — the chamber `pressure`
   reading implies a physically correct target temperature (looked up via
   interpolation over a steam table), rather than trusting the temperature
   reading on its own.
2. **Safe operating window: 125–145°C.** Below that, the lipase enzyme
   survives and free fatty acid keeps rising after harvest; above it, energy
   is wasted and the fruit is overcooked. The recommendation is clamped to
   this range.

`vibration` is treated as a proxy for digester/stripper mechanical load and
nudges the target slightly (heavier, more agitated batches mix less evenly,
so they get a small upward margin). This is the weakest part of the model —
if a real load or steam-quality sensor is added, that mapping should be
replaced first.

This is intentionally a **rule-based heuristic**, not a trained model. It's
written as a pure function (`recommend_optimal_temperature`,
`recommend_action`) so it can be swapped for a trained regressor/classifier
later, once real outcome data (e.g. oil yield or FFA level per batch) is
available, without changing the service layer that calls it.

## Running locally

```bash
docker compose up --build
```

This starts three containers:

| Service     | Port | Description                          |
|-------------|------|---------------------------------------|
| `simulator` | —    | publishes fake sensor events          |
| `backend`   | 8000 | FastAPI REST + GraphQL API            |
| `streamlit` | 8501 | live dashboard                        |

### Required environment variables

Create a `.env` file in the project root:

```
EVENTHUB_CONN_STR=<Azure Event Hub connection string>
EVENTHUB_NAME=<Event Hub name>
DATABASE_URL=<SQLAlchemy/pyodbc connection string>
```

## API

- `GET /events/latest` — latest enriched sensor events (REST)
- `POST /graphql` — `latestEvents(limit: Int)` query (GraphQL), returns the
  same fields including `riskScore`, `status`, `optimalTemperature`, and
  `temperatureAction`

## Dashboard

The Streamlit dashboard (`streamlit/app.py`) shows, per machine:

- Risk score distribution and trend, with a critical-risk alert panel
- Actual vs. recommended sterilizer temperature over time
- A breakdown of recommended temperature actions
- A live sensor feed table and a dedicated temperature-alerts panel for
  any reading that isn't `MAINTAIN`
