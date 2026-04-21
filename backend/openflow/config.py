import os

TEAMS_APP_ID = os.environ.get("TEAMS_APP_ID", "")
TEAMS_APP_SECRET = os.environ.get("TEAMS_APP_SECRET", "")
TEAMS_TENANT_ID = os.environ.get("TEAMS_TENANT_ID", "")

METABASE_URL = os.environ.get("METABASE_URL", "http://metabase:3000")
METABASE_USERNAME = os.environ.get("METABASE_USERNAME", "")
METABASE_PASSWORD = os.environ.get("METABASE_PASSWORD", "")
METABASE_DATABASE_ID = int(os.environ.get("METABASE_DATABASE_ID", "1"))
SCHEMA_CACHE_MINUTES = int(os.environ.get("SCHEMA_CACHE_MINUTES", "60"))

LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://ollama:11434/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "llama3.2")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
