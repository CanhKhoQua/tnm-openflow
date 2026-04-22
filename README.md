# TNM OpenFlow

**TNM OpenFlow** is a fork of [Open WebUI](https://github.com/open-webui/open-webui) that adds a **Microsoft Teams bot connector** and a **Metabase natural-language query tool** on top of the full Open WebUI platform.

Ask questions in plain English inside a Teams channel — OpenFlow translates them to SQL, runs them against your Metabase database, and replies with the results.

---

## What's Added

| Feature                | Description                                                                                                                                          |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Teams connector**    | Receives messages from a Microsoft Teams bot, routes them through the pipeline, and replies in the same conversation                                 |
| **NL-to-SQL tool**     | Converts a natural-language question into a read-only SQL query using a local LLM (Ollama), executes it via Metabase, and returns structured results |
| **Admin UI**           | Bot integrations panel inside Open WebUI Settings to view connector status                                                                           |
| **Security hardening** | Input sanitization, SQL allowlist (SELECT-only via sqlglot), prompt-injection isolation, startup config validation                                   |

Everything from the upstream Open WebUI — RAG, image generation, voice, model management — is preserved and unchanged.

---

## Architecture

```
Microsoft Teams
      │  webhook POST /openflow/teams/messages
      ▼
FastAPI (Open WebUI + OpenFlow routes)
      │
      ├── TeamsConnector  ──▶  BotFrameworkAdapter (auth + reply)
      │         │
      │    TeamsPipeline
      │         │
      │    run_query(question)
      │         │
      │    ┌────┴─────────────────────────┐
      │    │  _sanitize_question          │
      │    │  get_schema()  ──▶ Metabase  │
      │    │  _nl_to_sql()  ──▶ Ollama   │
      │    │  is_safe_sql() (sqlglot)     │
      │    │  metabase_post(/api/dataset) │
      │    └──────────────────────────────┘
      │
Ollama (LLM)       Metabase (database proxy)
```

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- A Microsoft Azure Bot registration (for Teams)
- A running Metabase instance with a configured database (handled by Docker Compose)

### 1. Clone

```bash
git clone https://github.com/CanhKhoQua/tnm-openflow.git
cd tnm-openflow
```

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` and fill in the required values:

```env
# Microsoft Teams
TEAMS_APP_ID=your-azure-app-id
TEAMS_APP_SECRET=your-azure-app-secret
TEAMS_TENANT_ID=your-tenant-id

# Metabase
METABASE_USERNAME=admin@example.com
METABASE_PASSWORD=your-metabase-password
METABASE_DATABASE_ID=1        # ID of the database to query in Metabase

# LLM
LLM_MODEL=llama3.2            # any Ollama model

# Ports (host-side)
OPEN_WEBUI_PORT=8080
METABASE_PORT=3001
```

### 3. Start

```bash
docker compose up -d
```

This starts three services:

| Service      | URL                   | Purpose                   |
| ------------ | --------------------- | ------------------------- |
| `open-webui` | http://localhost:8080 | Open WebUI + OpenFlow API |
| `ollama`     | internal              | LLM inference             |
| `metabase`   | http://localhost:3001 | Database query proxy      |

### 4. Register the Teams Webhook

In your Azure Bot registration, set the messaging endpoint to:

```
https://your-public-host/openflow/teams/messages
```

For local development, use [ngrok](https://ngrok.com/) or similar to expose port 8080.

### 5. Verify

```
GET http://localhost:8080/openflow/status
```

Should return `{"status": "ok", "connectors": ["teams"]}`.

---

## Environment Variables

### Required (OpenFlow)

| Variable            | Description                       |
| ------------------- | --------------------------------- |
| `TEAMS_APP_ID`      | Azure Bot application (client) ID |
| `TEAMS_APP_SECRET`  | Azure Bot client secret           |
| `METABASE_USERNAME` | Metabase admin username           |
| `METABASE_PASSWORD` | Metabase admin password           |

### Optional (OpenFlow)

| Variable               | Default                  | Description                           |
| ---------------------- | ------------------------ | ------------------------------------- |
| `TEAMS_TENANT_ID`      | _(empty)_                | Restrict bot to a single tenant       |
| `METABASE_URL`         | `http://metabase:3000`   | Internal Metabase URL                 |
| `METABASE_DATABASE_ID` | `1`                      | Metabase database ID to query         |
| `LLM_BASE_URL`         | `http://ollama:11434/v1` | OpenAI-compatible LLM endpoint        |
| `LLM_MODEL`            | `llama3.2`               | Model name for NL-to-SQL              |
| `LLM_API_KEY`          | _(empty)_                | API key if using a hosted LLM         |
| `SCHEMA_CACHE_MINUTES` | `60`                     | How long to cache the Metabase schema |
| `OPEN_WEBUI_PORT`      | `8080`                   | Host port for the web UI              |
| `METABASE_PORT`        | `3001`                   | Host port for Metabase                |

All standard Open WebUI environment variables are also supported unchanged.

---

## Security

OpenFlow applies several layers of defence before running any query:

1. **Input sanitization** — question is stripped, truncated to 500 chars, and matched against an allowlist of safe characters
2. **Prompt injection isolation** — the schema and user question are passed in separate `system` / `user` messages; the system prompt explicitly instructs the LLM to ignore embedded instructions
3. **SQL allowlist** — generated SQL is parsed with `sqlglot`; only a single `SELECT` statement with no DDL/DML sub-expressions is accepted
4. **Auth passthrough** — the raw `Authorization` header from Teams is forwarded directly to the Bot Framework SDK for cryptographic verification; it is never parsed or trusted by application code
5. **Startup validation** — the app exits immediately at boot if any required env var is missing

---

## Development

### Install dependencies

```bash
# Python 3.11 or 3.12
pip install -e ".[all]"
```

### Run tests

```bash
cd backend
pytest test/ -q
```

All 52 tests should pass. Tests use `respx` to mock HTTP calls and `monkeypatch` to isolate the LLM and Metabase schema — no live services required.

### Project layout

```
backend/
├── open_webui/          # upstream Open WebUI (do not rename)
│   └── main.py          # OpenFlow routes wired in at the bottom
└── openflow/            # TNM OpenFlow package
    ├── config.py         # env var loading + startup validation
    ├── connectors/
    │   ├── base.py       # BasePlatformConnector ABC
    │   ├── registry.py   # connector registry
    │   └── teams/
    │       ├── connector.py   # BotFrameworkAdapter wrapper
    │       ├── pipeline.py    # message routing
    │       ├── formatter.py   # Adaptive Card builder
    │       └── router.py      # FastAPI route
    ├── routers/
    │   └── status.py     # GET /openflow/status
    └── tools/
        └── metabase/
            ├── client.py    # Metabase HTTP client (session + retry)
            ├── executor.py  # run_query() orchestrator
            ├── safety.py    # SQL allowlist (sqlglot)
            └── schema.py    # schema fetcher + cache

test/
└── openflow/
    ├── connectors/
    │   ├── test_registry.py
    │   └── test_formatter.py
    └── tools/metabase/
        ├── test_executor.py
        └── test_safety.py

src/                     # SvelteKit frontend (Open WebUI)
└── lib/components/admin/
    └── BotIntegrations.svelte   # admin panel
```

---

## Upstream

TNM OpenFlow tracks [open-webui/open-webui](https://github.com/open-webui/open-webui). The `open_webui/` package is never renamed or restructured so upstream merges stay clean. All OpenFlow code lives exclusively in `openflow/`.

---

## License

The Open WebUI components are licensed under the [Open WebUI License](./LICENSE). TNM OpenFlow additions are proprietary to Twin Roots LLC.
