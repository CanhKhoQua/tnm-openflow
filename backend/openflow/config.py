import os
import sys


def _require(name: str) -> str:
    val = os.environ.get(name, '')
    if not val:
        print(f'FATAL: Required environment variable {name} is not set', file=sys.stderr)
        sys.exit(1)
    return val


TEAMS_APP_ID = os.environ.get('TEAMS_APP_ID', '')
TEAMS_APP_SECRET = os.environ.get('TEAMS_APP_SECRET', '')
TEAMS_TENANT_ID = os.environ.get('TEAMS_TENANT_ID', '')

METABASE_URL = os.environ.get('METABASE_URL', 'http://metabase:3000')
METABASE_USERNAME = os.environ.get('METABASE_USERNAME', '')
METABASE_PASSWORD = os.environ.get('METABASE_PASSWORD', '')
METABASE_DATABASE_ID = int(os.environ.get('METABASE_DATABASE_ID', '1'))
SCHEMA_CACHE_MINUTES = int(os.environ.get('SCHEMA_CACHE_MINUTES', '60'))

LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'http://ollama:11434/v1')
LLM_MODEL = os.environ.get('LLM_MODEL', 'llama3.2')
LLM_API_KEY = os.environ.get('LLM_API_KEY', '')


def validate_required_config() -> None:
    required = {
        'TEAMS_APP_ID': TEAMS_APP_ID,
        'TEAMS_APP_SECRET': TEAMS_APP_SECRET,
        'METABASE_USERNAME': METABASE_USERNAME,
        'METABASE_PASSWORD': METABASE_PASSWORD,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f'FATAL: Missing required env vars: {", ".join(missing)}', file=sys.stderr)
        sys.exit(1)
