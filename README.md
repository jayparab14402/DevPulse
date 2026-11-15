# DevPulse

DevPulse is a backend-focused API reliability and incident-monitoring service built with FastAPI, PostgreSQL, Redis, SQLAlchemy, Alembic, APScheduler, and Docker Compose.

It registers safe/read-only service endpoints, stores health-check history and latency, tracks repeated failures in a five-minute Redis window, creates one incident per ongoing outage, and can notify Slack or create one Jira issue when a new incident opens.

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
3 failures -> create OPEN incident -> Slack alert / Jira issue
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
JIRA_INTEGRATION_ENABLED=false
JIRA_BASE_URL=
JIRA_EMAIL=
JIRA_API_TOKEN=
JIRA_PROJECT_KEY=KAN
JIRA_ISSUE_TYPE=Task
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
- Jira is called only when the incident is first created and the integration is enabled.
- After an incident is resolved, a later qualifying failure window can create a new incident.
- Resolving an incident clears that monitor's Redis counter, so a later incident requires three fresh failures.

If Redis, Slack, or Jira is temporarily unavailable, the monitor check and incident remain stored in PostgreSQL. External notifications do not roll back incident creation.

## Jira integration

Jira creation is disabled by default so local checks and automated tests cannot consume Jira work items. To enable it, create a Jira API token and provide all Jira environment variables in the local `.env` file. Never commit the token.

The integration creates one Jira issue only when a new incident is inserted. Later failures update the same incident and do not call Jira again. DevPulse stores the Jira key, URL, synchronization status, and a sanitized error on the incident.

There is intentionally no automatic Jira retry loop in V1. A timeout or Jira error is recorded as `FAILED`, which avoids accidental duplicate issues or uncontrolled API usage on the free plan.

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
| `JIRA_INTEGRATION_ENABLED` | `false` | Enables Jira issue creation when set to `true` |
| `JIRA_BASE_URL` | empty | Jira site URL, such as `https://example.atlassian.net` |
| `JIRA_EMAIL` | empty | Atlassian account email used by the integration |
| `JIRA_API_TOKEN` | empty | Secret Jira API token; never commit it |
| `JIRA_PROJECT_KEY` | `KAN` | Jira project receiving incidents |
| `JIRA_ISSUE_TYPE` | `Task` | Jira issue type used for incidents |

Never commit `.env` or webhook URLs.
