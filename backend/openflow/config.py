import os

try:
    from open_webui.config import PersistentConfig
except ImportError:
    # Lightweight shim for test environments that don't have the full
    # Open WebUI stack installed. Behaves identically from the caller's
    # perspective: access the value via .value or str().
    class PersistentConfig:  # type: ignore[no-redef]
        def __init__(self, env_name: str, config_path: str, env_value):
            self.env_name = env_name
            self.config_path = config_path
            self.value = env_value

        def __str__(self) -> str:
            return str(self.value)


TEAMS_APP_ID = PersistentConfig(
    'TEAMS_APP_ID', 'openflow.teams_app_id', os.environ.get('TEAMS_APP_ID', '')
)
TEAMS_APP_SECRET = PersistentConfig(
    'TEAMS_APP_SECRET', 'openflow.teams_app_secret', os.environ.get('TEAMS_APP_SECRET', '')
)
TEAMS_TENANT_ID = PersistentConfig(
    'TEAMS_TENANT_ID', 'openflow.teams_tenant_id', os.environ.get('TEAMS_TENANT_ID', '')
)

METABASE_URL = PersistentConfig(
    'METABASE_URL', 'openflow.metabase_url', os.environ.get('METABASE_URL', 'http://metabase:3000')
)
METABASE_USERNAME = PersistentConfig(
    'METABASE_USERNAME', 'openflow.metabase_username', os.environ.get('METABASE_USERNAME', '')
)
METABASE_PASSWORD = PersistentConfig(
    'METABASE_PASSWORD', 'openflow.metabase_password', os.environ.get('METABASE_PASSWORD', '')
)
METABASE_DATABASE_ID = PersistentConfig(
    'METABASE_DATABASE_ID',
    'openflow.metabase_database_id',
    int(os.environ.get('METABASE_DATABASE_ID', '1')),
)
SCHEMA_CACHE_MINUTES = PersistentConfig(
    'SCHEMA_CACHE_MINUTES',
    'openflow.schema_cache_minutes',
    int(os.environ.get('SCHEMA_CACHE_MINUTES', '60')),
)

LLM_BASE_URL = PersistentConfig(
    'LLM_BASE_URL', 'openflow.llm_base_url', os.environ.get('LLM_BASE_URL', 'http://ollama:11434/v1')
)
LLM_MODEL = PersistentConfig(
    'LLM_MODEL', 'openflow.llm_model', os.environ.get('LLM_MODEL', 'llama3.2')
)
LLM_API_KEY = PersistentConfig(
    'LLM_API_KEY', 'openflow.llm_api_key', os.environ.get('LLM_API_KEY', '')
)


def validate_required_config() -> None:
    required = {
        'TEAMS_APP_ID': TEAMS_APP_ID.value,
        'TEAMS_APP_SECRET': TEAMS_APP_SECRET.value,
        'METABASE_USERNAME': METABASE_USERNAME.value,
        'METABASE_PASSWORD': METABASE_PASSWORD.value,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        import sys
        print(f'FATAL: Missing required env vars: {", ".join(missing)}', file=sys.stderr)
        sys.exit(1)
