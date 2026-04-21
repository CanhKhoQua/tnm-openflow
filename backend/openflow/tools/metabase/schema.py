import asyncio
import datetime
from typing import Any

from openflow.config import METABASE_DATABASE_ID, SCHEMA_CACHE_MINUTES
from openflow.tools.metabase.client import metabase_get

_cache: dict[str, Any] = {}
_cache_time: datetime.datetime | None = None


async def get_schema() -> str:
    global _cache, _cache_time
    now = datetime.datetime.now(datetime.timezone.utc)
    if _cache_time and (now - _cache_time).seconds < SCHEMA_CACHE_MINUTES * 60:
        return _cache['schema']

    fields_data = await metabase_get(f'/api/database/{METABASE_DATABASE_ID}/fields')
    tables: dict[str, list[str]] = {}
    for field in fields_data:
        table = field.get('table', {}).get('name', 'unknown')
        col = field.get('name', '')
        tables.setdefault(table, []).append(col)

    lines = []
    for table, cols in sorted(tables.items()):
        lines.append(f'Table: {table}')
        for col in cols:
            lines.append(f'  - {col}')

    schema = '\n'.join(lines)
    _cache = {'schema': schema}
    _cache_time = now
    return schema
