# DevPulse

DevPulse is a backend-focused API reliability and incident-monitoring service built with FastAPI, PostgreSQL, Redis, SQLAlchemy, Alembic, APScheduler, and Docker Compose.

It registers safe/read-only service endpoints, stores health-check history and latency, tracks repeated failures in a five-minute Redis window, creates one incident per ongoing outage, and can notify Slack when a new incident opens.

## How it works

```text
Enabled monitors
      |
APScheduler (every 60 seconds by default)
      |
External health/status endpoint
      |
MonitorCheck stored in PostgreSQL
      |
DOWN -> Redis failure counter (5-minute TTL)
      |
3 failures -> create OPEN incident -> Slack alert
4+ failures -> update the same OPEN incident
      |
Manual resolve API
```

DevPulse should monitor health, status, ping, sandbox, or other read-only endpoints. Do not configure transactional production endpoints that could create payments, orders, or other side effects.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Service health |
| `POST` | `/events` | Store an application error event |
| `GET` | `/events` | List error events |
| `POST` | `/monitor` | Register a monitor |
| `POST` | `/monitor/{monitor_id}/check` | Run and persist a monitor check |
| `GET` | `/incidents` | List incidents |
| `PATCH` | `/incidents/{incident_id}/resolve` | Resolve an open incident |

Interactive API documentation is available at `http://localhost:4321/docs` when running through Docker Compose.

## Quick start

Requirements:

- Docker with Docker Compose
- A Slack incoming-webhook URL only if Slack notifications are wanted

Create a local `.env` file:

```env
APP_PORT=4321
POSTGRES_USER=devpulse
POSTGRES_PASSWORD=change-me
POSTGRES_DB=devpulse
MONITOR_INTERVAL_SECONDS=60
SLACK_WEBHOOK_URL=
```

Then start the stack:

```bash
docker compose up -d --build
docker compose ps
```

The API container waits for healthy PostgreSQL and Redis services, applies Alembic migrations, and starts Uvicorn on port 1234 inside the container. The default host port is 4321.

Check the service:

```bash
curl http://localhost:4321/health
```

Stop the stack without deleting PostgreSQL data:

```bash
docker compose down
```

## Example

Register a monitor:

```bash
curl -X POST http://localhost:4321/monitor \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Example health endpoint",
    "url": "https://example.com",
    "method": "GET",
    "expected_status": 200,
    "timeout_seconds": 5
  }'
```

Run a manual check:

```bash
curl -X POST http://localhost:4321/monitor/1/check
```

List and resolve incidents:

```bash
curl http://localhost:4321/incidents
curl -X PATCH http://localhost:4321/incidents/1/resolve
```

Enabled monitors are also checked automatically. Change `MONITOR_INTERVAL_SECONDS` to adjust the interval.

## Failure and incident behavior

Redis uses the key `monitor:{id}:failures`.

- Failure 1 creates the counter and sets its TTL to 300 seconds.
- Failure 2 updates the counter but creates no incident.
- Failure 3 creates one open incident.
- Failure 4 and later update that same open incident.
- Slack is called only when the incident is first created.
- After an incident is resolved, a later qualifying failure window can create a new incident.

If Redis or Slack is temporarily unavailable, the monitor check remains stored in PostgreSQL. Slack delivery is best-effort and does not roll back incident creation.

## Local development and tests

For local Python execution, provide these additional values in `.env`:

```env
ENGINE=postgresql+psycopg://devpulse:change-me@localhost:5432/devpulse
REDIS_URL=redis://localhost:6379/0
```

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Run the test suite:

```bash
python -m pytest -v
```

The core tests use an isolated in-memory database and mock external HTTP, Redis, and Slack boundaries. They cover healthy and failed checks, Redis TTL behavior, incident creation/update, one-time Slack notification, resolution, and enabled-monitor scheduling.

## Database migrations

SQLAlchemy models are the schema source of truth. Apply existing migrations with:

```bash
alembic upgrade head
```

For a model change:

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

Inspect every generated migration before applying it. Files under `db/postgres/` are references only.

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `APP_PORT` | `4321` | Host port mapped to the API container |
| `POSTGRES_USER` | required | PostgreSQL user |
| `POSTGRES_PASSWORD` | required | PostgreSQL password |
| `POSTGRES_DB` | required | PostgreSQL database |
| `ENGINE` | set by Compose | SQLAlchemy database URL |
| `REDIS_URL` | set by Compose | Redis connection URL |
| `MONITOR_INTERVAL_SECONDS` | `60` | Automatic check interval |
| `SLACK_WEBHOOK_URL` | empty | Optional Slack incoming webhook |

Never commit `.env` or webhook URLs.
